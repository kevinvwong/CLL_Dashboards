# Data visualization

Every chart color does one job: identity (categorical), magnitude (sequential), polarity (diverging) or state (status). Pick the chart form first; color comes last.

## Choosing a form

| The data's job | Use | Not |
| --- | --- | --- |
| One headline number | StatTile | A chart with one bar |
| Compare categories | BarChart, sorted by value unless categories have an order | Pie with more than 3 slices |
| Change over time | LineChart | Bars for more than 12 periods |
| Part of a whole, 2–3 parts | Stacked bar or a single 100% bar | Donut with a legend |
| Progress to a known total | ProgressBar | Gauge |
| Exact values to look up | DataTable | A chart with a number on every mark |

## Categorical: `chart-1` to `chart-8`

Assign in this order, never cycled, and keep a series' slot when filters remove others:

| Slot | Hue | Lineage | Day | Night |
| --- | --- | --- | --- | --- |
| 1 | Navy blue | GT Bright Blue | #1762b6 | #4087de |
| 2 | Gold | GT Gold | #b2852e | #b78934 |
| 3 | Teal | GT Campanile | #05948b | #25a99b |
| 4 | Ember | New (GT has no orange) | #d8662a | #d8662a |
| 5 | Plum | GT Whistle | #92398f | #a955a5 |
| 6 | Green | GT Tech Lawn | #1c7c48 | #2f965b |
| 7 | Sky | GT Burdell | #299abe | #32a0c5 |
| 8 | Azalea | GT Azalea | #d6286c | #dd4679 |

Validated in both themes: every slot ≥3:1 on `surface`; worst adjacent pair ΔE 11.7 under protanopia and deuteranopia (target 8) and ≥15.3 for full color vision. Scatter plots, maps and small multiples use slots 1–3 only; a 9th series folds into "Other".

The chart slots are tuned versions of the GT hues, not the exact brand values: chart marks need equal visual weight, which the brand accents do not have. Gold drops slightly (#b39051 → #b2852e) to clear 3:1 on white.

## Sequential and diverging

- Magnitude: `seq-blue-1` (low) to `seq-blue-7` (high); a second magnitude in the same view uses `seq-gold-*`. At night the ramp runs dark to bright, so high values still stand out.
- Ordered categories (stages, tiers): day uses steps 4–7, night steps 3–7, so the lightest step still clears 2:1.
- Polarity around a baseline: `div-1` (gold, below) through `div-5` (gray, the baseline) to `div-9` (blue, above). Gold and blue survive every common color-vision deficiency.

## Status in charts

When a series means good or bad (on-time rate, failures), use `chart-status-good`, `chart-status-warning`, `chart-status-critical` with an icon and label, never categorical slots. Never mix status and categorical colors in one chart.

## Marks and chrome

- Bars start at zero, 2px gaps between adjacent bars, 4px rounded data ends. Lines 2px; markers appear on hover.
- Gridlines `chart-grid`, baseline `chart-axis`, tick labels `chart-label` in tabular figures. Text never wears a series color.
- One y-axis. Two measures with different units are two charts.
- Two or more series show a Legend; up to four lines also get direct end labels.
- Every chart has a hover tooltip, a title that names the measure, a subtitle with scope and units, a source footnote, and a table view (ChartCard's `table`).
