# demo

Submission artefacts for the final presentation.

| file | what it is | status |
|---|---|---|
| `slides.pptx` | 10-slide deck — overview, stack, architecture, CI/CD, security gate, infrastructure, Kubernetes, observability, learnings | committed |
| `VIDEO-SCRIPT.md` | shot-by-shot recording script: what to run, in what order, and what to say | committed |
| `presentation.mp4` | the recorded walkthrough | **to record** |

## Recording the video

Follow [`VIDEO-SCRIPT.md`](VIDEO-SCRIPT.md) top to bottom — its order is the order the submission
guidelines ask for, and it starts with a pre-flight block that brings the whole stack up before you hit
record.

When the file is exported, drop it in this folder as `presentation.mp4` and commit it:

```bash
git add demo/presentation.mp4
git commit -m "demo: presentation walkthrough video"
git push origin main
```

GitHub rejects files over 100 MB on a normal push. If the recording lands above that, either export at a
lower bitrate (1080p / ~2 Mbps is plenty for a screen capture) or attach it to a GitHub release instead
and link it here — the guidelines allow a release asset.
