# /// script
# requires-python = ">=3.11"
# dependencies = ["PyGithub>=2.4"]
# ///
from __future__ import annotations

import json
import os
import sys
from typing import Any

MARKER = "<!-- parsecore-bot:welcome -->"
MAINTAINERS = ["Error44s", "DevilPedrow"]
FIRST_TIME = {"FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "NONE"}
GREET_ACTIONS = {"opened", "reopened", "ready_for_review"}


def render_welcome(
    author: str,
    is_first_time: bool,
    reviewers: list[str],
    maintainers: list[str],
    contributing_url: str,
) -> str:
    """Build the sticky welcome comment.

    Args:
        author: The pull request author's login.
        is_first_time: Whether this is the author's first contribution.
        reviewers: The currently requested reviewers, if any.
        maintainers: The fallback maintainers to name when none are requested.
        contributing_url: Absolute link to the contribution guide.

    Returns:
        The rendered comment body, professional and emoji-free.
    """
    if is_first_time:
        opening = (
            f"Welcome, @{author}, and thank you for your first contribution to "
            "parsecore."
        )
    else:
        opening = f"Thank you for the contribution, @{author}."

    who = reviewers or maintainers
    mention = ", ".join(f"@{name}" for name in who)
    if reviewers:
        review_line = f"The requested reviewers ({mention}) will look at this shortly."
    else:
        review_line = f"{mention} will review this shortly."

    return "\n".join([
        MARKER,
        "## Thanks for your pull request",
        "",
        opening,
        "",
        "The automated checks run on every push; their result appears in a "
        "separate review comment below. A maintainer then goes through the "
        "change by hand, so please allow a little time for a human review.",
        "",
        review_line,
        "",
        "While you wait, please make sure the checklist in the pull request "
        f"template is complete. Our contribution guide is in [CONTRIBUTING.md]({contributing_url}).",
    ])


def _event() -> dict[str, Any]:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _run_ci() -> int:
    from github import Github

    payload = _event()
    action = payload.get("action", "")
    if action and action not in GREET_ACTIONS:
        print("welcome skipped for action:", action)
        return 0

    pr_payload = payload.get("pull_request")
    if not pr_payload:
        print("no pull request in payload; nothing to do")
        return 0

    token = os.environ.get("GH_TOKEN") or os.environ["GITHUB_TOKEN"]
    repo = Github(token).get_repo(os.environ["GITHUB_REPOSITORY"])
    pull = repo.get_pull(pr_payload["number"])

    author = pull.user.login if pull.user else "there"
    association = (pr_payload.get("author_association") or "").upper()
    is_first_time = association in FIRST_TIME
    reviewers = [r.login for r in pull.get_review_requests()[0]]
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    contributing_url = f"{server}/{os.environ['GITHUB_REPOSITORY']}/blob/main/CONTRIBUTING.md"
    body = render_welcome(author, is_first_time, reviewers, MAINTAINERS, contributing_url)

    mine = next(
        (c for c in pull.get_issue_comments()
         if c.user and c.user.type == "Bot" and MARKER in (c.body or "")),
        None,
    )
    if mine is not None:
        mine.edit(body)
        print("welcome comment updated")
    else:
        pull.create_issue_comment(body)
        print("welcome comment posted")
    return 0


def _self_test() -> int:
    ok = True

    def check(label: str, got: Any, expected: Any) -> None:
        nonlocal ok
        if got != expected:
            ok = False
        print(f"  [{'ok' if got == expected else 'FAIL'}] {label}: {got!r}")

    url = "https://github.com/O-Lib/parsecore/blob/main/CONTRIBUTING.md"
    first = render_welcome("octocat", True, [], MAINTAINERS, url)
    check("first-timer is welcomed", "first contribution" in first, True)
    check("names maintainers when none requested", "@Error44s" in first, True)
    check("links the contribution guide", url in first, True)

    repeat = render_welcome("octocat", False, ["DevilPedrow"], MAINTAINERS, url)
    check("returning contributor greeting", "Thank you for the contribution" in repeat, True)
    check("pings requested reviewer", "@DevilPedrow" in repeat, True)
    check("does not name unrequested maintainer", "@Error44s" not in repeat, True)

    check("comment is emoji-free", any(ord(c) > 0x2600 for c in first), False)
    check("carries the sticky marker", first.startswith(MARKER), True)
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()
    return _run_ci()


if __name__ == "__main__":
    raise SystemExit(main())
