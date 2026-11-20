"""GitHub side of the radar: repository details and the most-starred new AI repositories.

Uses the public REST API. A token is optional: in GitHub Actions the workflow passes
the automatic ``GITHUB_TOKEN`` (no secret to create); without one the unauthenticated
limits (60 requests per hour, 10 searches per minute) are still enough for one run.
"""

import logging
import re
from datetime import date

import requests

log = logging.getLogger(__name__)

API = "https://api.github.com"
# Topics searched for new AI repositories; results are merged and ranked by stars.
AI_TOPICS = ("llm", "ai-agents", "rag", "generative-ai", "mcp", "machine-learning")

# First path segments of github.com URLs that are not owner/repo pages.
_RESERVED = {
    "about", "apps", "blog", "collections", "contact", "customer-stories", "enterprise",
    "events", "explore", "features", "issues", "login", "marketplace", "new", "notifications",
    "orgs", "pricing", "pulls", "readme", "search", "security", "settings", "site", "sponsors",
    "topics", "trending", "users",
}
_REPO_URL = re.compile(r"^https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+)", re.IGNORECASE)


def parse_repo(url: str) -> str | None:
    """``owner/name`` for a link to a GitHub repository (or a page inside one), else None."""
    match = _REPO_URL.match(url or "")
    if not match:
        return None
    owner, name = match.groups()
    name = name.removesuffix(".git")
    if owner.lower() in _RESERVED or not name or name.startswith("."):
        return None
    return f"{owner}/{name}"


def _summary(repo: dict) -> dict:
    return {
        "repo": repo["full_name"],
        "url": repo["html_url"],
        "description": (repo.get("description") or "").strip(),
        "stars": int(repo.get("stargazers_count", 0)),
        "language": repo.get("language") or "",
        "created_at": (repo.get("created_at") or "")[:10],
        "pushed_at": (repo.get("pushed_at") or "")[:10],
        "topics": repo.get("topics", [])[:5],
    }


class GitHubClient:
    def __init__(self, token: str | None = None, session=None, timeout: float = 15.0):
        self.session = session or requests.Session()
        self.timeout = timeout
        self.headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                        "User-Agent": "ai-news-radar"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: dict | None = None) -> dict | None:
        try:
            response = self.session.get(f"{API}{path}", params=params, headers=self.headers,
                                        timeout=self.timeout)
        except requests.RequestException as exc:
            log.warning("GitHub request %s failed: %s", path, exc)
            return None
        if response.status_code != 200:
            log.warning("GitHub request %s returned HTTP %s", path, response.status_code)
            return None
        return response.json()

    def repo(self, full_name: str) -> dict | None:
        """Stars, language and description of ``owner/name``; None if unavailable."""
        data = self._get(f"/repos/{full_name}")
        return _summary(data) if data else None

    def new_ai_repos(self, since: date, topics: tuple[str, ...] = AI_TOPICS, n: int = 10,
                     max_checks: int = 20) -> list[dict]:
        """Most-starred repositories created on or after ``since`` with an AI topic.

        The search API cannot OR topics, so each topic is searched and the results merged.
        Candidates are then checked one by one, most-starred first, and star-farmed
        repositories are dropped (see ``looks_star_farmed``).
        """
        found: dict[str, dict] = {}
        for topic in topics:
            data = self._get("/search/repositories", {
                "q": f"topic:{topic} created:>={since.isoformat()} fork:false archived:false",
                "sort": "stars", "order": "desc", "per_page": 20,
            })
            for item in (data or {}).get("items", []):
                found.setdefault(item["full_name"], item)

        kept, checks = [], 0
        swarm = name_swarms(found.values())
        candidates = sorted(found.values(), key=lambda r: (-r["stargazers_count"], r["full_name"]))
        for item in candidates:
            # Cheap filters first, without extra requests.
            if not item.get("language") or _stem(item["name"]) in swarm:
                continue
            if checks == max_checks:  # two requests per check: stay within rate limits
                break
            checks += 1
            details = self._get(f"/repos/{item['full_name']}")
            owner = self._get(f"/users/{item['owner']['login']}")
            if details is None or owner is None or looks_star_farmed(details, owner):
                log.info("Skipping %s (unverifiable or star-farmed)", item["full_name"])
                continue
            kept.append(_summary(details))
            if len(kept) == n:
                break
        return kept


SWARM_OWNERS = 3


def _stem(name: str) -> str:
    """First three words of a repository name: 'blender-ai-copilot-studio' -> 'blender-ai-copilot'."""
    return "-".join([w for w in re.split(r"[-_.\s]+", name.lower()) if w][:3])


def name_swarms(items) -> set[str]:
    """Name stems published by at least SWARM_OWNERS different accounts at once.

    Spam campaigns push dozens of near-identical repositories from throwaway accounts
    ('Gemini-Config-Checker-', 'blender-ai-copilot-studio', '-flow', '-lab'...).
    """
    owners: dict[str, set[str]] = {}
    for item in items:
        owners.setdefault(_stem(item["name"]), set()).add(item["owner"]["login"].lower())
    return {stem for stem, who in owners.items() if len(who) >= SWARM_OWNERS}


# A genuine new repository has few watchers compared with its stars; star-farming
# accounts usually star and watch at the same time.
MAX_WATCHER_RATIO = 0.15
NEW_ACCOUNT_DAYS = 60
MIN_OWNER_FOLLOWERS = 5


def looks_star_farmed(repo: dict, owner: dict) -> bool:
    """Heuristics for repositories pushed up by fake stars (often malware lures).

    Flags a repository with no detected language, or with nearly as many watchers as
    stars, or owned by a brand-new account that nobody follows.
    """
    stars = max(int(repo.get("stargazers_count", 0)), 1)
    if not repo.get("language"):
        return True
    if int(repo.get("subscribers_count", 0)) / stars > MAX_WATCHER_RATIO:
        return True
    created, owner_created = repo.get("created_at", "")[:10], owner.get("created_at", "")[:10]
    if created and owner_created:
        account_age = (date.fromisoformat(created) - date.fromisoformat(owner_created)).days
        if account_age < NEW_ACCOUNT_DAYS and int(owner.get("followers", 0)) < MIN_OWNER_FOLLOWERS:
            return True
    return False
