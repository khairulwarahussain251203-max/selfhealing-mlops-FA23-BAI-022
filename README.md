# Self-Healing MLOps Pipeline — FA23-BAI-022

**Student:** Khair Ul wara Hussain · **Roll No:** FA23-BAI-022
CSC413 — DevOps for Cloud Computing · Lab Project "The Self-Healing Pipeline"

A closed-loop CI/CD + MLOps pipeline that deploys a HuggingFace DistilBERT sentiment
analysis API, continuously monitors its prediction confidence, and **automatically heals**
(rolls traffic over to a stable fallback) when confidence drops below the assigned
threshold for more than one minute — with no human in the loop.

## Assigned customization values (row FA23-BAI-022)

| Field | Value |
|---|---|
| Confidence Threshold | `0.587` (`alert.rules.yml` expr + Grafana red threshold line) |
| Stable Model Code | `stable-v0-C9B9` (`stable-fallback/app.py` `model_version`, both occurrences) |
| Webhook Token | `ROLLBACK_034051_TOKEN` (`alertmanager.yml` + Jenkins rollback trigger) |
| Test Category / Text | `RESTAURANT` — "The food was absolutely delicious and the chef clearly has exceptional skill" |

## Repository layout (main branch)

```
app.py                      # PROVIDED — unstable DistilBERT API
requirements.txt            # PROVIDED
templates/index.html        # PROVIDED — frontend (Selenium element IDs)
Dockerfile                  # unstable image build
Jenkinsfile                 # CI: sentiment-ci-pipeline (6 stages)
Jenkinsfile.rollback        # rollback-to-stable pipeline
exporter.py                 # Prometheus exporter (prediction_confidence_score :8000)
prometheus.yml              # scrape 10s, job sentiment-ml-exporter
alert.rules.yml             # alert ModelConfidenceDrift, expr < 0.587 for 1m
alertmanager.yml            # webhook -> Jenkins rollback (token ROLLBACK_034051_TOKEN)
k8s/
  pvc.yaml                  # sentiment-logs-pvc
  blue-deployment.yaml      # sentiment-blue-deployment  (unstable, slot: blue, 1 replica)
  green-deployment.yaml     # sentiment-green-deployment (stable,   slot: green, 2 replicas)
  service.yaml              # sentiment-api-service (NodePort 32500, selector slot: blue)
tests/
  test_api.py               # 4 PyTest functions
  test_ui.py                # Selenium test_frontend_sentiment
stable-fallback/            # build context for the stable image (also a dedicated branch)
  app.py                    # rule-based stable fallback (model_version stable-v0-C9B9)
  requirements.txt
  Dockerfile
```

The **`stable-fallback` branch** holds the stable `app.py` (with code `C9B9`),
`requirements.txt`, and `Dockerfile` at its root, as required by the project spec.

## Architecture

```
GitHub push ──► Jenkins (sentiment-ci-pipeline)
                 Fetch ─ Build and Run ─ Unit Test ─ UI Test ─ Build and Push ─ Deploy to Minikube
                                                                   │                    │
                                                   DockerHub ◄─────┘          Minikube (blue+green)
                                                                                        │ NodePort 32500
exporter.py :8000 ──poll /api/latest-confidence──► (app) ◄──── socat host:32500 ────────┘
        │ prediction_confidence_score
        ▼
Prometheus :9090 ──(alert ModelConfidenceDrift < 0.587 for 1m)──► Alertmanager :9093
                                                                        │ webhook (token)
                                                                        ▼
                                                  Jenkins rollback-to-stable job
                                                                        │ kubectl patch service
                                                                        ▼
                                            Service selector blue ──► green  (self-healed)
Grafana :3000  ── dashboard "MLOps - Sentiment API Health" (red threshold line @ 0.587)
```

## Infrastructure

Deployed on an **AWS EC2 instance** (t3.large class, 2 vCPU / 8 GB RAM + 8 GB swap):
public IP `16.170.218.108`, Ubuntu 26.04 LTS, ports 22/8080/9090/9093/3000/8000/32500.
Prometheus + Alertmanager run as Docker containers (host network); Grafana via apt;
the app runs on Minikube exposed via NodePort 32500 (forwarded to the host with socat).

<!-- CI webhook verification: push trigger test -->
