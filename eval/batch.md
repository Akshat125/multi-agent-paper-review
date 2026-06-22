# Batch Registry — Contract

> **Scope: generation session** (writes registry + run artifacts) and the **data handoff**
> metrics sessions consume. Defines *where* things live and *what shape* the registry has.
>
> **Not in this doc:** metric formulas, judge rubrics, aggregation logic → `eval/metrics.md`.

---

## Handoff

```
GENERATION                          EVALUATION (metrics session)
  experiments.py                      eval/metrics/metric*.py
    └─ reviewer.py                      └─ reads batch via eval/metrics/batch.py
    └─ writes artifacts  →  eval/outputs/<run_dir>/
    └─ writes registry   →  eval/runs/<batch>/{configs.json, runs.jsonl}
              │                              └─ writes → eval/runs/<batch>/metrics/*.json
              └──────── handoff ───────────────┘
```

Generation **writes**; metrics **read**. Neither imports the other.

---

## Batch

A **batch** is a named, self-contained run-set (e.g. `pilot_v1`, `full_eval`). Not a fixed
experiment stage — just a label for a group of runs executed together. Cross-batch comparison
is done explicitly in a notebook; there is no global merged log.

---

## Layout

```
eval/
  batch.md                 ← this doc
  metrics.md               ← metric computation spec
  outputs/
    <run_dir>/             ← per-run artifacts (TraceLogger)
      final_review.md
      review.json
      trace.jsonl
  runs/
    <batch_name>/
      configs.json         ← written by generation
      runs.jsonl           ← written by generation (append-only)
      metrics/             ← written by metric scripts
        <name>.json
```

---

## `configs.json`

Maps each `config_id` to its per-role model assignment.

```json
{
  "All-A":  {"models": {"leader": "A", "clarity": "A", "experiments": "A", "impact": "A"}, "homogeneous": true},
  "het_01": {"models": {"leader": "A", "clarity": "B", "experiments": "C", "impact": "A"}, "homogeneous": false}
}
```

Roles: `leader`, `clarity`, `experiments`, `impact`. Model values are the exact ids used at
generation time (e.g. OpenRouter slug).

---

## `runs.jsonl`

One JSON object per line, appended as each run completes. **Append-only** — never edit past lines.

```json
{"config_id": "het_01", "paper_id": "1Qpt43cqhg", "run_dir": "eval/outputs/20260622T103210Z", "replicate": 0}
```

| Field | Meaning |
|-------|---------|
| `config_id` | key into this batch's `configs.json` |
| `paper_id`  | key into `dataset/eval_sample_30.json` |
| `run_dir`   | path (relative to project root) to artifact directory |
| `replicate` | integer; `0` unless the same (config, paper) is re-run |

Extra fields (`ts`, `notes`, …) are allowed; no metric depends on them.

**Replicate policy.** Metrics read `replicate=0` only unless a metric spec says otherwise.

---

## Run artifacts (`eval/outputs/<run_dir>/`)

Each completed run must produce:

| File | Required |
|------|----------|
| `final_review.md` | yes |
| `review.json` | yes |
| `trace.jsonl` | yes |

Field semantics and which metrics read which fields: `eval/metrics.md` §0.4.

---

## Invariants

1. Every `run_dir` contains the three artifact files above.
2. Each line maps to exactly one `(config_id, paper_id, replicate)`.
3. `config_id` resolves via this batch's `configs.json`.
4. `runs.jsonl` is append-only.

More batches or more lines express new stages/sweeps/re-runs — **never** a schema change.

---

## Generation responsibilities

| Item | Owner | Status |
|------|-------|--------|
| `eval/experiments.py` orchestrator | generation | not built (`smoke.py` = single-run seed) |
| `eval/outputs/<run_dir>/…` | generation (TraceLogger) | exists |
| `eval/runs/<batch>/configs.json` | generation | — |
| `eval/runs/<batch>/runs.jsonl` | generation | — |

**P1 (blocks Metric 3).** Persist **full** per-expert output text. `ReviewTraceListener` currently
truncates to 500 chars — remove the cap or write `agents/<role>.txt` per run.

**P2 (done).** `review.json` must include numeric `rating` (1–10). Leader emits `RATING:` line;
`parse_review()` extracts it.

---

## Metrics read contract

Metrics sessions assume the batch registry already exists. They:

1. Load `eval/runs/<batch>/configs.json` + `runs.jsonl` (via `eval/metrics/batch.py`).
2. Resolve each `run_dir`, read artifacts per `eval/metrics.md`.
3. Write results to `eval/runs/<batch>/metrics/<name>.json`.

Example:

```bash
python eval/metrics/metric1_win_rate.py --batch pilot_v1
# → eval/runs/pilot_v1/metrics/win_rate.json
```

What each metric computes: `eval/metrics.md`. Metric-side prerequisites (P3–P6): `eval/metrics.md` §0.6.
