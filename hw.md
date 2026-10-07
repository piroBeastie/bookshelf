# Session 21 - Final Capstone: BookShelf

**Name:** Nanakjot Singh Chahal
**Enrollment No:** 24bcs10132

**Repo:** <https://github.com/piroBeastie/devops-heros> — project folder [`session21-capstone/`](.)

My application is **BookShelf**, a reading list. You add books, move them between `WANT` → `READING` →
`FINISHED`, rate them out of 5, and it keeps a running total of pages finished and the average rating.
The domain is mine; the DevOps layer follows the architecture taught in the course.

> everything below was actually run on my machine - wsl2 ubuntu with docker, a minikube cluster, and
> github actions for the pipeline. the one thing i could not do for real is `terraform apply`, because i
> do not have an AWS account with billing - that is explained honestly in M7.

---

## M1 - Application: Frontend + Backend + Database

FastAPI + PostgreSQL + React. Nine endpoints, one table, one Alembic migration.

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/books -H 'Content-Type: application/json' -d '{...}'
curl -s http://localhost:8000/api/books?shelf=READING | python3 -m json.tool
curl -s -X PUT http://localhost:8000/api/books/6 -H 'Content-Type: application/json' -d '{"shelf":"FINISHED","rating":5}'
curl -s http://localhost:8000/api/books/stats
curl -s -X DELETE http://localhost:8000/api/books/6
```

![API endpoints](screenshots/Screenshot%202026-10-07%20183254.png)

all four verbs in one go: `GET /health` → `{"status":"UP"}`, `POST` → **201** with the new id, `GET` with
a `?shelf=` filter, `PUT` flipping the book to `FINISHED` with a rating, `GET /api/books/stats`, and
`DELETE` → **204**.

the stats endpoint is the only bit of real logic:

```json
{"total":6,"want":1,"reading":2,"finished":3,"pagesRead":1400,"averageRating":4.67}
```

`pagesRead` only counts books on the `FINISHED` shelf (a SQL `sum` with a `where`), and `averageRating`
ignores unrated books instead of treating them as zero - otherwise every new book would drag the average
down.

### the UI

![BookShelf in the browser](screenshots/Screenshot%202026-10-07%20182612.png)

the stat cards, an add form, shelf filters, and per-book dropdowns that `PUT` the change straight away.
the frontend never talks to the backend directly - nginx proxies `/api` to it, which is why the same
build works in compose and in kubernetes.

| file | what it is |
|---|---|
| `backend/app/models.py` | the `Book` SQLAlchemy model |
| `backend/app/schemas.py` | pydantic request/response models, `shelf` is a `Literal` of three values |
| `backend/app/main.py` | the endpoints |
| `backend/alembic/versions/0001_create_books.py` | the migration that creates the table |
| `frontend/src/main.jsx` | the whole React app |

---

## M2 - Testing: Pytest + Code Quality

```bash
pytest -v
```

![pytest](screenshots/Screenshot%202026-10-07%20183212.png)

**11 tests, all passing**, covering 7 endpoints:

```
test_health_endpoint                      test_list_books_returns_created_book
test_root_reports_service_name            test_list_books_can_filter_by_shelf
test_metrics_endpoint_is_prometheus_format  test_get_single_book_and_404
test_create_book                          test_update_book
test_create_book_rejects_bad_rating       test_delete_book
                                          test_stats_counts_pages_and_rating
```

the important part is `tests/conftest.py`:

```python
import os
# point the app at a throwaway sqlite file BEFORE the app is imported, so the
# tests can never touch the real postgres database
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
```

that line has to run before `from app.main import app`, because the engine is created at import time.
an `autouse` fixture drops and recreates the tables around every test, so no test can see another test's
rows - `test_stats_counts_pages_and_rating` asserts `total == 3`, which only holds on a clean database.

`pytest.ini` sets `pythonpath = .` so `app` imports without installing the package. CI also runs
`flake8 app tests --max-line-length=110`, which passes clean.

---

## M3 - Git and GitHub

```bash
git log --oneline
cat .gitignore
```

![git history](screenshots/Screenshot%202026-10-07%20202118.png)

**13 capstone commits**, one per piece of work, with messages that say what changed - not "update" or
"fix". `.gitignore` covers `__pycache__/`, `*.pyc`, `.venv/`, `.pytest_cache/`, `backend/test.db`,
`node_modules/`, `dist/`, `.env`, `*.tfvars` (with `!*.tfvars.example`) and the terraform state files.

no credentials are committed anywhere. the only two files that look like secrets are
`backend/.env.example` and `terraform/terraform.tfvars.example`, and both contain placeholders only.

---

## M4 - Docker: Dockerfile + Compose

```bash
docker compose up --build
docker compose ps
```

![compose up build](screenshots/Screenshot%202026-10-07%20183141.png)

one command, three services: `bookshelf-postgres` (healthy), `bookshelf-backend` on 8000, and
`bookshelf-frontend` on 3000.

```bash
docker compose logs backend | grep -iE 'alembic|running upgrade|Uvicorn running'
docker compose exec backend id
docker compose exec frontend id
docker images
```

![migration and non-root](screenshots/Screenshot%202026-10-07%20183301.png)

three things this proves:

```
[alembic.runtime.migration] Running upgrade  -> 0001_create_books, create books table
uid=10001(appuser) gid=10001(appuser)        ← backend is not root
uid=101(nginx) gid=101(nginx)                ← frontend is not root
session21-capstone-backend    289MB
session21-capstone-frontend   73.9MB         ← multi-stage: node is gone from the final image
```

the backend `CMD` is `alembic upgrade head && uvicorn ...`, so the schema is created before the API
accepts traffic, and compose holds the backend back with `depends_on: condition: service_healthy` until
postgres answers `pg_isready`.

the frontend is a two stage build - `node:22-alpine` compiles the React bundle, then only `dist/` is
copied into `nginxinc/nginx-unprivileged`. that base image runs as uid 101 and listens on **8080**,
because a non-root process cannot bind to port 80. that is why the compose mapping is `3000:8080` and
the Service `targetPort` is 8080.

---

## M7 - Terraform: AWS Infrastructure as Code

> **honest note:** i do not have an AWS account with billing enabled, so i did **not** run
> `terraform apply` or `terraform destroy`, and i have no AWS console screenshot. an EKS cluster plus two
> `t3.medium` nodes is not something i can create on an account i do not have. what i did instead is run
> `init`, `fmt`, `validate` and a full `plan` with a provider that skips the credential calls, so the
> plan output below is real and shows exactly what would be created. the same approach as sessions 18
> and 19.

```bash
terraform init
terraform fmt -check -recursive
terraform validate
```

![terraform init and validate](screenshots/Screenshot%202026-10-07%20195409.png)

```bash
terraform plan -out=tfplan
```

![terraform plan](screenshots/Screenshot%202026-10-07%20195416.png)

```
# aws_eks_cluster.main                        will be created
# aws_eks_node_group.main                     will be created
# aws_iam_role.cluster                        will be created
# aws_iam_role.node                           will be created
# aws_iam_role_policy_attachment.{cluster_policy,node_cni,node_registry,node_worker}
# aws_internet_gateway.main                   will be created
# aws_route_table.public                      will be created
# aws_route_table_association.public[0..1]    will be created
# aws_subnet.public[0..1]                     will be created
# aws_vpc.main                                will be created
Plan: 15 to add, 0 to change, 0 to destroy.
```

**two public subnets in two different AZs** (`ap-south-1a` and `ap-south-1b`) - EKS refuses to create a
cluster in a single AZ, and it is also what keeps the cluster alive if one AZ fails.

![eks plan detail](screenshots/Screenshot%202026-10-07%20195424.png)

I wrote the resources by hand instead of using the community `vpc` and `eks` modules. The modules are
shorter, but they hide the IAM roles, and writing them out is the part that actually teaches you what
EKS needs: one role for the control plane (`AmazonEKSClusterPolicy`) and one for the nodes
(`AmazonEKSWorkerNodePolicy` + `AmazonEKS_CNI_Policy` + `AmazonEC2ContainerRegistryReadOnly`). It also
means the config has **no data sources**, which is exactly why the plan can run without credentials.

`terraform.tfvars.example` is committed; `terraform.tfvars`, `.terraform/` and all state files are
gitignored. Credentials would come from the environment or an IAM role, never from a file in the repo.

### what i would run with a real account

```bash
export AWS_ACCESS_KEY_ID=...        # or: aws sso login
terraform apply tfplan
aws eks update-kubeconfig --region ap-south-1 --name bookshelf-eks
helm upgrade --install bookshelf ./helm/bookshelf -n bookshelf --create-namespace ...
terraform destroy                   # the important one - EKS is ~$0.10/hour for the control plane alone
```

---

## M8 - Kubernetes + Helm

```bash
helm lint helm/bookshelf
kubectl apply -f k8s/namespace.yaml
helm upgrade --install bookshelf ./helm/bookshelf -n bookshelf --set backend.image=... --set backend.tag=dev ...
helm list -n bookshelf
```

![helm install](screenshots/Screenshot%202026-10-07%20195219.png)

```bash
kubectl get pods,svc -n bookshelf
kubectl get ingress,hpa -n bookshelf
```

![kubectl get all](screenshots/Screenshot%202026-10-07%20195224.png)

```
pod/bookshelf-backend-...   1/1  Running  0        ← 2 replicas
pod/bookshelf-backend-...   1/1  Running  0
pod/bookshelf-frontend-...  1/1  Running  0        ← 2 replicas
pod/bookshelf-frontend-...  1/1  Running  0
pod/bookshelf-postgres-...  1/1  Running  0

service/bookshelf-backend    ClusterIP  8000/TCP
service/bookshelf-frontend   ClusterIP  80/TCP
service/bookshelf-postgres   ClusterIP  5432/TCP

ingress/bookshelf   nginx   bookshelf.local,localhost   192.168.49.2   80
hpa/bookshelf-backend   Deployment/bookshelf-backend   cpu: 4%/70%   2   5   2
```

everything `Running` with **0 restarts**, which was not true on my first install - see the two problems
at the bottom of this page.

### the ingress routing

```bash
curl -H 'Host: bookshelf.local' http://192.168.49.2/
curl -H 'Host: bookshelf.local' http://192.168.49.2/api/books/stats
```

![curl through the ingress](screenshots/Screenshot%202026-10-07%20195229.png)

one hostname, two paths: `/` returns the React `index.html` from the frontend Service, `/api/...`
returns JSON from the backend Service. the ingress is the only thing exposed; the three Services are all
`ClusterIP`.

![app through the ingress](screenshots/Screenshot%202026-10-07%20192210.png)

the same app, this time in the browser through the ingress controller. the chart lists two hosts -
`bookshelf.local` for a real DNS entry, and `localhost` so i can reach it through a port-forward from
windows without editing a hosts file.

### what the chart contains

| template | what it makes |
|---|---|
| `postgres.yaml` | Secret, PVC, Service and Deployment (strategy `Recreate`, because two postgres pods cannot share one volume) |
| `backend-deployment.yaml` | 2 replicas, an initContainer that waits for postgres, `/ready` + `/health` probes, resources |
| `frontend-deployment.yaml` | 2 replicas, probes on `/` |
| `*-service.yaml` | three ClusterIP Services |
| `ingress.yaml` | `/api` → backend, `/` → frontend, over a list of hosts |
| `hpa.yaml` | scales the backend 2 → 5 at 70% CPU |

the database password is only in the Secret. the backend reads it with `secretKeyRef` and builds
`DATABASE_URL` from it using `$(POSTGRES_PASSWORD)` - which only works because kubernetes expands
`$(VAR)` for variables declared **above** it in the env list. i got that wrong the first time and the
pod came up with the literal string `$(POSTGRES_PASSWORD)` in its connection url.

---

## M9 - Observability: Prometheus + Grafana

### the /metrics endpoint

```bash
curl -s http://localhost:8000/metrics | grep '^http_requests_total'
```

![metrics endpoint](screenshots/Screenshot%202026-10-07%20183307.png)

```
http_requests_total{handler="/api/books",method="POST",status="2xx"} 6.0
http_requests_total{handler="/api/books/stats",method="GET",status="2xx"} 2.0
http_requests_total{handler="/api/books/{book_id}",method="PUT",status="2xx"} 1.0
http_requests_total{handler="/api/books/{book_id}",method="DELETE",status="2xx"} 1.0
```

one line of code produces all of this - `Instrumentator().instrument(app).expose(app, endpoint="/metrics")`.
note that the handler label is the **route template** (`/api/books/{book_id}`), not the actual path.
that matters: if it used the real path, every book id would create a new time series and prometheus
would fall over. that is the classic "high cardinality" mistake.

### prometheus and grafana in the cluster

```bash
helm upgrade --install prometheus prometheus-community/prometheus -n monitoring -f monitoring/prometheus-values.yaml
helm upgrade --install grafana   grafana/grafana               -n monitoring -f monitoring/grafana-values.yaml
kubectl get pods,svc -n monitoring
```

![monitoring namespace](screenshots/Screenshot%202026-10-07%20200521.png)

the `up` query returns **1 for both backend pods**, each labelled with its pod name.

![prometheus targets](screenshots/Screenshot%202026-10-07%20195847.png)

the Targets page shows `bookshelf-backend 2/2 up`. the scrape config in
`monitoring/prometheus-values.yaml` uses `kubernetes_sd_configs` with `role: endpoints` and keeps only
the `bookshelf-backend` service's `http` port:

```yaml
relabel_configs:
  - source_labels: [__meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
    action: keep
    regex: bookshelf-backend;http
```

that scrapes **each pod separately**. a static target pointing at the Service would get load balanced to
a random pod on every scrape, and the counters would jump around.

### the dashboard

![grafana dashboard](screenshots/Screenshot%202026-10-07%20200134.png)

```promql
sum by (handler) (rate(http_requests_total{job="bookshelf-backend"}[5m]))
```

one line per endpoint. the climb is `scripts/load-test.sh` sending 360 requests through the ingress.
the grafana data source is provisioned from `monitoring/grafana-values.yaml`, so it is code, not
something i clicked together and would have to redo after a restart.

---

## Two problems i had to fix

### the ingress controller was dropping four requests out of five

the first time i curled the app through the ingress i got `000` - a timeout - and the next request would
work, and the one after that would time out again. the controller pod said `1/1 Running`, so nothing
looked wrong until i read its logs:

```
[alert] 26#26: worker process 1277 exited with fatal code 2 and cannot be respawned
```

nginx was starting workers and they were dying immediately. the ingress addon lets nginx pick its worker
count from the node's CPU count, and on this machine that was more workers than it had file descriptors
for. capping it fixed it:

```bash
kubectl -n ingress-nginx patch cm ingress-nginx-controller --type merge \
  -p '{"data":{"worker-processes":"2","max-worker-open-files":"8192"}}'
kubectl -n ingress-nginx rollout restart deployment ingress-nginx-controller
```

six requests after the restart, six `200`s. the lesson i took from it: `Running` is not the same as
`working`, and the pod's own logs are the first place to look.

### the backend crashlooped on first install

`kubectl get pods` showed the backend with 3 and 4 restarts. the cause was timing - the container runs
`alembic upgrade head` before uvicorn, and postgres was not accepting connections yet, so alembic failed,
the container exited, kubernetes restarted it, and it worked a minute later once postgres was up.

compose already handled this with a healthcheck, so i gave the chart the kubernetes equivalent, an
initContainer:

```yaml
initContainers:
  - name: wait-for-postgres
    image: postgres:16-alpine
    command: ["sh", "-c", "until pg_isready -h bookshelf-postgres -p 5432 -U bookshelf; do sleep 2; done"]
```

after that the pods come up `1/1 Running` with 0 restarts. the app would have recovered on its own
either way - but "it fixes itself after a minute of CrashLoopBackOff" is not something you want to
explain during a deploy.
