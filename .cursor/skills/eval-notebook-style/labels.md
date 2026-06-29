# Eval figure labels

The paper defines what **A / B / C** and config slugs (`All-A`, `specialist`, …) mean. Figures use tags only — no model names, no tuples on plots.

## On the figure

| Element | Format | Example |
|---------|--------|---------|
| Config identity | **slug only** | `specialist`, `All-A`, `rot_2` |
| Model in legend | **letter only** | `A`, `B`, `C` |
| Role in legend | role name | `leader`, `clarity`, … |
| Homo/het | short words | `homogeneous`, `heterogeneous` |

**Never on figures:** `qwen3-32b`, `A · qwen3-32b`, `A=qwen…`, `specialist (A,B,A,C)`, `All-A (A,A,A,A)`.

## Below the cell (table)

Full detail: `config`, `tuple`, metrics — via `display(df[[...]])`.

## Scatter

```python
annotate_configs(ax, df[x], df[y], df["config"])
save_fig(fig, path, bottom=MARGIN_NO_LEGEND)
```

## Barh y-axis

```python
ax.set_yticklabels(d["config"], fontsize=8)
```

## Model-colour legend

```python
label="A"   # not MODEL_NAMES["A"]
```
