"""Custom Prometheus exporter (runs on the VM as a Python process on port 8000).

Polls the ML app's /api/latest-confidence endpoint every 5 seconds and exposes
the value as a single Prometheus gauge named exactly `prediction_confidence_score`.
If the endpoint is unreachable, the default value 1.0 is reported.
"""
import os
import time
import requests
from prometheus_client import start_http_server, Gauge

# The app is exposed on the Minikube NodePort 32500 (forwarded to the VM host).
APP_URL = os.environ.get("APP_URL", "http://localhost:32500")
LATEST_CONFIDENCE_ENDPOINT = APP_URL.rstrip("/") + "/api/latest-confidence"
POLL_INTERVAL_SECONDS = 5
EXPORTER_PORT = 8000

prediction_confidence_score = Gauge(
    "prediction_confidence_score",
    "Latest sentiment-model prediction confidence polled from the ML API",
)


def poll_once():
    try:
        resp = requests.get(LATEST_CONFIDENCE_ENDPOINT, timeout=3)
        resp.raise_for_status()
        confidence = float(resp.json().get("confidence", 1.0))
    except Exception:
        # Endpoint unreachable -> default value per the project spec.
        confidence = 1.0
    prediction_confidence_score.set(confidence)
    return confidence


if __name__ == "__main__":
    start_http_server(EXPORTER_PORT)
    print(f"Exporter listening on :{EXPORTER_PORT}, polling {LATEST_CONFIDENCE_ENDPOINT} every {POLL_INTERVAL_SECONDS}s")
    while True:
        value = poll_once()
        print(f"prediction_confidence_score={value}")
        time.sleep(POLL_INTERVAL_SECONDS)
