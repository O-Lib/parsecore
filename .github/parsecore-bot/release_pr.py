# /// script
# requires-python = ">=3.11"
# dependencies = ["PyGithub>=2.4"]
# ///
from __future__ import annotations

import datetime as dt
import os
import re
import sys

CHANGELOG_PATH = "docs/about/changelog.md"
PYPROJECT_PATH = "pyproject.toml"

_BUMP_RANK = {"major": 3, "minor": 2, "patch": 1}
_LABEL_BUMP = {
    "Semver: Major": "major",
    "Semver: Minor": "minor",
    "Semver: Patch": "patch",
}

_TYPE_HEADING = {
    "feat": "Features",
    "fix": "Bug fixes",
    "perf": "Performance",
}
_TITLE = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]*)\))?!?:\s*(?P<subject>.+)$")


def bump_from_labels(labels: list[str]) -> str | None:
    """Return the strongest release bump implied by a set of labels, or None."""
    bumps = [_LABEL_BUMP[name] for name in labels if name in _LABEL_BUMP]
    if not bumps:
        return None
    return max(bumps, key=lambda b: _BUMP_RANK[b])


def next_version(current: str, bump: str | None) -> str | None:
    """Apply a semver bump to ``major.minor.patch``. None bump -> None."""
    if bump is None:
        return None
    major, minor, patch = (int(part) for part in current.split("."))
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def changelog_section(version: str, date: str, titles: list[str]) -> str:
    """Render one changelog section, grouping PR titles by Conventional type."""
    groups: dict[str, list[str]] = {}
    for title in titles:
        match = _TITLE.match(title.strip())
        if match is None:
            continue
        heading = _TYPE_HEADING.get(match.group("type"))
        if heading is None:
            continue
        scope = match.group("scope")
        subject = match.group("subject").strip()
        prefix = f"**{scope}:** " if scope else ""
        groups.setdefault(heading, []).append(f"- {prefix}{subject}")

    lines = [f"## {version} - {date}", ""]
    for heading in ("Features", "Bug fixes", "Performance"):
        if heading in groups:
            lines.append(f"### {heading}")
            lines.extend(groups[heading])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _read_current_version(text: str) -> str:
    match = re.search(r'(?m)^version\s*=\s*"(\d+\.\d+\.\d+)"', text)
    if match is None:
        raise ValueError("no version = \"x.y.z\" found in pyproject.toml")
    return match.group(1)


def _run_ci() -> int:
    """Compute the release and open/update its PR. Returns an exit code."""
    from github import Github, GithubException

    token = os.environ.get("GH_TOKEN") or os.environ["GITHUB_TOKEN"]
    repo = Github(token).get_repo(os.environ["GITHUB_REPOSITORY"])
    default_branch = repo.default_branch

    tags = list(repo.get_tags())
    since = tags[0].commit.commit.author.date if tags else None
    merged: list = []
    for pull in repo.get_pulls(state="closed", base=default_branch, sort="updated", direction="desc"):
        if pull.merged_at is None:
            continue
        if since is not None and pull.merged_at <= since:
            break
        merged.append(pull)

    labels = [name for pull in merged for name in (label.name for label in pull.labels)]
    bump = bump_from_labels(labels)
    if bump is None:
        print("nothing releasable merged since the last tag")
        return 0

    pyproject = repo.get_contents(PYPROJECT_PATH, ref=default_branch)
    current = _read_current_version(pyproject.decoded_content.decode())
    version = next_version(current, bump)
    print(f"{len(merged)} merged PR(s), bump={bump}: {current} -> {version}")

    branch = f"release/v{version}"
    head_sha = repo.get_branch(default_branch).commit.sha
    try:
        repo.create_git_ref(f"refs/heads/{branch}", head_sha)
    except GithubException:
        repo.get_git_ref(f"heads/{branch}").edit(head_sha, force=True)

    new_pyproject = re.sub(
        r'(?m)^(version\s*=\s*)"\d+\.\d+\.\d+"', rf'\g<1>"{version}"',
        pyproject.decoded_content.decode(), count=1,
    )
    _put(repo, PYPROJECT_PATH, new_pyproject, branch, f"chore: bump version to {version}")

    today = dt.date.today().isoformat()
    section = changelog_section(version, today, [pull.title for pull in merged])
    try:
        existing = repo.get_contents(CHANGELOG_PATH, ref=branch)
        body = existing.decoded_content.decode()
    except GithubException:
        body = "# Changelog\n\n"
    if body.lstrip().startswith("# "):
        head, _, rest = body.partition("\n")
        merged_body = f"{head}\n\n{section}\n{rest.lstrip()}"
    else:
        merged_body = f"# Changelog\n\n{section}\n{body}"
    _put(repo, CHANGELOG_PATH, merged_body, branch, f"docs: changelog for {version}")

    title = f"release: v{version}"
    pr_body = f"Automated release PR.\n\n{section}"
    existing_pr = list(repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch}"))
    if existing_pr:
        existing_pr[0].edit(title=title, body=pr_body)
        print(f"updated {existing_pr[0].html_url}")
    else:
        pr = repo.create_pull(title=title, body=pr_body, base=default_branch, head=branch)
        pr.add_to_labels(_label_for(bump))
        print(f"opened {pr.html_url}")
    return 0


def _label_for(bump: str) -> str:
    return {"major": "Semver: Major", "minor": "Semver: Minor", "patch": "Semver: Patch"}[bump]


def _put(repo, path: str, content: str, branch: str, message: str) -> None:
    from github import GithubException

    try:
        current = repo.get_contents(path, ref=branch)
        repo.update_file(path, message, content, current.sha, branch=branch)
    except GithubException:
        repo.create_file(path, message, content, branch=branch)


_SELF_TEST = [
    (["Semver: Patch", "Semver: Minor"], "minor"),
    (["Semver: Major", "Semver: Patch"], "major"),
    (["Status: Confirmed"], None),
    ([], None),
]


def _self_test() -> int:
    ok = True

    def check(label, got, expected):
        nonlocal ok
        if got != expected:
            ok = False
        print(f"  [{'ok' if got == expected else 'FAIL'}] {label}: {got!r}")

    for labels, expected in _SELF_TEST:
        check(f"bump_from_labels({labels})", bump_from_labels(labels), expected)
    check("next_version 1.2.3 minor", next_version("1.2.3", "minor"), "1.3.0")
    check("next_version 1.2.3 major", next_version("1.2.3", "major"), "2.0.0")
    check("next_version 1.2.3 patch", next_version("1.2.3", "patch"), "1.2.4")
    check("next_version none", next_version("1.2.3", None), None)

    section = changelog_section(
        "1.3.0", "2026-01-01",
        ["feat(pp): add reading skill", "fix: taiko combo", "docs: tidy", "chore: deps"],
    )
    expect = (
        "## 1.3.0 - 2026-01-01\n\n"
        "### Features\n- **pp:** add reading skill\n\n"
        "### Bug fixes\n- taiko combo\n"
    )
    check("changelog_section", section, expect)
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()
    return _run_ci()


if __name__ == "__main__":
    raise SystemExit(main())
