"""Theme classification and one-sentence summaries with the Gemini API.

Stories are sent in batches; Gemini's structured output mode constrains the
answer to a JSON array whose ``theme`` field is one of the fixed themes.
The API key is read from the environment by the caller and sent in a header,
never in the URL.
"""

import json
import logging
import time

import requests

from radar.config import THEMES

log = logging.getLogger(__name__)

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Alias that always points to the current Flash-Lite model, which has a free tier.
DEFAULT_MODEL = "gemini-flash-lite-latest"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

THEME_GUIDE = {
    "models": "releases, updates, benchmarks or comparisons of specific AI models, open-weight models",
    "agents": "autonomous or tool-using AI agents, agent frameworks, computer use, multi-agent systems",
    "rag": "retrieval-augmented generation, embeddings, vector databases, search over documents",
    "dev-tools": "libraries, SDKs, coding assistants, IDEs, inference servers and infrastructure for building with AI",
    "security": "prompt injection, jailbreaks, vulnerabilities, data leaks, misuse and AI safety incidents",
    "research": "papers, scientific results, new techniques, interpretability and alignment research",
    "business": "companies, funding, acquisitions, pricing, hardware supply, jobs and the AI market",
    "regulation": "laws, policy, lawsuits, copyright and government action on AI",
    "other": "opinion, culture, education and anything that fits no other theme",
}

PROMPT = """You label Hacker News stories for a daily AI newsletter.

For each story, return an object with:
- "id": the story id, unchanged.
- "theme": exactly one of the themes below.
- "summary": one plain English sentence (at most 25 words) saying what the story is about.
  Use only what the title and the link domain tell you; do not invent names, numbers or claims.

Themes:
{themes}

Stories (JSON):
{stories}
"""

RESPONSE_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "id": {"type": "INTEGER"},
            "theme": {"type": "STRING", "enum": list(THEMES)},
            "summary": {"type": "STRING"},
        },
        "required": ["id", "theme", "summary"],
    },
}


class ClassificationError(RuntimeError):
    pass


def build_request(posts: list[dict]) -> dict:
    stories = [
        {"id": int(p["id"]), "title": p["title"], "domain": p.get("domain") or "news.ycombinator.com"}
        for p in posts
    ]
    themes = "\n".join(f"- {slug}: {THEME_GUIDE[slug]}" for slug in THEMES)
    prompt = PROMPT.format(themes=themes, stories=json.dumps(stories, ensure_ascii=False, indent=1))
    return {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }


def parse_response(payload: dict, expected_ids: set[int]) -> dict[int, dict]:
    """Extract ``{id: {"theme", "summary"}}`` from a generateContent response.

    Unknown ids are dropped and an unknown theme falls back to ``other``.
    """
    try:
        parts = payload["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        items = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ClassificationError(f"Unexpected Gemini response: {exc}") from exc
    if not isinstance(items, list):
        raise ClassificationError("Gemini response is not a JSON array")

    results: dict[int, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            post_id = int(item.get("id"))
        except (TypeError, ValueError):
            continue
        if post_id not in expected_ids:
            continue
        theme = str(item.get("theme", "")).strip().lower()
        summary = " ".join(str(item.get("summary", "")).split())
        results[post_id] = {"theme": theme if theme in THEMES else "other", "summary": summary}
    return results


class GeminiClassifier:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, session=None,
                 batch_size: int = 25, max_retries: int = 4, backoff: float = 5.0,
                 pause: float = 4.0, timeout: float = 90.0, sleep=time.sleep):
        if not api_key:
            raise ValueError("A Gemini API key is required")
        self.api_key = api_key
        self.model = model
        self.session = session or requests.Session()
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.backoff = backoff
        self.pause = pause  # between batches, to respect the free-tier rate limit
        self.timeout = timeout
        self.sleep = sleep

    def classify(self, posts: list[dict]) -> dict[int, dict]:
        """Classify ``posts``; batches that keep failing are logged and skipped."""
        results: dict[int, dict] = {}
        for start in range(0, len(posts), self.batch_size):
            batch = posts[start:start + self.batch_size]
            if start:
                self.sleep(self.pause)
            try:
                payload = self._generate(build_request(batch))
                results.update(parse_response(payload, {int(p["id"]) for p in batch}))
            except ClassificationError as exc:
                log.error("Batch of %d stories not classified: %s", len(batch), exc)
        return results

    def _generate(self, body: dict) -> dict:
        url = API_URL.format(model=self.model)
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        for attempt in range(self.max_retries + 1):
            last_try = attempt == self.max_retries
            try:
                response = self.session.post(url, json=body, headers=headers, timeout=self.timeout)
            except requests.RequestException as exc:
                if last_try:
                    raise ClassificationError(f"Request failed: {exc}") from exc
                error = str(exc)
            else:
                if response.status_code == 200:
                    return response.json()
                error = f"HTTP {response.status_code}: {response.text[:300]}"
                if response.status_code not in RETRYABLE_STATUS or last_try:
                    raise ClassificationError(error)
            delay = self.backoff * 2 ** attempt
            log.warning("Gemini call failed (%s), retrying in %.0fs", error, delay)
            self.sleep(delay)
        raise ClassificationError("Retries exhausted")  # pragma: no cover
