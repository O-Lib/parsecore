# /// script
# requires-python = ">=3.11"
# dependencies = ["PyGithub>=2.4"]
# ///
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).with_name("config.json")
MARKER = "<!-- parsecore-bot -->"
_STATUS_WORD = {"pass": "Pass", "fail": "Fail", "warn": "Warning", "skip": "Skipped"}


@dataclass
class Result:
    """The outcome of one check."""

    name: str
    status: str
    blocking: bool
    message: str


@dataclass
class ChangedFile:
    """The subset of a PR file the checks need."""

    filename: str
    additions: int
    patch: str | None


def _title_check(cfg: dict, title: str) -> Result:
    ok = re.match(cfg["pattern"], title) is not None
    return Result("Conventional title", "pass" if ok else "fail", cfg["blocking"],
                  cfg["pass"] if ok else cfg["fail"])


def _template_check(cfg: dict, body: str) -> Result:
    problems = []
    summary = re.search(r"## Summary([\s\S]*?)(\n#|\n---|$)", body)
    text = re.sub(r"<!--[\s\S]*?-->", "", summary.group(1) if summary else "")
    if len(text.replace("Closes #", "").strip()) < 10:
        problems.append("summary missing")
    if not re.search(r"- \[x\]", body, re.IGNORECASE):
        problems.append("no Type of Change ticked")
    ok = not problems
    message = cfg["pass"] if ok else f"{cfg['fail']} ({', '.join(problems)})"
    return Result("PR template", "pass" if ok else "fail", cfg["blocking"], message)


def _parity_check(cfg: dict, body: str, files: list[ChangedFile]) -> Result:
    # Anything under these can change a computed value: the rulesets do the
    # arithmetic, and the beatmap layer decides what they are handed.
    touches_perf = any(
        f.filename.endswith(".py")
        and (
            f.filename.startswith("parsecore/Rulesets/")
            or f.filename.startswith("parsecore/Beatmaps/")
            or f.filename.startswith("parsecore/Utils/")
        )
        for f in files
    )
    if not touches_perf:
        return Result("Accuracy statement", "skip", False, cfg["skip"])
    section = re.search(r"### Accuracy([\s\S]*?)(\n#|\n---|$)", body)
    text = re.sub(r"<!--[\s\S]*?-->", "", section.group(1) if section else "").strip()
    ok = len(text) > 5 and re.fullmatch(r"N/?A\.?", text, re.IGNORECASE) is None
    return Result("Accuracy statement", "pass" if ok else "fail", cfg["blocking"],
                  cfg["pass"] if ok else cfg["fail"])


_PUBLIC_SYMBOL = re.compile(r"^\+\s*(?:async\s+)?(?:def|class)\s+([A-Za-z]\w*)")


def _is_public_api(filename: str) -> bool:
    return (
        filename.startswith("parsecore/")
        and filename.endswith(".py")
        and "generated_mods" not in filename
        and "__init__" not in filename
        and "_patches" not in filename
    )


def _adds_public_symbol(patch: str | None) -> bool:
    if not patch:
        return False
    for line in patch.split("\n"):
        match = _PUBLIC_SYMBOL.match(line)
        if match and not match.group(1).startswith("_"):
            return True
    return False


def _docs_check(cfg: dict, files: list[ChangedFile]) -> Result:
    touches_api = any(
        _is_public_api(f.filename) and _adds_public_symbol(f.patch) for f in files
    )
    if not touches_api:
        return Result("Docs update", "skip", False, cfg["skip"])
    has_docs = any(
        f.filename.startswith("docs/")
        or f.filename == "README.md"
        or f.filename.endswith(".md")
        for f in files
    )
    return Result("Docs update", "pass" if has_docs else "warn", False,
                  cfg["pass"] if has_docs else cfg["fail"])


def _comment_check(cfg: dict, body: str, files: list[ChangedFile]) -> Result:
    if cfg["skip_marker"] in body:
        return Result("Comment-free code", "skip", False,
                      f"Skipped via `{cfg['skip_marker']}`.")
    offenders = []
    for f in files:
        if not (f.filename.startswith("parsecore/") and f.filename.endswith(".py") and f.patch):
            continue
        if any(re.match(r"^\+\s*#", line) for line in f.patch.split("\n")):
            offenders.append(f.filename)
    ok = not offenders
    if ok:
        message = cfg["pass"]
    else:
        listed = ", ".join(f"`{name}`" for name in sorted(set(offenders)))
        message = f"{cfg['fail']} Files: {listed}"
    return Result("Comment-free code", "pass" if ok else "fail", cfg["blocking"], message)


def _size_check(cfg: dict, files: list[ChangedFile]) -> Result:
    added = sum(f.additions for f in files)
    limit = cfg["warn_added_lines"]
    ok = added <= limit
    message = (f"{cfg['pass']} (+{added} lines)" if ok
               else cfg["fail"].replace("{limit}", str(limit)) + f" (+{added} lines)")
    return Result("PR size", "pass" if ok else "warn", False, message)


def run_checks(cfg: dict, title: str, body: str, files: list[ChangedFile]) -> list[Result]:
    """Run every enabled check and return the results, in display order."""
    checks = cfg["checks"]
    results: list[Result] = []
    if checks["title"]["enabled"]:
        results.append(_title_check(checks["title"], title))
    if checks["template"]["enabled"]:
        results.append(_template_check(checks["template"], body))
    if checks["parity"]["enabled"]:
        results.append(_parity_check(checks["parity"], body, files))
    if checks["docs"]["enabled"]:
        results.append(_docs_check(checks["docs"], files))
    if checks["comment_policy"]["enabled"]:
        results.append(_comment_check(checks["comment_policy"], body, files))
    if checks["size"]["enabled"]:
        results.append(_size_check(checks["size"], files))
    return results


def verdict(results: list[Result]) -> str:
    """``fail`` if a blocking check failed, ``warn`` if any remark, else ``pass``."""
    if any(r.status == "fail" and r.blocking for r in results):
        return "fail"
    if any(r.status == "warn" or (r.status == "fail" and not r.blocking) for r in results):
        return "warn"
    return "pass"


def render_comment(cfg: dict, results: list[Result]) -> str:
    """Build the sticky review comment. Plain, professional, no emoji."""
    tpl = cfg["templates"]
    outcome = verdict(results)
    verdict_text = {"fail": tpl["verdict_fail"], "warn": tpl["verdict_warn"],
                    "pass": tpl["verdict_pass"]}[outcome]

    rows = "\n".join(
        f"| {r.name} | {_STATUS_WORD[r.status]} | {r.message.split(chr(10))[0]} |"
        for r in results
    )
    fixes = [r for r in results if r.status == "fail"]
    fix_block = ""
    if fixes:
        items = "\n".join(f"- **{r.name}** {r.message}" for r in fixes)
        fix_block = f"\n\n### Required fixes\n\n{items}"

    return "\n".join([
        MARKER,
        tpl["header"].replace("{bot_name}", cfg["bot_name"]),
        "",
        verdict_text,
        "",
        "| Check | Result | Notes |",
        "|---|---|---|",
        rows,
        fix_block,
        tpl["footer"],
    ])


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def _run_ci(cfg: dict) -> int:
    from github import Github

    token = os.environ.get("GH_TOKEN") or os.environ["GITHUB_TOKEN"]
    repo = Github(token).get_repo(os.environ["GITHUB_REPOSITORY"])
    pull = repo.get_pull(int(os.environ["PR_NUMBER"]))
    files = [
        ChangedFile(f.filename, f.additions or 0, f.patch)
        for f in pull.get_files()
    ]
    results = run_checks(cfg, pull.title, pull.body or "", files)
    comment = render_comment(cfg, results)

    mine = next(
        (c for c in pull.get_issue_comments()
         if c.user and c.user.type == "Bot" and MARKER in (c.body or "")),
        None,
    )
    if mine is not None:
        mine.edit(comment)
    else:
        pull.create_issue_comment(comment)

    for r in results:
        print(f"{_STATUS_WORD[r.status]:8} {r.name}")
    if verdict(results) == "fail":
        print("blocking checks failed", file=sys.stderr)
        return 1
    return 0


def _self_test(cfg: dict) -> int:
    ok = True

    def check(label: str, got: Any, expected: Any) -> None:
        nonlocal ok
        if got != expected:
            ok = False
        print(f"  [{'ok' if got == expected else 'FAIL'}] {label}: {got!r}")

    # A change that cannot move a number needs no parity statement.
    good = run_checks(cfg, "docs(readme): document the beatmap encoder",
                      "## Summary\nA real, sufficiently long summary.\n\n- [x] Documentation",
                      [ChangedFile("README.md", 10, "+text")])
    check("clean PR verdict", verdict(good), "pass")

    bad_title = run_checks(cfg, "made something better",
                           "## Summary\nLong enough summary here.\n- [x] fix", [])
    check("bad title -> fail", verdict(bad_title), "fail")

    no_accuracy_note = run_checks(
        cfg, "fix(pp): x", "## Summary\nLong enough summary here.\n- [x] fix\n### Accuracy\nN/A",
        [ChangedFile("parsecore/Rulesets/Osu/Difficulty/Aim.py", 5, "+x")],
    )
    accuracy = next(r for r in no_accuracy_note if r.name == "Accuracy statement")
    check("calculation without accuracy note -> fail", accuracy.status, "fail")

    # The comment policy is off: the port relies on comments to mark every
    # precision and ordering quirk, so a new one is not a defect.
    commented = run_checks(
        cfg, "fix(pp): x", "## Summary\nLong enough summary here.\n- [x] fix\n### Accuracy\nChecked against the game over 34 beatmaps",
        [ChangedFile("parsecore/Rulesets/Osu/Difficulty/Aim.py", 5, "+# a comment")],
    )
    check("added # comment -> no complaint", verdict(commented), "pass")

    with_accuracy_note = run_checks(
        cfg, "fix(beatmap): x",
        "## Summary\nLong enough summary here.\n- [x] fix\n### Accuracy\nChecked against the game over 34 beatmaps",
        [ChangedFile("parsecore/Beatmaps/Formats/LegacyBeatmapDecoder.py", 5, "+x")],
    )
    accuracy_ok = next(r for r in with_accuracy_note if r.name == "Accuracy statement")
    check("decoder change with accuracy note -> pass", accuracy_ok.status, "pass")

    new_api = run_checks(
        cfg, "feat(pp): add public helper",
        "## Summary\nLong enough summary here.\n- [x] feat\n### Accuracy\nChecked against the game over 34 beatmaps",
        [ChangedFile("parsecore/Rulesets/Osu/Difficulty/Aim.py", 5, "+def new_helper():")],
    )
    docs_res = next(r for r in new_api if r.name == "Docs update")
    check("new public symbol without docs -> warn (non-blocking)",
          (docs_res.status, docs_res.blocking, verdict(new_api)), ("warn", False, "warn"))

    internal = run_checks(
        cfg, "refactor(pp): tidy internals",
        "## Summary\nLong enough summary here.\n- [x] refactor\n### Accuracy\nChecked against the game over 34 beatmaps",
        [ChangedFile("parsecore/Rulesets/Osu/Difficulty/Aim.py", 5, "+    x = 1")],
    )
    internal_docs = next(r for r in internal if r.name == "Docs update")
    check("internal-only change -> docs skip", internal_docs.status, "skip")

    big = run_checks(cfg, "fix(pp): x", "## Summary\nLong enough summary here.\n- [x] fix",
                     [ChangedFile("parsecore/x.py", 5000, None)])
    size_res = next(r for r in big if r.name == "PR size")
    check("oversized PR -> warn (non-blocking)", (size_res.status, verdict(big)), ("warn", "warn"))

    text = render_comment(cfg, bad_title)
    has_emoji = any(ord(ch) > 0x2600 for ch in text)
    check("comment is emoji-free", has_emoji, False)
    return 0 if ok else 1


def main() -> int:
    cfg = _load_config()
    if "--self-test" in sys.argv:
        return _self_test(cfg)
    return _run_ci(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
