# Experiment Execution Plan

Homogeneous vs. heterogeneous multi-agent paper review. This file is the runbook for the
execution session: generate reviews, run metrics, prune, pivot. Update it on the fly.

Paper-side context (hypotheses, model fit, metrics) lives in
`../seminar-paper/paper-context/` (`experiment-setup.md`, `model_benchmark_analysis.md`,
`eval-metrics.md`, `dataset.md`).

---

## What we're testing

- **H1 (outcome):** the best heterogeneous config beats the best homogeneous baseline.
- **H2 (mechanism):** different families produce substantively different per-role content; this diversity drives H1.

Operationalised as three design questions:
- **Q1 outcome** — does any heterogeneous config beat `max(All-A, All-B, All-C)`?
- **Q2 assignment** — does the specific role×model mapping matter, or only the set of models? (rotations + specialist/anti)
- **Q3 localization** — which role's model identity matters most? (single-role swaps)

## Pool & judges (locked)

| Key | Model | Profile |
|-----|-------|---------|
| A | `qwen/qwen3-32b` (thinking off) | reasoning |
| B | `mistralai/mistral-small-3.2-24b-instruct` | balanced / instruction-following |
| C | `meta-llama/llama-3.3-70b-instruct` | instruction-following / generalist |

(C was `google/gemma-3-27b-it` until Gemma 3 proved un-pinnable as a tool-calling leader on OpenRouter — only DeepInfra serves Gemma's `tools` API, and it 429s. `llama-3.3-70b` is tool-capable on three fp8 providers, capability-matched to A/B, and from a fourth family.)

Judges (out-of-suite, P4): `openai/gpt-5-mini`, `deepseek/deepseek-v3.2`. Recall/extraction: `openai/gpt-5-mini`. Diversity: local SentenceTransformer. Both judges sit ~27–30 GPQA-Diamond points above the strongest pool member, and neither shares a family with the pool (OpenAI / DeepSeek vs Qwen / Mistral / Llama).

---

## Two buckets

- **Fixed references (never pruned):** `All-A`, `All-B`, `All-C`. Anchor H1, supply the H2 diversity signal, calibrate capability. Always in both stages.
- **Search candidates (pruned):** the 9 heterogeneous configs.

## The 12 configs — `(leader, clarity, experiments, impact)`

Design constant: **leader = B** everywhere except `swap_leader` (A) and the references.
Rationale: C (Llama) does not delegate reliably as leader (pilot: 1/5 papers) so it
cannot occupy the leader seat; A and B both delegate. Fixing leader = B keeps the swap
and rotation families on one delegating leader so role effects aren't confounded by a
leader change. Swap baseline = all-`B`, swap-in `A`.

| ID | tuple | role |
|----|-------|------|
| `All-A` / `All-B` / `All-C` | (A,A,A,A) / (B,B,B,B) / (C,C,C,C) | fixed references |
| `swap_leader` | (A,B,B,B) | Q3 — leader is the only A |
| `swap_clarity` | (B,A,B,B) | Q3 |
| `swap_experiments` | (B,B,A,B) | Q3 |
| `swap_impact` | (B,B,B,A) | Q3 |
| `rot_1` | (B,A,B,C) | Q2 rotation (expert-counterbalanced, leader B) |
| `rot_2` | (B,C,A,B) | Q2 rotation |
| `rot_3` | (B,B,C,A) | Q2 rotation |
| `specialist` | (A,B,A,C) | Q2 informed (benchmark-fit seats) |
| `anti_specialist` | (B,A,C,B) | Q2 mismatched (same {A,B,B,C}-ish set, wrong seats) |

Counterbalance: across `rot_1/2/3` (leader fixed B) each of {A,B,C} fills each expert seat
exactly once. `specialist`/`anti_specialist` test informed vs. mismatched assignment:
specialist puts A→experiments (reasoning) and C→impact (knowledge) in their benchmark-strong
seats with A leading (delegates + reasons); anti deliberately misfits the experts. Full
4-role counterbalancing is impossible because C cannot lead, so the leader is held fixed and
only the three expert seats are rotated.

---

## Budget guardrail

- **Key cap: $50** (per-key limit, not the account). Check anytime with the credits/key endpoint.
- Estimated cost (`poetry run python eval/estimate.py`, pinned-provider prices, grounded token profile, 2 judges, full round-robin): **~$22.03 / €20.27** per full run → ~2.3 runs fit the cap.
- Breakdown: win-rate judging ~76% ($16.82), generation ~17% ($3.65 for all 210 reviews), comment recall ~7% ($1.56); diversity/spearman free. Generation rose from ~5% pre-grounding because every expert now reads the full paper and the leader re-sends it on each of its ~4 calls.
- Providers are **pinned** (qwen→SiliconFlow, mistral→Venice, llama→DeepInfra→Nebius→AkashML; all fp8, ≥131k ctx, all tool-capable) via `PROVIDER_ROUTING` in `review_agent/src/utils/openrouter.py` — this keeps quant/context/tool-calling fixed across runs. `prices.json` reflects these pinned providers (do not `--refresh-prices` without re-pinning the three pool entries).
- Levers if needed: fewer pilot judge calls (single-judge anchored pilot) or truncating the paper in the judge prompt. Note `--dimension overall` does **not** cut cost (one judge call returns all dimensions).

---

## Stage 1 — pilot (12 configs × 5 papers)

Pilot papers (source of truth here; write into `pilot.papers` when `eval/batches.json` is
rebuilt). Chosen to span the strata and difficulty range so the prune generalises to the
held-out 25 — **not** an arbitrary slice.

| Paper | Stratum | rating_std | nrev | chars |
|-------|---------|-----------|------|-------|
| `RZwtbg3qYD` | controversial / Accept | 1.20 | 5 | 52k |
| `tKn6gpvlUX` | controversial / Reject | 1.60 | 5 | 50k |
| `WKfb1xGXGx` | normal / Accept | 0.87 | 4 | 41k (≈ mean) |
| `KgiMUvJcwm` | normal / Reject | 0.87 | 4 | 36k |
| `unDQOUah0F` | normal / Accept | 0.98 | 5 | 39k |

Selection logic:
- **All 4 strata covered**, 2 controversial : 3 normal (mirrors the 10:20 population ratio); 3 Accept : 2 Reject.
- **Spans difficulty** — controversial (std 1.2–1.6, where configs diverge most → discriminative for pruning) vs. clean normal (std 0.87–0.98).
- **No size outliers** — all 36–52k chars (near the 41k mean); excludes the degenerate 1.5k paper and the 83k giant (both kept for the held-out 25).
- `unDQOUah0F` is the **flexible 5th slot** — swap for a normal-Reject (e.g. `r0opxuq8T8`) to go 2A/3R.

```bash
# 0. preflight: confirm the run matrix and that nothing is spent yet
poetry run python eval/experiments.py --run-set pilot --dry-run

# 1. generate (sequential, resumable, ~$0.30 of generation)
poetry run python eval/experiments.py --run-set pilot

# 2. Stage-1 pruning signal: win-rate ONLY (overall dimension keeps it cheap)
poetry run python eval/metrics/win_rate.py --run-set pilot --dimension overall
```

**Prune:** from `eval/results/pilot/metrics/win_rate.json`, rank the **9 heterogeneous** configs by `per_config.overall`; keep the **top ~3**. The 3 homogeneous references are kept regardless.

---

## Stage 2 — full (6 configs × held-out 25 papers)

The pilot's 5 papers were used for selection, so finalists are scored on the **other 25** to avoid selection bias.

1. Add a `full` run-set to `eval/batches.json`: pool `{A,B,C}`, the **6** configs (3 references + 3 survivors), and `papers` = the 25 dataset ids **not** in the pilot.

```bash
# 3. generate finalists on the held-out 25
poetry run python eval/experiments.py --run-set full --dry-run
poetry run python eval/experiments.py --run-set full

# 4. full metric suite (all share --run-set)
poetry run python eval/metrics/win_rate.py --run-set full          # 2 judges, all dimensions
poetry run python eval/metrics/comment_recall.py --run-set full
poetry run python eval/metrics/diversity.py --run-set full
poetry run python eval/metrics/spearman.py --run-set full
poetry run python eval/metrics/cost.py --run-set full
```

---

## Read the results

- **Capability precondition (do first):** spread of `All-A/B/C` win-rates. If one runs away, report the gap and frame H2 relative to it. `All-C` (Llama-3.3-70B, the pool's strongest instruction-follower at IFEval 92.1) is a plausible baseline to beat, but let the pilot decide rather than presuming.
- **H1 / Q1:** best heterogeneous vs. best homogeneous (win-rate, then comment recall for substance).
- **Q2 assignment:** are `rot_1/2/3` ≈ equal (composition-only)? is `specialist` > `anti_specialist` (assignment matters)?
- **Q3 localization:** which `swap_*` moves win-rate most? is the leader-swap effect > expert-swap effects?
- **H2 diversity:** per-role cross-model dissimilarity from `All-A/B/C` (diversity metric) — which role is most model-sensitive.
- **Confounds to keep in mind:** the leader writes the final review, so win-rate partly reflects leader writing style — lean on comment recall for substance. Spearman is a calibration anchor, not a quality signal.

## Data quality — full run (regenerated 2026-06-28)

The first full generation (175 runs, concurrency 4) had 21 bad runs, all
Mistral-leader: 16 empty (Venice/DeepInfra **429** rate-limits wiped the experts
and/or the leader emitted only a plan), 4 heterogeneous runs where the leader
never delegated (manipulation absent), 1 All-C run poisoned by 429 error text
captured as expert "output". A further 5 valid runs had the leader's planning
preamble (`### Current Step:` / `### High-Level Plan` / `### Current Task:`)
leaking into `final_review.md`, which the win-rate and comment-recall judges read
verbatim.

Fixes landed in the harness:
- `final_review.md` is normalised to `[first section header … RATING line]`
  (`review_parser.normalize_final_review`), stripping leader scaffolding. The 5
  pre-existing contaminated runs were cleaned in place.
- `is_run_complete` now requires a **substantive** review (non-null rating **and**
  all four non-empty sections), so parse failures auto-regenerate and never feed
  metrics (`spec.review_is_substantive`).
- `default_runner` retries up to `REVIEW_MAX_ATTEMPTS` (default 3) on a
  non-substantive review or transient error, committing the first valid attempt
  (isolated per-attempt dirs; no trace interleave). 429 avoidance = run at
  `--concurrency 1` (litellm-style `num_retries` can't be injected through this
  CrewAI version — it reaches the OpenAI SDK and is rejected).

The 21 originals are backed up under `eval/reviews/_quarantine_full_<ts>/`.
Re-audit after regeneration: **173/175 fully clean**.

**Delegation behaviour is an outcome, not just a control (keep all 175).**
Across the full run the leader's decision to delegate is strongly
model-dependent — and paper-dependent:

| Leader | delegates to all 3 experts | zero delegation |
|--------|----------------------------|-----------------|
| A (qwen3-32b)        | 75/75 (100%) | 0  |
| B (mistral-small-3.2)| 72/75 (96%)  | 3  |
| C (llama-3.3-70b)    | 7/25 (28%)   | 18 |

All 3 of Mistral's zero-delegation runs are on the **same paper `6jxUsDAdAu`**
(across `All-B`, `rot_2`, `swap_experiments`) — a reproducible
(Mistral-leader × this paper) → self-review behaviour, not noise. We **keep**
`rot_2__6jxUsDAdAu` and `swap_experiments__6jxUsDAdAu` as valid runs: they are
proper reviews, and excluding them while retaining All-C's 18 zero-delegation
runs would be a double standard (Llama-as-leader mostly doesn't delegate either).
Treat the delegation rate itself as an H2 finding — it extends the "C can't
lead" rationale (B occasionally won't either, paper-dependently). Caveat only
where it bites: win-rate is unaffected (leader writes the final text regardless),
but comment-recall/diversity read per-role expert outputs, so a zero-delegation
run legitimately contributes no per-role diversity signal.

## On-the-fly knobs

- Swap direction (`A→C` vs `C→A`), pilot paper set, how many survivors promote (default ~3), 25 vs 30 final papers.
- Keep this file and `eval/batches.json` in sync as you pivot.
