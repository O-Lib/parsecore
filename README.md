<div align="center">

![ParseCore](https://i.imgur.com/35asYBQ.jpeg)

**A Python library for osu! beatmaps: parsing, mods, star rating and performance points.**

[![PyPI Version](https://img.shields.io/pypi/v/parsecore?style=for-the-badge&color=pink)](https://pypi.org/project/parsecore/)
[![Python](https://img.shields.io/pypi/pyversions/parsecore?style=for-the-badge&color=blue)](https://pypi.org/project/parsecore/)
[![License](https://img.shields.io/github/license/O-Lib/parsecore?style=for-the-badge&color=green)](LICENSE)
[![Docs](https://img.shields.io/readthedocs/parsecore?style=for-the-badge&logo=readthedocs&logoColor=white&label=docs)](https://parsecore.readthedocs.io)
[![Discord](https://img.shields.io/discord/1499516844711608350?style=for-the-badge&logo=discord&label=discord&color=5865F2)](https://discord.gg/9p7whE7QxQ)

</div>

### Overview

ParseCore reads `.osu` beatmaps, writes them back out, and computes star
ratings and performance points for all four game modes osu!, taiko, catch and
mania including converts and the full mod system.

The values it produces are **bit for bit identical** to the ones the game
awards. Not close, not rounded to five decimals: identical, down to the last
bit of the last double. That guarantee is the whole product, and everything
below exists to keep it.

### Features

* **Beatmap parsing.** Every section of the `.osu` format: General, Editor,
  Metadata, Difficulty, Events, Timing Points and Hit Objects, with the control
  point model the format really uses.
* **Beatmap writing.** A decoded beatmap goes back out as `.osu` text, byte for
  byte.
* **All four game modes,** natively and as converts, including the legacy mania
  pattern generator and key mods from 1K to 10K.
* **Star rating and pp,** with the full attribute breakdown: aim, speed,
  reading, flashlight, slider factors, strain counts.
* **Both scoring eras.** Modern scores with slider tail statistics, and scores
  from the classic client, where the recorded total is read back for the combo
  breaks it hides.
* **No runtime dependencies.** Pure Python, standard library only.

### Accuracy

Star rating and pp look like simple arithmetic and are not. Much of the
geometry runs in single precision, narrowing at every step rather than at the
end, and the game carries a long tail of behaviour that a clean-room rewrite
would quietly get wrong. ParseCore reproduces it deliberately:

```python
# The catcher is drawn at twice an object's scale, not the same.
scale = f32(CalculateScaleFromCircleSize(circle_size) * 2)

# Two whole millisecond counts less a single-precision grace period, worked
# out at single precision before it widens.
time_to_next = f32(int(a.StartTime) - int(b.StartTime) - HYPER_DASH_GRACE)

# The classic client ran this on 80-bit registers. A double rounds the other
# way on a good number of ranked beatmaps, so this uses a decimal.
CalculateDifficultyPeppyStars(difficulty, object_count, drain_length)
```

Whole-number exponents multiply out instead of calling `pow`. Integer
divisions throw their remainder away. Rounding goes to the nearest even
number. Chords are ordered by an unstable sort, because the order decides the
result. Each of these is marked where it sits, so the next reader knows it is
load-bearing rather than clumsy.

### Verification

Every number is checked against reference values taken from the game itself,
over 34 beatmaps covering all four modes, converts, and mod combinations.

| Area | Cases | Result |
|---|---|---|
| osu! difficulty attributes | 34 | bit-exact |
| osu! attributes across 9 mod sets | 306 | bit-exact |
| taiko conversion, preprocessing, skills | 102 | bit-exact |
| taiko attributes and pp | 340 | bit-exact |
| catch objects, star rating, pp | 306 | bit-exact |
| mania conversion, columns, star rating, pp | 306 | bit-exact |
| mania hit windows | 576 | bit-exact |
| classic score simulation | 136 | bit-exact |
| classic pp with combo breaks | 1190 | bit-exact |
| `.osu` writer output | 34 | character-identical |

Roughly 3300 verified cases, plus 345 unit tests.

### Installation

```bash
pip install parsecore
```

With [uv](https://github.com/astral-sh/uv):

```bash
uv add parsecore
```

Requires Python 3.11 or newer.

### Usage

A beatmap is decoded once, then converted for whichever mode you want to rate
it as, then rated.

### Reading a beatmap

```python
from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder

beatmap = LegacyBeatmapDecoder.FromPath("map.osu")

print(beatmap.Metadata.Title, "-", beatmap.BeatmapInfo.DifficultyName)
print(beatmap.Difficulty.ApproachRate, beatmap.Difficulty.CircleSize)

for hit_object in beatmap.HitObjects[:5]:
    print(type(hit_object).__name__, hit_object.StartTime)
```

### Star rating and pp

```python
from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Mods.ModDoubleTime import ModDoubleTime
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Difficulty.OsuDifficultyCalculator import (
    OsuDifficultyCalculator,
)
from parsecore.Rulesets.Osu.Difficulty.OsuPerformanceCalculator import (
    OsuPerformanceCalculator,
)
from parsecore.Rulesets.Osu.Mods.OsuModHidden import OsuModHidden
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Scoring.ScoreInfo import ScoreInfo

decoded = LegacyBeatmapDecoder.FromPath("map.osu")
mods = [OsuModHidden(), ModDoubleTime()]

playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
    OsuBeatmapConverter, OsuBeatmapProcessor, mods
)
attributes = OsuDifficultyCalculator(playable, decoded).Calculate(mods)

print(attributes.StarRating) # 10.201730601358229
print(attributes.MaxCombo) # 703

score = ScoreInfo(
    Mods=mods,
    BeatmapDifficulty=decoded.Difficulty,
    MaxCombo=attributes.MaxCombo,
    Accuracy=1.0,
    Statistics={
        HitResult.Great: attributes.HitCircleCount
        + attributes.SliderCount
        + attributes.SpinnerCount,
        HitResult.SliderTailHit: attributes.SliderCount,
    },
)
performance = OsuPerformanceCalculator().Calculate(score, attributes)

print(performance.Total, performance.Aim, performance.Speed, performance.Accuracy)
```

Swap `Osu` for `Taiko`, `Catch` or `Mania` to rate the same beatmap as a
convert. Mania takes no processor and works its column count out for itself:

```python
from parsecore.Rulesets.Mania.Beatmaps.ManiaBeatmapConverter import (
    ManiaBeatmapConverter,
)
from parsecore.Rulesets.Mania.Difficulty.ManiaDifficultyCalculator import (
    ManiaDifficultyCalculator,
)
from parsecore.Rulesets.Mania.Mods.ManiaKeyMod import ManiaModKey4

mods = [ManiaModKey4()]
playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
    ManiaBeatmapConverter, None, mods
)

print(playable.TotalColumns) # 4
print(ManiaDifficultyCalculator(playable).Calculate(mods).StarRating)
```

### Writing a beatmap back out

```python
from parsecore.Beatmaps.Formats.LegacyBeatmapEncoder import LegacyBeatmapEncoder

text = LegacyBeatmapEncoder(decoded).EncodeToString()

with open("out.osu", "w", encoding="utf-8", newline="") as file:
    file.write(text)
```

### Reading a classic score

A score from the classic client records a total but never says where the combo
broke, and a slider break costs combo without leaving a miss behind. Give
ParseCore the total and it works the breaks out:

```python
from parsecore.Rulesets.Osu.Mods.OsuModClassic import OsuModClassic

score = ScoreInfo(
    Mods=[OsuModClassic()],
    BeatmapDifficulty=decoded.Difficulty,
    MaxCombo=219,
    Accuracy=0.9948453608247423,
    LegacyTotalScore=884865,
    Statistics={HitResult.Great: 193, HitResult.Miss: 1},
)
```

### Scope

ParseCore answers what a beatmap and a score are worth. Gameplay, rendering,
skinning, editing, storyboards and anything online are out of scope: none of
them change a number.

### Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md)
first; it explains the one rule that matters here, which is that a change must
not move a value the library already gets right. To report a security issue,
see [SECURITY.md](SECURITY.md).

### Documentation

Guides and the API reference live at
[parsecore.readthedocs.io](https://parsecore.readthedocs.io).

### Translations

The documentation is translated by the community on
[Crowdin](https://crowdin.com/project/parsecore) (English is the source;
German, French, Luxembourgish, and Portuguese are in progress). No coding is
required to help.

### Licence

MIT. See [LICENSE](LICENSE).

Beatmaps under `beatmaps/` belong to their respective mappers and are included
only so the test suite has something real to check against.

### Contributors

Thanks to everyone who has contributed to ParseCore. This list is maintained
automatically by the ParseCore Bot.

<!-- contributors:start -->
<!-- contributors:end -->

<div align="center">

<img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/footers/gray0_ctp_on_line.svg?sanitize=true" />

<code>&copy; 2026 <a href="https://github.com/O-Lib">O!Lib Team</a></code>

</div>
