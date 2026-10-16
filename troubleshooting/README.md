# troubleshooting

Two manifests that are broken on purpose, and the commands that find the fault.
Apply one, diagnose it, delete it.

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n bookshelf
kubectl describe pod -l app=broken-image -n bookshelf | tail -15
kubectl delete -f troubleshooting/broken-image.yaml
```

| file | symptom | where the answer is |
|---|---|---|
| `broken-image.yaml` | pod stuck in `ImagePullBackOff` | `kubectl describe pod` - the Events list the registry's 404 |
| `broken-service.yaml` | Service exists, nothing answers it | `kubectl get endpoints broken-service` is empty, because the selector matches no pod |

The lesson in both: `kubectl get pods` tells you *that* something is wrong.
`kubectl describe` and `kubectl get endpoints` tell you *what*.

For the service one, compare the two:

```bash
kubectl get endpoints bookshelf-backend -n bookshelf   # has addresses
kubectl get endpoints broken-service -n bookshelf      # <none>
kubectl get pods -n bookshelf --show-labels            # no pod carries app=label-that-does-not-exist
```

A Service is only a label selector. If no pod carries the label, the Service is a
perfectly healthy object pointing at nothing.
