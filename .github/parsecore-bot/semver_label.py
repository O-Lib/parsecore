# /// script
# requires-python = ">=3.11"
# dependencies = ["PyGithub>=2.4"]
# ///
from __future__ import annotations

import os
import re
import sys

MAJOR_LABEL = "Semver: Major"
TYPE_TO_LABEL = {
    "feat": "Semver: Minor",
    "fix": "Semver: Patch",
    "perf": "Semver: Patch",
}
ALL_SEMVER_LABELS = {MAJOR_LABEL, *TYPE_TO_LABEL.values()}


_TITLE = re.compile(r"^(?P<type>[a-z]+)(?:\([^)]*\))?(?P<bang>!)?:\s")


def semver_label_for(title: str, body: str = "") -> str | None:
    """Return the semver label a PR should carry, or ``None`` for no label.

    Args:
        title: The pull request title.
        body: The pull request body, checked for a ``BREAKING CHANGE`` footer.
    """
    match = _TITLE.match(title.strip())
    if match is None:
        return None
    if match.group("bang") or "BREAKING CHANGE" in f"{title}\n{body}":
        return MAJOR_LABEL
    return TYPE_TO_LABEL.get(match.group("type"))


def reconcile(current: set[str], target: str | None) -> tuple[list[str], list[str]]:
    """Return ``(to_add, to_remove)`` to make the semver labels match ``target``.

    Only the three ``Semver: *`` labels are ever touched; anything else the PR
    carries is left exactly as it is.
    """
    keep = {target} if target else set()
    to_remove = sorted((current & ALL_SEMVER_LABELS) - keep)
    to_add = [target] if target and target not in current else []
    return to_add, to_remove


def _apply(repo_name: str, pr_number: int, token: str) -> int:
    """Reconcile the PR's semver label to match its title. Returns an exit code."""
    from github import Github

    pull = Github(token).get_repo(repo_name).get_pull(pr_number)
    target = semver_label_for(pull.title, pull.body or "")
    to_add, to_remove = reconcile({label.name for label in pull.labels}, target)

    for name in to_remove:
        pull.remove_from_labels(name)
        print(f"removed {name!r}")
    for name in to_add:
        pull.add_to_labels(name)
        print(f"added {name!r}")
    if not to_add and not to_remove:
        print(f"no change (target: {target!r})")
    return 0


_CASES = [
    ("fix(pp): correct taiko scroll speed", "Semver: Patch"),
    ("feat(mods): add lazer classic", "Semver: Minor"),
    ("feat!: drop python 3.10", "Semver: Major"),
    ("refactor(pp)!: rename Difficulty", "Semver: Major"),
    ("perf: speed up strain calc", "Semver: Patch"),
    ("docs: fix a typo", None),
    ("chore: bump deps", None),
    ("not a conventional title", None),
]


def _self_test() -> int:
    ok = True
    for title, expected in _CASES:
        got = semver_label_for(title)
        flag = "ok" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"  [{flag}] {title!r} -> {got!r} (expected {expected!r})")
    breaking = semver_label_for("fix: x", "body\n\nBREAKING CHANGE: y")
    if breaking != MAJOR_LABEL:
        ok = False
        print(f"  [FAIL] BREAKING CHANGE footer -> {breaking!r}")

    recon_cases = [
        ({"Status: Confirmed"}, "Semver: Minor", (["Semver: Minor"], [])),
        ({"Semver: Patch"}, "Semver: Minor", (["Semver: Minor"], ["Semver: Patch"])),
        ({"Semver: Minor"}, "Semver: Minor", ([], [])),
        ({"Semver: Patch", "bug"}, None, ([], ["Semver: Patch"])),
    ]
    for current, target, expected in recon_cases:
        got = reconcile(set(current), target)
        flag = "ok" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"  [{flag}] reconcile({current}, {target!r}) -> {got}")
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    number = os.environ.get("PR_NUMBER")
    if not (token and repo_name and number):
        print("GH_TOKEN, GITHUB_REPOSITORY and PR_NUMBER are required", file=sys.stderr)
        return 2
    return _apply(repo_name, int(number), token)


if __name__ == "__main__":
    raise SystemExit(main())
