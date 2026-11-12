"""Keyword filter that decides whether a Hacker News title is about AI.

Short acronyms (AI, LLM, RAG...) are matched case-sensitively so that ordinary
words such as "rag" or names such as "Ai Weiwei" do not count. Longer terms and
product names are matched case-insensitively.
"""

import re

# (label, pattern, case_sensitive)
_KEYWORDS: list[tuple[str, str, bool]] = [
    # Acronyms
    ("AI", r"\bAIs?\b|\bA\.I\.|\bGenAI\b", True),
    ("AGI", r"\bAGI\b", True),
    ("LLM", r"\bLLMs?\b", True),
    ("GPT", r"\bGPT(?:s|-?\d[\w.]*)?\b", True),
    ("RAG", r"\bRAG\b", True),
    ("ML", r"\bML\b", True),
    ("NLP", r"\bNLP\b", True),
    ("MCP", r"\bMCP\b", True),
    ("RLHF", r"\bRLHF\b", True),
    ("xAI", r"\bxAI\b", True),
    # Concepts
    ("artificial intelligence", r"\bartificial intelligence\b", False),
    ("machine learning", r"\bmachine[- ]learning\b", False),
    ("deep learning", r"\bdeep[- ]learning\b", False),
    ("reinforcement learning", r"\breinforcement learning\b", False),
    ("neural", r"\bneural\b", False),
    ("language model", r"\blanguage models?\b", False),
    ("transformer", r"\btransformer (?:models?|architectures?)\b", False),
    ("diffusion", r"\bdiffusion models?\b|\bstable diffusion\b", False),
    ("embeddings", r"\bembeddings?\b", False),
    ("vector database", r"\bvector (?:databases?|dbs?|stores?|search)\b", False),
    ("retrieval-augmented", r"\bretrieval[- ]augmented\b", False),
    ("fine-tuning", r"\bfine[- ]?tun(?:e|ed|es|ing)\b", False),
    ("agents", r"\bagentic\b|\bmulti[- ]agent\b|\bcoding agents?\b", False),
    ("prompt injection", r"\bprompt (?:injection|engineering)\b|\bjailbreak", False),
    ("chatbot", r"\bchat ?bots?\b", False),
    ("vibe coding", r"\bvibe[- ]cod(?:e|ed|ing)\b", False),
    ("Model Context Protocol", r"\bmodel context protocol\b", False),
    # Labs, models and tools
    ("OpenAI", r"\bOpenAI\b", False),
    ("ChatGPT", r"\bChatGPT\b", False),
    ("Anthropic", r"\bAnthropic\b", False),
    ("Claude", r"\bClaude\b", False),
    # Exclude the Gemini protocol (gemini://), a small-web project often on HN.
    ("Gemini", r"\bGemini\b(?!\s*(?:protocol|capsule)|://)", False),
    ("DeepMind", r"\bDeepMind\b|\bAlpha(?:Fold|Go|Zero)\b", False),
    ("DeepSeek", r"\bDeepSeek\b", False),
    ("Mistral", r"\bMistral\b", False),
    ("Llama", r"\bLlama\b|\bOllama\b|\bvLLM\b", False),
    ("Qwen", r"\bQwen\b", False),
    ("Hugging Face", r"\bhugging ?face\b", False),
    ("PyTorch", r"\bPyTorch\b|\bTensorFlow\b", False),
    ("Copilot", r"\bCopilot\b", False),
    ("Midjourney", r"\bMidjourney\b", False),
    ("LangChain", r"\bLangChain\b|\bLlamaIndex\b", False),
]

_COMPILED = [
    (label, re.compile(pattern, 0 if case_sensitive else re.IGNORECASE))
    for label, pattern, case_sensitive in _KEYWORDS
]


def match_ai_keywords(title: str) -> list[str]:
    """Return the labels of every AI keyword found in ``title`` (empty if none)."""
    if not title:
        return []
    return [label for label, regex in _COMPILED if regex.search(title)]


def is_ai_related(title: str) -> bool:
    return bool(match_ai_keywords(title))
