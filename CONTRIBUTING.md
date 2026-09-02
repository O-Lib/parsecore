<div align="center">

## Contributing to ParseCore

**Thank you for taking the time to contribute.**

</div>

### Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating,
you agree to uphold it. Report unacceptable behaviour to
[conduct@olib.dev](mailto:conduct@olib.dev).

### The one rule that matters

ParseCore's star ratings and pp values are identical, to the last bit, to the
ones the game awards. That guarantee is the whole product, and every change has
to preserve it.

Two things follow from it.

**Do not tidy the arithmetic.** A great deal of what looks clumsy is
load-bearing, and rewriting it changes the answer:

* `f32(...)` calls are not decoration. Much of the geometry runs in single
  precision and narrows at every step, so each call marks exactly where a value
  stops being a double. Removing one drifts every result downstream of it.
* `DiffUtils.Pow(x, 3)` with a whole-number exponent multiplies out rather than
  calling `pow`. `x ** 3` is a different number.
* Integer divisions throw their remainder away, rounding goes to the nearest
  even number, and chords are ordered by an unstable sort. All three are
  deliberate, and all three are commented where they sit.
* The order values are drawn from `LegacyRandom` is fixed. Draw one too many or
  one too few and every note after it moves.

If a formula reads badly to you, assume it is deliberate until you have checked.

**Prove a change against the game, not against the previous answer.** Anything
that touches a calculation has to be verified against the values the game
itself awards, and the pull request should say how. "The tests still pass" is
not the same claim: the test suite pins values that were themselves taken from
the game, so a wrong change to both would look green.

### What we accept

* **Bug fixes**, including a value that has drifted.
* **Algorithm updates** when the game changes how something is rated, with
  evidence.
* **New functionality** within the library's scope.
* **Documentation**, examples, typos.
* **Tests**, especially awkward beatmaps and edge cases.
* **Performance work**, as long as every value stays identical.
* **Tooling and CI.**

### What we do not accept

* Anything that changes a computed value the library already gets right.
* Breaking API changes without prior discussion. Open an issue.
* New runtime dependencies. The library deliberately has none.
* Anything intended to help with cheating or score manipulation.

### Reporting a wrong value

This is the report we care most about, so please make it precise:

* The beatmap, by ID or attached `.osu` file.
* The game mode and the exact mods.
* What ParseCore returned and what the game awards.
* The ParseCore version, the Python version, and the operating system.

Compare against the game itself rather than against a third-party calculator,
which often lags behind a rework.

### Reporting anything else

1. Check the latest version; your problem may already be fixed.
2. Search the existing issues.
3. Reduce it to the smallest snippet that still shows the problem.

Include what you expected, what happened, and the full traceback if there is
one.

### Development setup

You need Python 3.11 or newer and, ideally,
[`uv`](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/O-Lib/parsecore.git
cd parsecore

uv sync
# or, with pip:
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Check your work:

```bash
pytest -q
ruff check parsecore/ tests/
```

The test suite reads the beatmaps under `beatmaps/`, so it needs no network and
no game installation.

### How the code is laid out

The library is organised by what a value depends on rather than by what a
caller wants:

```
parsecore/
  Audio/       hit samples
  Beatmaps/    decoding, encoding, control points, the conversion pipeline
  Rulesets/    the objects, conversion, skills and pp of each game mode,
               over a shared base of objects, mods, skills and scoring
  Scoring/     a score as it is handed to a performance calculator
  Utils/       single precision, the classic generator, vectors
```

A new file belongs with the layer whose data it works on. Anything that reads a
beatmap before it belongs to a mode goes under `Beatmaps/` or
`Rulesets/Objects/`; anything that is true only for one mode goes under that
mode.

### Coding standards

We follow PEP 8, with these points:

* Line length 88, four-space indentation.
* Types and their members use `PascalCase` names, matching the vocabulary the
  `.osu` format and the game itself use (`StarRating`, `ApplyToBeatmap`), so
  that a reader can move between a beatmap file and the code without
  translating. Local variables and private helpers are `snake_case`.
* Every module, class, function and method carries a Google-style docstring: a
  summary line, then `Args:`, `Returns:` and `Raises:` where they say something.

Comments earn their place by explaining a decision the code cannot. Most of
them here mark a precision or ordering quirk:

```python
# Two whole millisecond counts less a single-precision grace period,
# which is worked out at single precision before it widens.
time_to_next = f32(
    int(following.StartTime) - int(current.StartTime) - HYPER_DASH_GRACE
)
```

A comment restating the line below it does not.

### Pull requests

1. Open an issue first for anything non-trivial.
2. Branch from `main`.
3. Add or update tests.
4. Make sure `pytest` and `ruff check` are clean.
5. Say in the description how you checked that no value moved.

### Commit guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.

Scopes: `beatmap`, `osu`, `taiko`, `catch`, `mania`, `mods`, `pp`, `scoring`,
`readme`, `docs`, `ci`, `packaging`.

Examples:

```
feat(mania): add the legacy pattern generators
fix(catch): work the hyper-dash grace period out at single precision
fix(beatmap): apply sample control points to hit objects when decoding
docs(readme): document the beatmap writer
chore(ci): run the test suite on Python 3.13
```

### Review process

* A first review lands within five business days.
* Follow-up reviews land within two or three.

Reviewers check the values first, then correctness, tests, and style.

<div align="center">

<img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/footers/gray0_ctp_on_line.svg?sanitize=true" />

<code>&copy; 2026 <a href="https://github.com/O-Lib">O!Lib Team</a></code>

</div>
