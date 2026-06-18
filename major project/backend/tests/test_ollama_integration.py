import json
import os
import sys
import pytest

# Ensure backend directory is on sys.path so tests can import app.py
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_analyze_feedback_with_sample(client):
    sample = {
        "feedback_text": "The onboarding was confusing and my manager didn't explain expectations.",
        "domain": "engineering",
    }
    resp = client.post("/api/feedback", json=sample)
    assert resp.status_code == 201
    data = resp.get_json()
    # Ensure top-level keys exist
    assert "suggestion" in data
    # suggestion can be dict (advanced) or string (basic); handle both
    suggestion = data["suggestion"]
    # If it's the LLM-style wrapper, it will be a dict with 'suggestion' inside
    if isinstance(suggestion, dict) and suggestion.get("type") == "llm":
        payload = suggestion.get("suggestion", {})
    elif isinstance(suggestion, dict) and "sentiment" in suggestion:
        payload = suggestion
    else:
        # Basic fallback: just ensure sentiment keys exist at top-level response
        payload = {}

    # If payload contains sentiment, assert allowed label
    if "sentiment" in payload:
        label = payload["sentiment"].get("label")
        assert label in {"positive", "neutral", "negative"}

    # Ensure the API preserved sentiment_label computed earlier
    assert "sentiment_label" in data
    assert data["sentiment_label"] in {"Positive", "Neutral", "Negative"}
