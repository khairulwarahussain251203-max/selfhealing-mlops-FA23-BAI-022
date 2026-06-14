"""PyTest unit tests for the Sentiment API.

Run against BASE_URL = "http://<ip>:5000". All four function names below are
required exactly by the grading script.
"""
import os
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")


def test_health_endpoint():
    """GET /health -> HTTP 200; 'status':'healthy' and key 'model_version' present."""
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "model_version" in data


def test_predict_returns_label_and_confidence():
    """POST /predict -> HTTP 200; label in [POSITIVE,NEGATIVE]; 0<=confidence<=1; 'model_version' present.

    Uses the assigned APP test sentence (row FA23-BAI-022)."""
    r = requests.post(f"{BASE_URL}/predict", json={"text": "The food was absolutely delicious and the chef clearly has exceptional skill"})
    assert r.status_code == 200
    data = r.json()
    assert data["label"] in ["POSITIVE", "NEGATIVE"]
    assert 0 <= data["confidence"] <= 1
    assert "model_version" in data


def test_predict_negative_text():
    """POST /predict with negative text -> HTTP 200."""
    r = requests.post(f"{BASE_URL}/predict", json={"text": "This is terrible and I absolutely hate it"})
    assert r.status_code == 200


def test_health_returns_model_version_unstable():
    """GET /health -> model_version == 'unstable-v1' exactly."""
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json()["model_version"] == "unstable-v1"
