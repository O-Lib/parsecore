<div align="center">

## Security Policy

**Found a vulnerability? Thank you for telling us privately first.**

</div>

### Supported versions

Security fixes go to the latest stable release. If you are on an older version,
please update before reporting, since the issue may already be resolved.

### Reporting a vulnerability

Please do not open a public GitHub issue for a security vulnerability.

Send a report to [security@olib.dev](mailto:security@olib.dev) with the subject
line:

```
[parsecore] Security Vulnerability Report
```

Please include:

* The affected versions (`pip show parsecore`).
* Steps to reproduce. For a parser issue, attach the crafted `.osu` file.
* The potential impact (a crash, resource exhaustion, code execution, and so on).
* A suggested fix, if you have one.

### What counts as a security issue

ParseCore parses untrusted `.osu` files: bots and websites feed it maps supplied
by users. Reports that are relevant to security include:

* Crafted beatmap files that cause crashes, hangs, or unbounded memory or CPU
  usage (decompression bombs, pathological object counts, malformed sections).
* Anything that could lead to code execution from file contents.
* Denial of service vectors in the decoding or calculation pipeline.

### Response timeline

* Initial acknowledgement within 48 hours.
* Assessment within five business days.
* A fix released within fourteen business days, depending on severity.

### Disclosure policy

We follow responsible disclosure. Once a fix is publicly available, we publish a
GitHub Security Advisory. Reporters who wish to be credited are named in the
release notes.

<div align="center">

<img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/footers/gray0_ctp_on_line.svg?sanitize=true" />

<code>&copy; 2026 <a href="https://github.com/O-Lib">O!Lib Team</a></code>

</div>
