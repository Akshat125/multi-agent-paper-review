# Figure titles

Notebook titles are **working labels** for PNG exports. LaTeX figure captions carry run scope, judges, and methods — do not force everything into `set_title`.

## Rules

1. **Sentence case** — `Comment recall by config`, not Title Case.
2. **No run-set prefix** for the 25-paper eval (`RUN_SET == "full"`). Never `full:`, `Main ·`, etc.
3. **Pilot only** — when `RUN_SET == "pilot"`, append `(pilot, …)` in parentheses.
4. **Sample size** — include `n=` only when it helps:
   - always for pilot (with the pilot tag)
   - for full when **n ≠ 25** (e.g. diversity common-paper set, **n=7**)
   - omit for standard full-run figures (n=25 is implicit; LaTeX subtitle covers it)
5. **Stats in title** — only when they're the headline: `(r=0.67)`, `(ρ=0.60*)`. Not judge names, bootstrap n, or SEM notes every time.
6. **Multi-panel** — short suptitle + panel titles; no duplicate run-set noise on every panel.

## Helper (setup cell)

```python
def fig_title(desc: str, *, n_papers: int | None = None, extra: str = "") -> str:
    """Build a notebook figure title. Keep light — captions carry detail."""
    parts = []
    if RUN_SET == "pilot":
        parts.append("pilot")
    if n_papers is not None and (RUN_SET == "pilot" or n_papers != 25):
        parts.append(f"n={n_papers} papers")
    if extra:
        parts.append(extra)
    if parts:
        return f"{desc} ({', '.join(parts)})"
    return desc
```

## Examples

| Run | Call | Title |
|-----|------|-------|
| full | `fig_title("Win-rate by config")` | Win-rate by config |
| full | `fig_title("Per-role diversity", n_papers=7)` | Per-role diversity (n=7 papers) |
| pilot | `fig_title("Win-rate by config", n_papers=5)` | Win-rate by config (pilot, n=5 papers) |
| full | `fig_title("Recall vs verbosity", extra="r=0.67")` | Recall vs verbosity (r=0.67) |

## Anti-patterns

- `f"{RUN_SET}: …"` — internal bucket name, not a title
- Config name as title (`specialist: Spearman ρ=…`) — use caption / table
- Inconsistent bare vs prefixed titles in the same notebook
- Repeating judges, SEM, and n when the LaTeX subcaption already states them
