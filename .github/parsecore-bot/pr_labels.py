# /// script
# requires-python = ">=3.11"
# dependencies = ["PyGithub>=2.4"]
# ///
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

TRIAGE_LABEL = "Status: Needs Triage"

TYPE_BY_PREFIX = {
    "feat": "Type: Feature",
    "fix": "Type: Bug",
    "docs": "Type: Docs",
    "style": "Type: Refactor",
    "refactor": "Type: Refactor",
    "perf": "Type: Performance",
    "test": "Type: Test",
    "chore": "Type: Chore",
    "revert": "Type: Revert",
}

SCOPE_RULES = [
    (re.compile(r"^parsecore/Beatmaps/"), "Scope: Beatmap"),
    (re.compile(r"^parsecore/Rulesets/Mods/"), "Scope: Mods"),
    (re.compile(r"^parsecore/Rulesets/(?:\w+/)?Difficulty/"), "Scope: PP"),
    (re.compile(r"^parsecore/Rulesets/(?!\w+/Difficulty/|Difficulty/|Mods/)"), "Scope: Rulesets"),
    (re.compile(r"^parsecore/Scoring/"), "Scope: Scoring"),
    (re.compile(r"^\.github/"), "Scope: CI"),
    (re.compile(r"^pyproject\.toml$"), "Scope: Packaging"),
    (re.compile(r"\.md$", re.IGNORECASE), "Type: Docs"),
]

_TITLE = re.compile(r"^(\w+)(\([^)]*\))?(!)?:")

DRAFT_LABEL = "PR: Draft"
READY_LABEL = "PR: Ready For Review"

PA_LABELS = [
    "PA: Pending All Reviewers",
    "PA: Pending One Reviewer",
    "PA: Awaiting Author",
    "PA: Awaiting CI",
    "PA: Reviewer Assigned",
    "PA: Under Review",
    "PA: Second Opinion Needed",
    "PR: Approved",
    "PR: Changes Requested",
]


def content_labels(title: str, is_draft: bool, filenames: list[str]) -> set[str]:
    """Return the content labels a pull request should carry.

    Args:
        title: The pull request title.
        is_draft: Whether the pull request is a draft.
        filenames: The paths changed by the pull request.

    Returns:
        The set of type, scope, breaking and draft-state labels.
    """
    labels: set[str] = set()
    match = _TITLE.match(title.strip())
    if match:
        mapped = TYPE_BY_PREFIX.get(match.group(1).lower())
        if mapped:
            labels.add(mapped)
        if match.group(3) == "!":
            labels.add("Breaking Change")
    for name in filenames:
        for pattern, label in SCOPE_RULES:
            if pattern.search(name):
                labels.add(label)
    labels.add(DRAFT_LABEL if is_draft else READY_LABEL)
    return labels


def open_review_update(
    current: set[str],
    is_draft: bool,
    review_states: list[str],
    requested_reviewers: int,
) -> tuple[list[str], list[str]]:
    """Return ``(to_add, to_remove)`` for the review-state labels of an open PR.

    Args:
        current: The labels already on the pull request.
        is_draft: Whether the pull request is a draft.
        review_states: The latest non-comment review state per reviewer.
        requested_reviewers: The number of still-requested reviewers.
    """
    if is_draft:
        return [], []

    approved = sum(1 for s in review_states if s == "APPROVED")
    changes = sum(1 for s in review_states if s == "CHANGES_REQUESTED")
    total_reviewers = len(review_states) + requested_reviewers

    add: set[str] = set()
    if changes > 0:
        add.update({"PA: Awaiting Author", "PR: Changes Requested"})
    elif total_reviewers == 0:
        add.add("PA: Second Opinion Needed")
    elif requested_reviewers > 0 and not review_states:
        add.update({"PA: Pending All Reviewers", "PA: Reviewer Assigned"})
    elif requested_reviewers > 0 and approved > 0:
        add.update({"PA: Pending One Reviewer", "PA: Under Review"})
    elif requested_reviewers == 0 and approved > 0:
        add.add("PR: Approved")
    elif review_states:
        add.add("PA: Under Review")

    remove = [label for label in PA_LABELS if label in current and label not in add]
    to_add = sorted(label for label in add if label not in current)
    return to_add, remove


def closed_review_update(current: set[str], merged: bool) -> tuple[list[str], list[str]]:
    """Return ``(to_add, to_remove)`` for the labels of a closed PR."""
    remove = [label for label in PA_LABELS if label in current]
    remove += [label for label in (READY_LABEL, DRAFT_LABEL) if label in current]
    to_add = ["PR: Merged"] if merged else ["PR: Closed Without Merge"]
    return to_add, remove


def _event() -> dict[str, Any]:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _apply(issue, add: list[str], remove: list[str]) -> None:
    for label in remove:
        try:
            issue.remove_from_labels(label)
        except Exception:
            pass
    if add:
        issue.add_to_labels(*add)


def _run_ci() -> int:
    from github import Github

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    payload = _event()
    token = os.environ.get("GH_TOKEN") or os.environ["GITHUB_TOKEN"]
    repo = Github(token).get_repo(os.environ["GITHUB_REPOSITORY"])

    if event_name == "issues":
        if payload.get("action") != "opened":
            print("issue event ignored:", payload.get("action"))
            return 0
        issue = repo.get_issue(payload["issue"]["number"])
        current = {label.name for label in issue.get_labels()}
        if TRIAGE_LABEL not in current:
            issue.add_to_labels(TRIAGE_LABEL)
            print("added", TRIAGE_LABEL)
        return 0

    pr_payload = payload.get("pull_request") or payload.get("review", {}).get("pull_request")
    if not pr_payload:
        print("no pull request in payload; nothing to do")
        return 0

    pull = repo.get_pull(pr_payload["number"])
    issue = repo.get_issue(pull.number)
    current = {label.name for label in issue.get_labels()}

    add: set[str] = set()
    remove: set[str] = set()

    if pull.state == "closed":
        c_add, c_remove = closed_review_update(current, bool(pull.merged))
        add.update(c_add)
        remove.update(c_remove)
    else:
        wanted = content_labels(
            pull.title, pull.draft, [f.filename for f in pull.get_files()]
        )
        exclusive = READY_LABEL if pull.draft else DRAFT_LABEL
        if exclusive in current:
            remove.add(exclusive)
        add.update(label for label in wanted if label not in current)

        states: dict[str, str] = {}
        for review in pull.get_reviews():
            if review.state == "COMMENTED" or review.user is None:
                continue
            states[review.user.login] = review.state
        requested = len(list(pull.get_review_requests()[0])) if not pull.draft else 0
        r_add, r_remove = open_review_update(
            current, pull.draft, list(states.values()), requested
        )
        add.update(r_add)
        remove.update(r_remove)

    remove -= add
    _apply(issue, sorted(add), sorted(remove))
    print("added:", sorted(add) or "none")
    print("removed:", sorted(remove) or "none")
    return 0


def _self_test() -> int:
    ok = True

    def check(label: str, got: Any, expected: Any) -> None:
        nonlocal ok
        if got != expected:
            ok = False
        print(f"  [{'ok' if got == expected else 'FAIL'}] {label}: {got!r}")

    check(
        "feat + perf path -> feature, scope pp, ready",
        content_labels("feat(pp): add reading skill", False,
                       ["parsecore/Rulesets/Osu/Difficulty/Aim.py"]),
        {"Type: Feature", "Scope: PP", "PR: Ready For Review"},
    )
    check(
        "breaking draft + md -> breaking, docs, draft",
        content_labels("fix!: drop legacy path", True, ["README.md"]),
        {"Type: Bug", "Breaking Change", "Type: Docs", "PR: Draft"},
    )
    check(
        "no requested reviewers, no reviews -> second opinion",
        open_review_update(set(), False, [], 0),
        (["PA: Second Opinion Needed"], []),
    )
    check(
        "reviewer requested, no reviews yet -> pending all",
        open_review_update(set(), False, [], 2),
        (["PA: Pending All Reviewers", "PA: Reviewer Assigned"], []),
    )
    check(
        "changes requested -> awaiting author, drops stale pending",
        open_review_update({"PA: Pending All Reviewers"}, False, ["CHANGES_REQUESTED"], 0),
        (["PA: Awaiting Author", "PR: Changes Requested"], ["PA: Pending All Reviewers"]),
    )
    check(
        "draft -> no review labels",
        open_review_update(set(), True, ["APPROVED"], 0),
        ([], []),
    )
    check(
        "merged close -> PR: Merged, clears pending",
        closed_review_update({"PA: Under Review", "PR: Ready For Review"}, True),
        (["PR: Merged"], ["PA: Under Review", "PR: Ready For Review"]),
    )
    check(
        "approved, none requested -> PR: Approved",
        open_review_update(set(), False, ["APPROVED"], 0),
        (["PR: Approved"], []),
    )
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()
    return _run_ci()


if __name__ == "__main__":
    raise SystemExit(main())
