import pytest

from radar.filters import is_ai_related, match_ai_keywords


@pytest.mark.parametrize("title", [
    "Show HN: I built an AI that reviews pull requests",
    "OpenAI announces a new reasoning model",
    "Running LLMs locally on a Raspberry Pi",
    "A practical guide to RAG pipelines",
    "Claude can now use a computer",
    "GPT-5 system card",
    "The state of agentic coding in 2026",
    "Fine-tuning small models for classification",
    "Prompt injection attacks against browser agents",
    "Why AI's energy use is hard to measure",
    "EU AI Act enforcement begins",
    "Gemini 3 Flash is now generally available",
    "Building a vector database from scratch",
])
def test_ai_titles_match(title):
    assert is_ai_related(title)


@pytest.mark.parametrize("title", [
    "Ai Weiwei opens a new exhibition in Berlin",
    "My favourite cleaning rag for cast iron pans",
    "Sending email from the command line",
    "Rust 2.0 released",
    "Exploring Gemini protocol capsules",
    "A tour of gemini://geminiprotocol.net",
    "The MAIL command in SMTP",
    "",
])
def test_non_ai_titles_do_not_match(title):
    assert not is_ai_related(title)


def test_match_returns_every_label():
    labels = match_ai_keywords("OpenAI and Anthropic LLMs compared")
    assert {"OpenAI", "Anthropic", "LLM"} <= set(labels)
