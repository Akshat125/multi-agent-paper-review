# Eval notebook typography & layout

Screen-optimized for Jupyter notebooks. LaTeX handles publication sizing.

## rcParams block

```python
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "figure.dpi": 110,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.alpha": 0.25,
    "grid.color": "#E0E0E0",
    "grid.linestyle": "-",
    "lines.linewidth": 1.5,
    "patch.linewidth": 0.5,
})
```

## Font scale

| Element | Size |
|---------|------|
| Figure title | 11 |
| Axis labels | 10 |
| Tick labels | 9 (8 if crowded) |
| Legend | 8 |
| Bar value annotations | 8 |

## Legend + save (always use both)

Fixed spacing — every legend sits at **`LEGEND_Y = 0.035`** (figure coords).

| Case | `save_fig` bottom |
|------|-------------------|
| No legend | `MARGIN_NO_LEGEND` (0.12) |
| Legend, no rotated x | `MARGIN_LEGEND` (0.22) — return value of `legend_below(..., xrot=0)` |
| Rotated x ≈ 30° | `MARGIN_XROT30` (0.28) |
| Rotated x ≈ 45° | `MARGIN_XROT45` (0.32) |
| Heatmap 90° x | `MARGIN_HEATMAP` (0.28) |

```python
bottom = legend_below(fig, ax, ncol=2, xrot=0)
save_fig(fig, path, bottom=bottom)   # always use bottom= from legend_below
```

Never hardcode `bottom=0.14` etc. Never `tight_layout()` before save.

## One metric → one figure

Do not combine unrelated panels (e.g. tokens + latency) in one PNG.

## Scatter config labels

```python
pad_axes_for_labels(ax)
annotate_configs(ax, df[x_col], df[y_col], df["config"])
save_fig(fig, path, bottom=0.14)   # no legend needed — config slug identifies each point
```

Keep tuple detail in the `display()` table below the cell.

## Annotations

**Bar charts:** value labels outside the bar or error bar; extend `xlim`/`ylim` first.

## Multi-panel

Only when panels share a caption (e.g. human vs model score histograms). Use `save_fig(..., top=0.82)` with `fig.suptitle`.
