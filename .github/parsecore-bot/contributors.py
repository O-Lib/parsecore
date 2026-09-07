# /// script
# requires-python = ">=3.11"
# dependencies = ["PyGithub>=2.4"]
# ///
from __future__ import annotations

import os
import re
import sys
from typing import Any

START = "<!-- contributors:start -->"
END = "<!-- contributors:end -->"
PER_ROW = 7
BRANCH = "bot/contributors"


def render_grid(contributors: list[tuple[str, str, str]], per_row: int = PER_ROW) -> str:
    """Render the contributor avatar grid as an HTML table.

    Args:
        contributors: Tuples of ``(login, avatar_url, profile_url)`` in display order.
        per_row: How many avatars to place per table row.

    Returns:
        The HTML table, or a short placeholder when there are no contributors.
    """
    if not contributors:
        return "<p>No contributors yet.</p>"
    cells = [
        f'<td align="center"><a href="{url}">'
        f'<img src="{avatar}?s=100" width="80" height="80" alt="{login}" />'
        f"<br /><sub><b>{login}</b></sub></a></td>"
        for login, avatar, url in contributors
    ]
    rows = [
        "  <tr>\n    " + "\n    ".join(cells[i:i + per_row]) + "\n  </tr>"
        for i in range(0, len(cells), per_row)
    ]
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def replace_section(readme: str, inner: str) -> str:
    """Replace the text between the contributor markers, keeping the markers."""
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    return pattern.sub(f"{START}\n{inner}\n{END}", readme)


def _run_ci() -> int:
    from github import Github, GithubException

    token = os.environ.get("GH_TOKEN") or os.environ["GITHUB_TOKEN"]
    repo = Github(token).get_repo(os.environ["GITHUB_REPOSITORY"])
    base = repo.default_branch

    people = [
        (c.login, c.avatar_url, c.html_url)
        for c in repo.get_contributors()
        if c.type != "Bot" and "[bot]" not in c.login
    ]
    grid = render_grid(people)

    readme_file = repo.get_contents("README.md", ref=base)
    current = readme_file.decoded_content.decode("utf-8")
    if START not in current:
        print("no contributor markers in README; nothing to do")
        return 0
    updated = replace_section(current, grid)
    if updated == current:
        print("contributors list already up to date")
        return 0

    base_sha = repo.get_branch(base).commit.sha
    ref = f"refs/heads/{BRANCH}"
    try:
        repo.get_git_ref(f"heads/{BRANCH}").edit(base_sha, force=True)
    except GithubException:
        repo.create_git_ref(ref, base_sha)

    branch_file = repo.get_contents("README.md", ref=BRANCH)
    repo.update_file(
        "README.md",
        "docs: update the contributors list",
        updated,
        branch_file.sha,
        branch=BRANCH,
    )

    owner = os.environ["GITHUB_REPOSITORY"].split("/")[0]
    existing = list(repo.get_pulls(state="open", head=f"{owner}:{BRANCH}", base=base))
    if not existing:
        repo.create_pull(
            title="docs: update the contributors list",
            body="Automated refresh of the contributors grid in the README.",
            head=BRANCH,
            base=base,
        )
        print("opened contributors pull request")
    else:
        print("contributors pull request already open; refreshed its branch")
    return 0


def _self_test() -> int:
    ok = True

    def check(label: str, got: Any, expected: Any) -> None:
        nonlocal ok
        if got != expected:
            ok = False
        print(f"  [{'ok' if got == expected else 'FAIL'}] {label}: {got!r}")

    empty = render_grid([])
    check("empty grid placeholder", "No contributors yet" in empty, True)

    grid = render_grid(
        [("octocat", "https://avatars/1", "https://github.com/octocat")], per_row=7
    )
    check("grid links the profile", "https://github.com/octocat" in grid, True)
    check("grid shows the login", "<b>octocat</b>" in grid, True)
    check("grid is emoji-free", any(ord(c) > 0x2600 for c in grid), False)

    readme = f"before\n{START}\nOLD\n{END}\nafter"
    out = replace_section(readme, "NEW")
    check("replaces only between markers", out, f"before\n{START}\nNEW\n{END}\nafter")
    check("keeps surrounding text", out.startswith("before") and out.endswith("after"), True)

    rows = render_grid([(f"u{i}", "a", "https://github.com/u") for i in range(8)], per_row=7)
    check("wraps into two rows", rows.count("<tr>"), 2)
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()
    return _run_ci()


if __name__ == "__main__":
    raise SystemExit(main())
