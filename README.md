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

## CI/CD pipeline

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on every push to `main` and on pull
requests, and can also be started by hand from the Actions tab.

```
test   (flake8 → pytest → npm ci → npm run build → upload the bundle)  ─┐
                                                                        ├─► build-scan-push
chart  (helm lint → helm template)  ────────────────────────────────────┘
```

`build-scan-push` declares `needs: [test, chart]`, so an image is never built from code whose tests or
chart failed. Inside it:

| step | what it does |
|---|---|
| Work out the image names | lowercases the repository owner, because a Docker repository name cannot contain capitals |
| Log in to GHCR | with the automatic `GITHUB_TOKEN` and `packages: write` |
| Build backend / frontend | one `docker build` each |
| Trivy report ×2 | prints every HIGH and CRITICAL finding, `exit-code: 0` |
| Security gate ×2 | the same scan with `ignore-unfixed: true` and `exit-code: 1` — this one fails the build |
| Push images | `ghcr.io/<owner>/bookshelf-backend:<commit-sha>` and the same for the frontend |

Images are tagged with the **full commit SHA, never `latest`**, so a running pod's tag points straight
at the commit that produced it.

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

## GitOps with Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f argocd/application.yaml
```

[`argocd/application.yaml`](argocd/application.yaml) is the only file applied by hand. Argo CD then
renders `helm/bookshelf` straight from this repository into the `bookshelf-gitops` namespace and keeps
it there: `prune: true` deletes what is removed from git, `selfHeal: true` undoes anything changed
directly against the cluster.

It deploys beside the Helm release rather than replacing it — Argo CD templates the chart itself, so its
copy does not appear in `helm list`, and the release in the `bookshelf` namespace stays as the
Helm-managed deployment.

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

## Known issues and limitations

- **No `terraform apply`.** I do not have an AWS account with billing enabled, so the VPC and EKS
  cluster were never created and there is no AWS Console screenshot. `init`, `fmt`, `validate` and a
  full `plan` (15 resources) do run — against the real AWS provider with the credential calls skipped,
  which is only possible because the config uses no data sources. `apply` and `destroy` are untested.
- **Kubernetes runs on minikube, not EKS.** Everything in the chart is portable, but the Ingress is
  served by the minikube ingress-nginx addon rather than an AWS load balancer, and the Postgres PVC
  uses the default `standard` StorageClass rather than EBS.
- **Postgres runs in the cluster.** A single replica with a `Recreate` strategy and one PVC. That is
  fine for a demo and wrong for production, where this would be RDS.
- **The database password is a chart default.** `values.yaml` ships `bookshelf/bookshelf` and the chart
  puts it in a Secret. Real deployments should pass `--set postgres.password=...` from a secret manager
  rather than committing a default.
- **The pipeline does not deploy.** It builds, scans and publishes; the Helm upgrade is run by hand (or
  by Argo CD from git). Wiring CI straight into a cluster would need a kubeconfig in repository secrets.
- **The Trivy gate ignores unfixed CVEs.** Findings with no patch available are printed by the report
  step but do not fail the build — otherwise the gate blocks on things nobody can act on and ends up
  being switched off.
- **Ingress hostnames are local.** `bookshelf.local` needs a hosts entry; `localhost` is listed as a
  second host so the app can be reached through a port-forward without one.

## Layout

```
bookshelf/
├── backend/            fastapi app, alembic migrations, pytest suite, Dockerfile
├── frontend/           react app, nginx config, multi-stage Dockerfile
├── docker-compose.yml  the whole stack locally
├── k8s/                namespace
├── helm/bookshelf/     the kubernetes package
├── terraform/          vpc + eks
├── monitoring/         prometheus and grafana helm values
├── argocd/             the Argo CD Application that watches this repo
├── scripts/            load generator
├── demo/               slide deck and the presentation video
├── screenshots/        evidence for every module
└── hw.md               the writeup, module by module
```

The pipeline lives in [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml).
