import json

import pytest
import requests
from conftest import FakeResponse

from radar.classifier import (
    THEME_GUIDE,
    ClassificationError,
    GeminiClassifier,
    build_request,
    parse_response,
)
from radar.config import THEMES


def gemini_payload(items):
    return {"candidates": [{"content": {"parts": [{"text": json.dumps(items)}]}}]}


class FakeGeminiSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.requests.append({"url": url, "json": json, "headers": headers})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


POSTS = [
    {"id": 1, "title": "OpenAI releases a new model", "domain": "openai.com"},
    {"id": 2, "title": "Ask HN: Best RAG stack?", "domain": ""},
]


def test_every_theme_has_a_description():
    assert set(THEME_GUIDE) == set(THEMES)


def test_build_request_constrains_themes():
    body = build_request(POSTS)
    schema = body["generationConfig"]["responseSchema"]
    assert schema["items"]["properties"]["theme"]["enum"] == list(THEMES)
    prompt = body["contents"][0]["parts"][0]["text"]
    assert "OpenAI releases a new model" in prompt
    assert "news.ycombinator.com" in prompt  # fallback domain for Ask HN


def test_parse_response_validates_output():
    payload = gemini_payload([
        {"id": 1, "theme": "models", "summary": "  OpenAI ships\n a model. "},
        {"id": 2, "theme": "not-a-theme", "summary": "A question."},
        {"id": 99, "theme": "rag", "summary": "Unknown id."},
        "garbage",
    ])
    results = parse_response(payload, {1, 2})
    assert results == {
        1: {"theme": "models", "summary": "OpenAI ships a model."},
        2: {"theme": "other", "summary": "A question."},
    }


def test_parse_response_rejects_invalid_json():
    payload = {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]}
    with pytest.raises(ClassificationError):
        parse_response(payload, {1})


def test_classify_sends_key_in_header_and_batches():
    session = FakeGeminiSession([
        FakeResponse(gemini_payload([{"id": 1, "theme": "models", "summary": "S1."}])),
        FakeResponse(gemini_payload([{"id": 2, "theme": "rag", "summary": "S2."}])),
    ])
    classifier = GeminiClassifier("secret", model="m", session=session, batch_size=1,
                                  sleep=lambda s: None)
    results = classifier.classify(POSTS)
    assert results == {1: {"theme": "models", "summary": "S1."},
                       2: {"theme": "rag", "summary": "S2."}}
    assert len(session.requests) == 2
    assert session.requests[0]["headers"]["x-goog-api-key"] == "secret"
    assert "secret" not in session.requests[0]["url"]
    assert session.requests[0]["url"].endswith("/models/m:generateContent")


def test_classify_retries_on_rate_limit():
    delays = []
    session = FakeGeminiSession([
        FakeResponse(status_code=429, text="quota"),
        requests.ConnectionError("boom"),
        FakeResponse(gemini_payload([{"id": 1, "theme": "agents", "summary": "S."}])),
    ])
    classifier = GeminiClassifier("k", session=session, backoff=1, sleep=delays.append)
    assert classifier.classify(POSTS[:1]) == {1: {"theme": "agents", "summary": "S."}}
    assert delays == [1, 2]


def test_classify_skips_batch_on_permanent_error():
    session = FakeGeminiSession([FakeResponse(status_code=400, text="bad request")])
    classifier = GeminiClassifier("k", session=session, sleep=lambda s: None)
    assert classifier.classify(POSTS) == {}


def test_classifier_requires_a_key():
    with pytest.raises(ValueError):
        GeminiClassifier("")
