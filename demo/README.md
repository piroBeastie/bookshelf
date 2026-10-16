# demo

Submission artefacts for the final presentation.

| file | what it is |
|---|---|
| [`presentation.mp4`](presentation.mp4) | 6:12 walkthrough, 1920x1080, **captions on screen, no narration** |
| [`slides.pptx`](slides.pptx) | 10 slides - overview, stack, architecture, CI/CD, security, infrastructure, Kubernetes, observability, learnings |
| [`VIDEO-SCRIPT.md`](VIDEO-SCRIPT.md) | the running order, and the commands that bring the whole stack up before recording |

## About the video

No voice track - every section is explained by a caption on screen, so it can be watched with the sound
off.

The terminal sections are **real screen recordings**: the commands you see are running live while the
video records, and the output is whatever they actually printed. The browser sections (the app, the
GitHub Actions run, the GHCR package page, Argo CD, Prometheus, Grafana) are full-resolution
screenshots of those same live systems, held on screen long enough to read.

Running order:

| at | section |
|---|---|
| 0:00 | title |
| 0:07 | the application in the browser |
| 0:15 | codebase - endpoints, both Dockerfiles |
| 0:57 | testing - flake8 and 11 pytest tests |
| 1:39 | docker compose - three services, non-root, Alembic migration |
| 2:19 | CI/CD - the green pipeline run |
| 2:27 | the build job, Trivy reports and both security gates |
| 2:36 | images in GHCR, tagged with the commit SHA |
| 2:44 | terraform validate and plan - 15 resources |
| 3:44 | the one honest limitation: no `terraform apply` |
| 3:54 | kubernetes - pods, services, ingress, HPA, helm list |
| 4:39 | Argo CD synced to main |
| 4:48 | GitOps self-healing: manual drift reverted |
| 5:46 | Prometheus - 2/2 targets up |
| 5:55 | Grafana - request rate per endpoint |
| 6:04 | the whole chain |

To re-record it, the pre-flight block in [`VIDEO-SCRIPT.md`](VIDEO-SCRIPT.md) brings the cluster, the app,
monitoring and Argo CD up first.
