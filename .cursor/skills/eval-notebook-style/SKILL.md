---
name: eval-notebook-style
description: >-
  Style and visual conventions for eval analysis Jupyter notebooks under
  eval/analysis/. Defines seaborn-deep 4-color palette, outside-bottom legends,
  asymmetric titles (pilot tagged only), and setup-cell template. Use when
  creating, editing, or unifying eval analysis notebooks, matplotlib figures,
  or figure exports in eval/analysis/figures/.
---

# Eval Notebook Style

Visual-style skill for `eval/analysis/*.ipynb`. Metric logic stays in each notebook; this skill governs look-and-feel only.

**Manual iteration required** — open each notebook, re-run plot cells, inspect PNGs, tune `subplots_adjust` and axis limits. Scripts cannot judge legend overlap.

## When to apply

- Creating or editing analysis notebooks under `eval/analysis/`
- Fixing legend overlap, clipped text, inconsistent colors, or title noise
- Regenerating figures after results update

## Quick workflow

1. Copy [templates/setup-cell.py](templates/setup-cell.py) into cell 0.
2. Use [palette.md](palette.md) — one quad palette, pick 2/3/4 swatches per figure.
3. Labels via [labels.md](labels.md) — config slugs on plots, A/B/C in legends, tuples in tables only.
4. Titles via `fig_title()` — [titles.md](titles.md).
4. Legends outside bottom — [typography.md](typography.md).
5. Scatter plots: **config slug labels** on points (`annotate_configs`); table below for tuple detail.
6. Run cell → open PNG → adjust `subplots_adjust(bottom=…)` and axis padding → repeat.

## Figure size presets

| Preset | `figsize` | Use |
|--------|-----------|-----|
| `FIG_RANK` | `(8.5, 4.5)` | Config ranking barh |
| `FIG_COMPACT` | `(6, 3.6)` | Small comparisons |
| `FIG_SCATTER` | `(7, 5)` | Scatter |
| `FIG_PANEL` | `(9.5, 3.8)` | 1×2 panels |
| `FIG_WIDE` | `(12, 4.0)` | Heatmaps, wide matrices |

## Titles (summary)

- **Full eval (25 papers):** plain sentence-case title, no run prefix, usually no n.
- **Pilot:** `(pilot, n=5 papers)` suffix.
- **Special n (e.g. diversity, 7 common papers):** `(n=7 papers)` when n ≠ 25.
- LaTeX captions carry judges, SEM, methods — don't force into every title.

See [titles.md](titles.md).

## Color (summary)

One palette — blue, orange, green, red from per-role cost breakdown. Two colors → blue+orange; three → +green; four → full set. One categorical story per axes.

See [palette.md](palette.md).

## Legend (summary)

Default: **below the plot**, `bbox_to_anchor=(0.5, -0.12)`, `fig.subplots_adjust(bottom=0.22)`.

See [typography.md](typography.md).

## Save contract

- Path: `eval/analysis/figures/{RUN_SET}/{metric}_{view}.png`
- `fig.savefig(..., bbox_inches="tight")`

## Anti-patterns

- `f"{RUN_SET}: …"` in titles
- Model names on figures (`qwen3-32b`, `A · qwen…`)
- Tuple suffix on plot labels (`All-A (A,A,A,A)`)
- In-plot `legend(loc="upper right")` over data
- Point labels on dense scatters without `pad_axes_for_labels`
- Legend entries as bare `A` / `B` / `C` — use `f"{letter} · {MODEL_NAMES[letter]}"`
- Fifth hue outside `PALETTE`
- Mixing het/ref and model color on same axes
- Batch regex migration without visual review

## Additional resources

- [palette.md](palette.md)
- [titles.md](titles.md)
- [labels.md](labels.md)
- [typography.md](typography.md)
- [templates/setup-cell.py](templates/setup-cell.py)
