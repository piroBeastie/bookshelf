# BookShelf — DevOps Final Capstone

**Name:** Nanakjot Singh Chahal
**Enrollment No:** 24bcs10132

BookShelf is a small reading-list application. You add books you want to read, move them between three
shelves (`WANT` → `READING` → `FINISHED`), give them a rating out of 5, and the app keeps a running count
of how many pages you have actually finished and what your average rating is.

The application is deliberately small. The point of the capstone is everything **around** it: tests, a
container build, a pipeline, a security gate, infrastructure as code, a Helm release and a dashboard.

```
            browser
               |
        nginx (frontend)          ← react bundle, serves / and proxies /api
               |
        fastapi (backend)         ← rest api + /health, /ready, /metrics
               |
          postgresql              ← one table, created by an alembic migration
```

---

## Stack

| layer | what i used |
|---|---|
| frontend | React 18 + Vite, served by nginx |
| backend | FastAPI (Python 3.12), SQLAlchemy 2, Pydantic |
| database | PostgreSQL 16, schema managed by Alembic |
| tests | pytest (11 tests, sqlite test database) |
| containers | two Dockerfiles, both running as non-root; docker compose for local |
| ci/cd | GitHub Actions → pytest, flake8, helm lint, docker build, Trivy, GHCR |
| security | Trivy image scan, build fails on fixable HIGH/CRITICAL CVEs |
| infrastructure | Terraform — VPC, two public subnets, EKS cluster + managed node group |
| kubernetes | Helm chart with Deployments, Services, Ingress, HPA and probes |
| observability | Prometheus scrapes `/metrics`, Grafana dashboard |

---

## API

| method | path | what it does |
|---|---|---|
| GET | `/health` | liveness - always `{"status":"UP"}` |
| GET | `/ready` | readiness - runs a real query against postgres |
| GET | `/metrics` | prometheus metrics |
| GET | `/api/books` | list books, optional `?shelf=WANT\|READING\|FINISHED` |
| GET | `/api/books/stats` | totals, pages read, average rating |
| GET | `/api/books/{id}` | one book, 404 if it does not exist |
| POST | `/api/books` | create a book (201) |
| PUT | `/api/books/{id}` | update any field |
| DELETE | `/api/books/{id}` | delete a book (204) |

---

## Running it locally

```bash
docker compose up --build
```

- app: <http://localhost:3000>
- api docs: <http://localhost:8000/docs>

The backend container runs `alembic upgrade head` before uvicorn, so the `books` table is created on
first start. Postgres has a healthcheck and the backend waits for it.

## Running the tests

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

The tests point `DATABASE_URL` at a throwaway sqlite file before the app is imported, so they can never
touch the real database.

## Deploying to Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml

helm upgrade --install bookshelf ./helm/bookshelf -n bookshelf \
  --set backend.image=ghcr.io/pirobeastie/bookshelf-backend --set backend.tag=<sha> \
  --set frontend.image=ghcr.io/pirobeastie/bookshelf-frontend --set frontend.tag=<sha>

kubectl get pods -n bookshelf
```

The chart creates postgres (with a PVC), the backend and frontend Deployments with 2 replicas each,
three ClusterIP Services, an HPA on the backend and an Ingress that routes `/api` to the backend and
everything else to the frontend.

## Monitoring

```bash
helm upgrade --install prometheus prometheus-community/prometheus -n monitoring -f monitoring/prometheus-values.yaml
helm upgrade --install grafana   grafana/grafana               -n monitoring -f monitoring/grafana-values.yaml
```

Prometheus discovers the backend pods through the `bookshelf-backend` Service endpoints and scrapes
`/metrics`. The Grafana data source is provisioned from the values file.

## Infrastructure

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply     # creates real AWS resources
terraform destroy   # always, when you are finished
```

No credentials live in this repository. Terraform reads them from the environment or an IAM role.

---

## Layout

```
session21-capstone/
├── backend/            fastapi app, alembic migrations, pytest suite, Dockerfile
├── frontend/           react app, nginx config, multi-stage Dockerfile
├── docker-compose.yml  the whole stack locally
├── k8s/                namespace
├── helm/bookshelf/     the kubernetes package
├── terraform/          vpc + eks
├── monitoring/         prometheus and grafana helm values
├── scripts/            load generator
└── hw.md               the writeup, with screenshots of every module
```

The pipeline lives in [`.github/workflows/capstone-ci-cd.yml`](../.github/workflows/capstone-ci-cd.yml)
at the root of the repository, because that is where GitHub looks for workflows.
