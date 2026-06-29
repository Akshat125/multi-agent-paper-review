# Eval notebook palette

One **seaborn-deep quad** everywhere — the per-role cost breakdown colors. No ad-hoc purple, pink, lavender, or gray-as-data-color.

## Canonical palette

```python
# blue · orange · green · red  (seaborn deep)
PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]

MODEL_COLORS = {"A": PALETTE[0], "B": PALETTE[1], "C": PALETTE[2]}
MODEL_NAMES = {
    "A": "qwen3-32b", "B": "mistral-small-3.2", "C": "llama-3.3-70b",
}
ROLE_COLORS = dict(zip(
    ("leader", "clarity", "experiments", "impact"), PALETTE
))
ROLES = ("leader", "clarity", "experiments", "impact")

# Two-color ranking: heterogeneous vs homogeneous reference
C_HET = PALETTE[0]   # blue — heterogeneous (accent)
C_REF = PALETTE[1]   # orange — homogeneous reference

# Neutrals (non-data)
C_ANNOT = "#333333"
C_MUTED = "#555555"
C_REF_LINE = "#666666"
C_EDGE = "#FFFFFF"
C_ERR = "#333333"
```

## How many colors?

Pick the first *k* swatches from `PALETTE` — never introduce a fifth hue.

| k | Colors | Use |
|---|--------|-----|
| 2 | blue + orange | het vs ref rankings; input vs output; two strata |
| 3 | blue, orange, green | models A/B/C; three strata |
| 4 | full `PALETTE` | roles; four-way breakdowns |

Side-by-side panels may show different *views* but must still draw from `PALETTE`.

## One story per axes

Each axes encodes **one** categorical dimension. Do not mix het/ref coloring with model coloring on the same scatter.

| Claim | Encoding |
|-------|----------|
| Does this config beat references? | `C_REF` / `C_HET` |
| Which model / seat? | `MODEL_COLORS` |
| Which role? | `ROLE_COLORS` |
| Stratum | first k of `PALETTE` in fixed order |

## Swatch

```
blue    ███  #4C72B0   het / model A / leader
orange  ███  #DD8452   ref / model B / clarity
green   ███  #55A868   model C / experiments
red     ███  #C44E52   impact / 4th stratum
```
