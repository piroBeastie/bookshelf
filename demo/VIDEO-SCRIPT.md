# Presentation video — recording script

Target length **10–12 minutes**. Record at 1080p with the microphone on. Export as MP4 and commit it to
this folder as `demo/presentation.mp4`.

The order below is the order the submission guidelines ask for. Don't improvise the order — a grader is
ticking items off.

---

## Before you hit record

Run this once and leave it running. It takes a few minutes the first time.

```bash
# 1. cluster
minikube start --memory=5120 --cpus=4
minikube addons enable ingress
minikube addons enable metrics-server

# 2. the app, from the images the pipeline published
kubectl apply -f k8s/namespace.yaml
helm upgrade --install bookshelf ./helm/bookshelf -n bookshelf \
  --set backend.image=ghcr.io/pirobeastie/bookshelf-backend  --set backend.tag=<sha> \
  --set frontend.image=ghcr.io/pirobeastie/bookshelf-frontend --set frontend.tag=<sha>

# 3. monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
kubectl create namespace monitoring
helm upgrade --install prometheus prometheus-community/prometheus -n monitoring -f monitoring/prometheus-values.yaml
helm upgrade --install grafana   grafana/grafana               -n monitoring -f monitoring/grafana-values.yaml

# 4. argo cd
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd patch configmap argocd-cmd-params-cm --type merge -p '{"data":{"server.insecure":"true"}}'
kubectl -n argocd rollout restart deployment argocd-server
kubectl apply -f argocd/application.yaml

# 5. some traffic, so the Grafana panel is not flat
bash scripts/load-test.sh http://192.168.49.2 200
```

Open these in **four terminal tabs** and leave them open:

| tab | command |
|---|---|
| Argo CD UI | `kubectl port-forward svc/argocd-server -n argocd 8080:80` |
| app via Ingress | `kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8088:80` |
| Prometheus | `kubectl port-forward svc/prometheus-server -n monitoring 9091:80` |
| Grafana | `kubectl port-forward svc/grafana -n monitoring 3001:80` |

Argo CD admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Browser tabs to pre-open (so you are never typing a URL on camera):

1. `http://localhost:8088` — the app through the Ingress
2. `https://github.com/piroBeastie/bookshelf` — the repo
3. `https://github.com/piroBeastie/bookshelf/actions` — the pipeline
4. `https://github.com/piroBeastie/bookshelf/pkgs/container/bookshelf-backend` — GHCR
5. `http://localhost:8080` — Argo CD, already logged in
6. `http://localhost:9091/targets` — Prometheus targets
7. `http://localhost:3001` — Grafana, already logged in, dashboard open

Last check before recording: `kubectl get pods -A` — everything `Running`, nothing `CrashLoopBackOff`.

---

## 1 · Slides — 2 min 30 s

Open `demo/slides.pptx`, present mode.

| slide | say |
|---|---|
| 1 Title | "BookShelf — a reading tracker, and the DevOps pipeline that ships it. I'm Nanakjot Singh Chahal, 24bcs10132." |
| 2 What I built | "Books move between three shelves, you rate them, and the API totals the pages you actually finished. The app is deliberately small — the DevOps layer around it is the project." |
| 3 Tech stack | Don't read the grid. "FastAPI and Postgres behind a React frontend, containerised, shipped by GitHub Actions, running on Kubernetes, watched by Prometheus." |
| 4 Architecture | "The browser only ever talks to nginx, which proxies `/api` to the backend. That's why the same frontend image works in Compose and in Kubernetes without a rebuild." |
| 5 CI/CD | "Two quality jobs in parallel, then build, scan and push. The build job needs both, so an image is never built from failing code." |
| 6 Security gate | Slow down here. "The gate blocked my first build — three fixable HIGH CVEs in starlette, which I never installed. FastAPI pulls it in. I fixed it by upgrading, not by suppressing." |
| 7 Terraform | "Fifteen resources planned: a VPC, two public subnets in two AZs because EKS refuses one, the IAM roles, the cluster and a node group. I'll be straight about the limitation in a moment." |
| 8 Kubernetes | "Five pods, three ClusterIP services, one Ingress, an HPA on the backend." |
| 9 Observability | "One line of code exposes `/metrics`. Prometheus discovers the pods and scrapes each one separately." |
| 10 Learnings | "Running it is the only test that counts — every pipeline bug I hit was invisible locally." |

---

## 2 · Codebase — 1 min 30 s

Editor open at the repo root.

- Show the top-level folders: `backend/`, `frontend/`, `helm/`, `terraform/`, `monitoring/`, `argocd/`, `.github/workflows/`.
- `backend/app/main.py` — scroll the endpoints. Say: "nine endpoints — health, ready, metrics, and full CRUD on books, plus a stats endpoint that sums pages on the FINISHED shelf."
- `backend/tests/conftest.py` — point at the first three lines. "`DATABASE_URL` is pointed at SQLite **before** the app is imported, because the engine is built at import time. That's what keeps the tests off the real database."
- `backend/Dockerfile` — "`USER appuser`, uid 10001."
- `frontend/Dockerfile` — "Two stages: node builds the bundle, then only `dist/` is copied into nginx-unprivileged, which runs as uid 101 and listens on 8080 because a non-root process can't bind to 80."
- `helm/bookshelf/templates/backend-deployment.yaml` — point at the `env:` block. "The password comes from a Secret, and `DATABASE_URL` is built from it with `$(POSTGRES_PASSWORD)` — which only works because Kubernetes expands variables declared **above** it in the list. I got that wrong the first time."

---

## 3 · CI/CD — 2 min

This is the one that has to be live. Make a tiny real change.

```bash
# edit README.md - add a line, anything
git add README.md
git commit -m "docs: note the demo recording"
git push origin main
```

Switch to the Actions tab and refresh. While it runs:

- "Two jobs start together — tests and the chart lint."
- Open the **Tests and frontend build** job: flake8, 11 pytest tests, `npm ci`, `npm run build`, artifact uploaded.
- When `Build, scan and push images` starts, open it and narrate the steps as they go green: image names lowercased, GHCR login, two builds, two Trivy reports, **two security gates**, push.
- When it finishes: open the GHCR package page. "Tagged with the commit SHA, never `latest`."

If the run is slow, cut to the Terraform section and come back — don't sit watching a spinner.

---

## 4 · Terraform — 1 min 30 s

```bash
cd terraform
terraform init
terraform validate
terraform plan
```

Narrate: "Fifteen to add. VPC, internet gateway, route table and associations, two public subnets in
`ap-south-1a` and `1b`, four IAM objects, the EKS cluster and a managed node group."

**Then say this plainly, on camera:**

> "I don't have an AWS account with billing enabled, so I never ran `apply` or `destroy`, and I have no
> AWS Console screenshot. The plan is real — it runs against the AWS provider with the credential calls
> skipped, which only works because the config has no data sources. That's written up under Known
> Limitations in the README."

Don't apologise for it twice. State it, point at the README, move on.

---

## 5 · Argo CD — 1 min 30 s

Browser tab 5, already logged in.

- Show the `bookshelf` application tile: **Synced / Healthy**, source `github.com/piroBeastie/bookshelf`, path `helm/bookshelf`.
- Open it and show the resource tree.
- "Argo CD renders the Helm chart straight from this repository. Nothing here was applied with kubectl."
- Demonstrate self-healing — this is the bit that lands:

```bash
kubectl scale deployment bookshelf-backend -n bookshelf-gitops --replicas=3
kubectl get deploy bookshelf-backend -n bookshelf-gitops          # shows 3
# wait ~20 seconds
kubectl get deploy bookshelf-backend -n bookshelf-gitops          # back to 1
```

> "Git says one replica. I changed the cluster directly and Argo CD put it back. With `selfHeal` on,
> editing the cluster does nothing permanent — if you want a different number, you change the file."

---

## 6 · Kubernetes — 1 min 30 s

```bash
kubectl get pods -n bookshelf
kubectl get svc -n bookshelf
kubectl get ingress,hpa -n bookshelf
helm list -n bookshelf
```

- "Five pods Running — two backend, two frontend, one Postgres."
- "Three ClusterIP services. Nothing is exposed except the Ingress."
- "The Ingress routes `/` to the frontend and `/api` to the backend over one hostname."

Then switch to browser tab 1 and **use the app on camera**: add a book, move it to READING, rate it,
watch the stat cards change. "That's going through the Ingress, to nginx, to FastAPI, to Postgres."

---

## 7 · Prometheus — 45 s

Browser tab 6 (`/targets`).

- "`bookshelf-backend`, two of two targets up — each pod scraped individually, labelled with its pod
  name. A static target pointed at the Service would be load balanced to a random pod every scrape and
  the counters would jump around."
- Optionally run a query: `up{job="bookshelf-backend"}` → two series, both `1`.

---

## 8 · Grafana — 45 s

Browser tab 7, dashboard open, time range **Last 15 minutes**.

```promql
sum by (handler) (rate(http_requests_total{job="bookshelf-backend"}[5m]))
```

- "One line per endpoint. The data source is provisioned from `monitoring/grafana-values.yaml`, so it's
  code, not something I clicked together."
- If the graph is flat, run the load script in a terminal and let the lines climb on camera.

---

## 9 · Close — 20 s

> "Everything you saw came from one repository. A commit runs the tests, builds two images, scans them,
> publishes them tagged with that commit, and Argo CD puts them in the cluster. The one gap is
> `terraform apply`, and that's documented. Thanks for watching."

---

## Recording tips

- **Zoom the terminal to ~16pt.** Default font is unreadable in a compressed MP4.
- Light theme in the editor records better than dark at low bitrates.
- Close Slack, mail and notifications before you start.
- Do a 30-second test recording first and listen back — check the mic actually picked you up.
- One take is fine. Small stumbles are fine. A missing section is not.
- If something breaks live, say what broke and what you'd check. That reads better than cutting.
