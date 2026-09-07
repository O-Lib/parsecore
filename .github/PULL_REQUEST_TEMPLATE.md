### Summary

<!-- What does this pull request do? Keep it short. -->

Closes #<!-- issue number -->

---

### Type of change

- [ ] Bug fix
- [ ] New functionality
- [ ] Algorithm update (the game changed how something is rated)
- [ ] Performance improvement
- [ ] Documentation
- [ ] Tests
- [ ] Chore / tooling / CI

---

### Changes

<!-- A short list of what changed, and why. -->

-

---

### Accuracy

<!--
Fill this in for anything that can change a computed value. Write N/A only if
the change cannot possibly move a number.
-->

**Values affected:** <!-- none, or: catch star rating on beatmaps with hyper-dashes -->

**How you checked it:**

<!--
Say what you compared and over how many cases. "The existing tests pass" is not
enough on its own: those tests pin values that were taken from the game in the
first place, so a wrong change to both would still look green.
-->

---

### Testing

```bash
pytest -q
ruff check parsecore/ tests/
```

<!-- Paste anything worth seeing, such as a before-and-after value. -->

---

### Breaking changes

<!-- If this breaks an existing API, describe the migration path. -->

N/A

---

### Checklist

- [ ] No value the library already gets right has moved, or the change is the point and is evidenced above
- [ ] Precision and ordering details left intact (`f32` narrowing, whole-number exponents, integer division, draw order)
- [ ] Tests added or updated
- [ ] `pytest` and `ruff check` are clean
- [ ] Documentation updated where it says something different now
