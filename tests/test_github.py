from datetime import date

import pytest
import requests
from conftest import NOW, FakeResponse, make_item

from radar.github import GitHubClient, looks_star_farmed, name_swarms, parse_repo
from radar.hn import to_record
from radar.site import github_week
from radar.storage import empty_posts, merge_posts
from radar.trends import prepare, top_github_repos


@pytest.mark.parametrize("url, expected", [
    ("https://github.com/anthropics/claude-code", "anthropics/claude-code"),
    ("https://www.github.com/a/b.git", "a/b"),
    ("https://github.com/a/b/tree/main/docs?x=1#y", "a/b"),
    ("http://GitHub.com/Owner/Repo.Name", "Owner/Repo.Name"),
    ("https://github.com/features/copilot", None),
    ("https://github.com/sponsors/someone", None),
    ("https://github.com/someone", None),
    ("https://gist.github.com/a/123", None),
    ("https://example.com/a/b", None),
    ("", None),
])
def test_parse_repo(url, expected):
    assert parse_repo(url) == expected


def repo(name="o/r", stars=500, watchers=3, language="Python", created="2026-11-12", owner="o"):
    return {"full_name": name, "name": name.split("/")[1], "owner": {"login": owner},
            "html_url": f"https://github.com/{name}", "description": f"About {name}",
            "stargazers_count": stars, "subscribers_count": watchers, "language": language,
            "created_at": f"{created}T10:00:00Z", "pushed_at": f"{created}T11:00:00Z",
            "topics": ["llm"]}


OLD_OWNER = {"created_at": "2019-01-01T00:00:00Z", "followers": 50}
NEW_OWNER = {"created_at": "2026-11-01T00:00:00Z", "followers": 0}


def test_looks_star_farmed():
    assert not looks_star_farmed(repo(), OLD_OWNER)
    assert looks_star_farmed(repo(language=None), OLD_OWNER)
    assert looks_star_farmed(repo(stars=500, watchers=400), OLD_OWNER)  # bots watch what they star
    assert looks_star_farmed(repo(), NEW_OWNER)
    assert not looks_star_farmed(repo(), {**NEW_OWNER, "followers": 40})


def test_name_swarms():
    items = [repo(f"u{i}/Gemini-Config-Checker-", owner=f"u{i}") for i in range(3)]
    items += [repo("x/blender-ai-copilot-lab", owner="x"), repo("y/blender-ai-copilot-flow", owner="y"),
              repo("z/real-project", owner="z")]
    assert name_swarms(items) == {"gemini-config-checker"}


class FakeGitHub:
    """Answers /repos, /users and /search/repositories from dictionaries."""

    def __init__(self, repos, owners, search):
        self.repos, self.owners, self.search = repos, owners, search
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        path = url.split("api.github.com", 1)[1]
        self.calls.append((path, params, headers))
        if path.startswith("/repos/"):
            name = path.removeprefix("/repos/")
            return FakeResponse(self.repos[name]) if name in self.repos else FakeResponse(status_code=404)
        if path.startswith("/users/"):
            return FakeResponse(self.owners.get(path.removeprefix("/users/"), OLD_OWNER))
        topic = params["q"].split()[0].removeprefix("topic:")
        if topic == "broken":
            raise requests.ConnectionError("down")
        return FakeResponse({"items": self.search.get(topic, [])})


def test_new_ai_repos_merges_topics_and_drops_spam():
    good, other = repo("a/good", stars=900), repo("b/other", stars=300)
    farmed = repo("c/farmed", stars=2000, watchers=1500, owner="c")
    newbie = repo("d/newbie", stars=800, owner="d")
    no_lang = repo("e/nolang", stars=5000, language=None, owner="e")
    swarm = [repo(f"s{i}/Clone-Tool-X", stars=700, owner=f"s{i}") for i in range(3)]
    everything = [good, other, farmed, newbie, no_lang, *swarm]
    session = FakeGitHub(
        repos={r["full_name"]: r for r in everything},
        owners={"d": NEW_OWNER},
        search={"llm": [good, farmed, no_lang, *swarm], "rag": [other, newbie, good]},
    )
    client = GitHubClient(token="t", session=session)
    result = client.new_ai_repos(since=date(2026, 11, 10), topics=("llm", "rag", "broken"))
    assert [r["repo"] for r in result] == ["a/good", "b/other"]
    assert result[0]["stars"] == 900 and result[0]["language"] == "Python"
    assert session.calls[0][2]["Authorization"] == "Bearer t"
    assert "created:>=2026-11-10" in session.calls[0][1]["q"]
    # Spam caught by the cheap filters never costs a request.
    assert not any("nolang" in path or "Clone-Tool" in path for path, _, _ in session.calls)


def test_repo_details_and_failures():
    session = FakeGitHub(repos={"a/b": repo("a/b", stars=42)}, owners={}, search={})
    client = GitHubClient(session=session)
    assert client.repo("a/b")["stars"] == 42
    assert client.repo("missing/repo") is None
    assert "Authorization" not in session.calls[0][2]


def hn_posts():
    specs = [  # id, hours before NOW, url, score, comments
        (1, 2, "https://github.com/acme/agent", 300, 100),
        (2, 30, "https://github.com/acme/agent/blob/main/README.md", 50, 10),
        (3, 5, "https://github.com/solo/tool", 80, 20),
        (4, 6, "https://example.com/not-github", 999, 999),
        (5, 400, "https://github.com/old/repo", 900, 900),  # 16 days earlier
    ]
    records = []
    for item_id, hours, url, score, comments in specs:
        rec = to_record(make_item(item_id, f"AI {item_id}", hours_ago=hours, score=score,
                                  comments=comments, url=url), ["AI"], NOW)
        rec.update(theme="dev-tools")
        records.append(rec)
    return prepare(merge_posts(empty_posts(), records))


def test_top_github_repos_groups_posts_of_the_same_repo():
    table = top_github_repos(hn_posts()[lambda d: d["id"] != 5])
    assert table["repo"].tolist() == ["acme/agent", "solo/tool"]
    first = table.iloc[0]
    assert (first["stories"], first["engagement"], first["title"]) == (2, 460, "AI 1")
    assert top_github_repos(hn_posts().iloc[0:0]).empty


def test_github_week_without_and_with_a_client():
    df, end = hn_posts(), NOW.date()
    offline = github_week(df, date(2026, 11, 1), end)
    assert offline["start"] == "2026-11-06" and offline["new"] == []
    assert [r["repo"] for r in offline["on_hn"]] == ["acme/agent", "solo/tool"]  # old/repo is out of the week
    assert offline["on_hn"][0]["stars"] is None

    class Client:
        def repo(self, name):
            return {"url": f"https://github.com/{name}", "description": "d", "stars": 7, "language": "Go"}

        def new_ai_repos(self, since):
            return [{"repo": "n/new", "since": since.isoformat()}]

    online = github_week(df, date(2026, 11, 1), end, Client())
    assert online["on_hn"][0]["stars"] == 7
    assert online["new"] == [{"repo": "n/new", "since": "2026-11-06"}]
