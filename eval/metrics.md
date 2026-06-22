# Evaluation Metrics — Implementation Spec

> Working spec for implementing the evaluation suite of the homogeneous-vs-heterogeneous
> multi-agent review study. **Each `##` metric section is self-contained and independently
> ownable** — a parallel agent session can pick one section and implement it end-to-end
> without touching the others. Read §0 first; it defines the shared inputs, conventions,
> and prerequisites every metric depends on.

---

## 0. Context, conventions, and prerequisites

### 0.1 What we are evaluating

A multi-agent reviewer (`review_agent/src/agents/reviewer.py`): one **leader** + three experts
(**clarity**, **experiments**, **impact**). The *only* thing that varies between experimental
**configurations** is which LLM is assigned to each of the four roles. A configuration is a
4-tuple `(leader, clarity, experiments, impact)`.

- **Homogeneous** config: same model in all four roles (`All-A`, `All-B`, `All-C` for pool `{A,B,C}`).
- **Heterogeneous** config: models mixed across roles.

### 0.2 Hypotheses these metrics serve

- **H1 (outcome):** the best heterogeneous config beats the best homogeneous baseline on review quality.
- **H2 (mechanism):** different LLM families produce substantively different content **per role**; this
  diversity may explain H1.

### 0.3 Metric → purpose map

| # | Metric | Serves | Judge-independent? | Status |
|---|--------|--------|--------------------|--------|
| 1 | LLM-as-judge win-rate | H1 (primary, relative quality) | No | **Core** |
| 2 | Comment recall (+ comment count) | H1 coverage **and** H2 outcome signature | Partial | **Core** |
| 3 | Per-role cross-model diversity | H2 (mechanism) | Yes (embeddings) | **Core** |
| 4 | Decision score alignment (Spearman) | objective bias-immune anchor | Yes | **Core** |
| 5 | Cost & inference time | control / budget | Yes | **Core** |
| O1 | H-Max | absolute "vs human ceiling" quality | No | **Optional** |
| O2 | Precision / Jaccard | overlap diagnostics (appendix only) | Partial | **Optional** |

### 0.4 Data inputs (shared)

**Papers** — `dataset/eval_sample_30.json`, key `papers[]`, each item:

```json
{
  "id": "1Qpt43cqhg",
  "decision": "Accept",
  "stratum": "controversial",          // "controversial" | "normal"
  "ratings": [6, 8, 5, 7],             // numeric human reviewer scores
  "rating_std": 1.09,
  "n_reviewers": 4,
  "paper_text": "\\title{...}...",     // full LaTeX body
  "human_reviews": [                   // structured ICLR review forms (ground truth)
    {
      "id": "IwyEWtfHt7",
      "rating": 8,                     // 1-10 overall score (top-level; mirrors content.rating)
      "content": {
        "summary": "...",
        "strengths": "...",
        "weaknesses": "...",
        "questions": "...",
        "soundness": 3,                // 1-4 (not used by core metrics)
        "presentation": 2,
        "contribution": 4,
        "confidence": 4,
        "rating": 8
      }
    }
  ]
}
```

**Run artifacts** — every `(config, paper)` run produces a directory (see `TraceLogger`):

- `final_review.md` — full final review text (untruncated markdown + trailing `RATING:` line). Source for metrics 1, O1 (whole-text judge).
- `review.json` — structured parse of the review, mirroring the core human `content` keys:

```json
{
  "summary": "...",
  "strengths": "...",
  "weaknesses": "...",
  "questions": "...",
  "rating": 7
}
```

Source for metric 4 (`rating` vs `mean(ratings)`) and metric 2 (comment extraction from `weaknesses` + `questions`). Written by `parse_review()` after each traced run.
- `trace.jsonl` — one JSON object per line. Relevant record types:

```
run_header        {paper_id, paper_chars, paper_hash, models:{role:model}, roles:{role:label}}
llm_call          {agent_role, model, tokens_in, tokens_out, total_tokens}   # one per LLM call
delegation_finished {expert_role, task, output, output_chars, duration_ms, status}  # output is PREVIEW-TRUNCATED (see P1)
leader_completion {output, output_chars}                                # output is PREVIEW-TRUNCATED; full text is in final_review.md
review_parsed     {rating, summary_chars, strengths_chars, weaknesses_chars, questions_chars}
run_footer        {duration_ms, delegations, delegation_errors}              # duration_ms = total wall-clock
```

### 0.5 Run manifest (orchestration contract)

Assume the run orchestrator emits `eval/runs/manifest.json` so metrics can locate inputs without
guessing paths. If it does not exist yet, the first metric implemented should define and create it:

```json
{
  "configs": {
    "All-A":  {"models": {"leader":"A","clarity":"A","experiments":"A","impact":"A"}, "homogeneous": true},
    "het_01": {"models": {"leader":"A","clarity":"B","experiments":"C","impact":"A"}, "homogeneous": false}
  },
  "runs": [
    {"config_id": "All-A", "paper_id": "1Qpt43cqhg", "run_dir": "eval/outputs/<ts>"}
  ]
}
```

### 0.6 Output convention

Each metric writes to `eval/metrics/<metric_name>.json` with **both** per-`(config[,paper])` detail
and a per-config aggregate block, so downstream aggregation is uniform. Use macro-averaging over
papers (mean of per-paper values) unless a section says otherwise.

### 0.7 Global prerequisites (some block specific metrics)

| ID | Prerequisite | Blocks | Notes |
|----|--------------|--------|-------|
| **P1** | Persist **full** per-agent (per-role) output text | **Metric 3** | `ReviewTraceListener` currently stores `preview(output)` (≤500 chars). Either remove the cap for `delegation`/`leader_completion` outputs, or write each agent's full output to `eval/outputs/<ts>/agents/<role>.txt`. Full text is mandatory for embeddings. |
| **P2** | Emit a **numeric overall score (1–10)** per review | — | **Done.** Leader outputs `RATING: <1-10>`; `parse_review()` extracts it into `review.json`. Metric 4 reads `review.json` → `rating`. |
| **P3** | `eval/prices.json` — per-model OpenRouter price table | Metric 5 | `{ "<openrouter_model_id>": {"in": <usd_per_1M_in>, "out": <usd_per_1M_out>} }`. |
| **P4** | Judge model pool: **≥2 models, out-of-suite, none from the candidate families, different families from each other** | Metrics 1, O1 | Self-preference bias guardrail (see §0.8). |
| **P5** | Embedding model choice (fixed across all runs) | Metric 3 | e.g. a SentenceTransformer (`all-MiniLM-L6-v2`/`bge-*`) or a hosted embedding API. Record model id in output. |
| **P6** | Comment extraction + alignment LLM | Metric 2, O2 | May be one of the judge-class models; fix it and record id. |

### 0.8 Guardrails — read before implementing 1 or O1

- **Judge self-preference bias is real and directly threatens H1** (a family-heterogeneity claim).
  Always use multiple out-of-suite judges (P4); never let a model judge its own family.
- **Position bias:** always evaluate each pair in **both orders** (or randomize and record order),
  then average.
- **Do NOT** implement RDS (whole-system re-run variance) as a diversity metric — it measures
  sampling jitter, not model-induced diversity. The diversity metric is **Metric 3** only.
- **Do NOT** use precision/Jaccard as quality signals (they penalize valid novel comments). Recall is
  the headline; precision/Jaccard are appendix-only (O2).

---

## 1. LLM-as-judge win-rate  *(Core · H1 · primary)*

**Serves.** H1. Relative quality: which config's reviews are preferred head-to-head. This is the
primary outcome metric and the pruning signal for the Successive-Halving pilot.

**Inputs.** For a config pair `(A, B)` on paper `p`: `final_review.md` of each, plus `paper_text`
from the dataset. Judge pool from P4.

**Method.**
1. For each unordered config pair and each paper, build a judging prompt: the paper (or its
   abstract+intro if context-limited) and **two anonymized reviews** labelled *Review 1* / *Review 2*.
2. Ask each judge to pick the better review (`1`, `2`, or `tie`) on each **dimension**:
   `overall` (primary) + aspect dims `technical_soundness`, `constructiveness`, `clarity`,
   `significance`. Dimensions are configurable; `overall` is mandatory.
3. **Position-debias:** run the pair in both orders (A=Review 1, then B=Review 1); average outcomes.
4. **Multiple judges (P4):** repeat for each judge; aggregate by averaging win fractions.

**Formula.** With ties counted as half:

```
score(A vs B) = (wins_A + 0.5 * ties) / n_comparisons          # per dimension, over orders × judges × papers
WinRate(A)    = mean over all opponents B of score(A vs B)      # config-level
```

Optional global ranking via **Bradley–Terry** (fit strengths β by MLE on pairwise win counts):

```
P(A beats B) = exp(β_A) / (exp(β_A) + exp(β_B))
```

Report BT strength per config (and/or convert to Elo for presentation). BT is preferred over raw
win-rate when the pairwise design is unbalanced.

**Output** (`eval/metrics/win_rate.json`): per-pair, per-dimension, per-judge raw outcomes;
per-config aggregated `WinRate` per dimension; optional BT strengths with bootstrap CIs.

**Notes.** Keep the rubric text fixed and store it alongside results. Log raw judge responses for
auditability. Source: MAMORX (Elo arena), ScholarPeer (SxS win-rate across dimensions).

---

## 2. Comment recall + comment count  *(Core · H1 coverage & H2 outcome signature)*

**Serves.** H1 (coverage of human-flagged issues) and — crucially — the **outcome-level signature of
H2**: if heterogeneity reduces shared blind spots, configs should cover *more* distinct human issues
(higher recall).

**Inputs.** Per paper: config `final_review.md` (→ generated comments `C_gen`) and `human_reviews[]`
(→ ground-truth comments `C_real`). Extraction/alignment LLM from P6.

**Method (two-stage alignment, after MARG §6).**
1. **Extract** atomic, *actionable* comments from each review (the config review and each human
   review). Instruct the extractor to keep criticism/suggestions and **ignore** positive remarks and
   minor grammar/style. Union the human comments across that paper's reviews → `C_real`.
2. **Many-to-many candidate match:** feed all `C_gen` and `C_real` to the LLM; ask for all matching
   pairs. Run 5 passes with shuffled order; keep pairs appearing in **≥2/5** passes.
3. **Pairwise filter:** for each candidate pair, score **relatedness** ∈ {none, weak, medium, high}
   and **relative specificity** ∈ {less, same, more}. A pair is a **match** iff
   `relatedness ∈ {medium, high}` **and** `specificity ∈ {same, more}`.

**Formula.** Directional intersections (matches are many-to-many, so use directional operators):

```
C_gen →∩ C_real = real comments matched by ≥1 generated comment
C_gen ←∩ C_real = generated comments matched by ≥1 real comment

Recall    = |C_gen →∩ C_real| / |C_real|          # headline
n_comments = |C_gen|                              # mandatory companion (guards against volume-gaming)
```

Macro-average `Recall` and `n_comments` over papers per config.

**Output** (`eval/metrics/recall.json`): per-paper `recall`, `|C_gen|`, `|C_real|`, matched counts;
per-config macro-averaged `recall` and `n_comments`. Persist the extracted comment lists and the
alignment edges for inspection.

**Notes.** `n_comments` is a normaliser, **not** its own axis — always report it next to recall so a
high recall driven purely by verbosity is visible. Source: MARG §6.

---

## 3. Per-role cross-model diversity  *(Core · H2 mechanism)*

**Serves.** H2. Measures whether different models, **doing the same job**, produce different content.
This is the input-side mechanism evidence (pairs with Metric 2's outcome-side evidence).

**Key design rule.** Diversity is measured over outputs of **different models** on the **same role +
same paper** — never across different roles (confounded by role), never across re-runs of one config
(that's RDS = sampling noise). The clean source is the **homogeneous runs**: `All-A`, `All-B`,
`All-C` each give that role's output under one model.

**Inputs.** **Full** per-role output text from the three homogeneous runs (requires **P1**). For each
role `r ∈ {leader, clarity, experiments, impact}` and paper `p`, collect `o_r^A, o_r^B, o_r^C`.
Embedding model from P5.

**Method.**
1. Embed each role output: `E(o_r^m)`.
2. Compute mean pairwise cosine similarity across the `M=3` models for the same `(r, p)`.
3. Diversity = `1 − similarity`. Average over papers → a per-role diversity number.
4. (Optional, recommended) also compute the **Vendi Score** = effective number of distinct outputs.

**Formula.** (Same shape as ScholarPeer RDS Eq. 1, but applied **per role, across models** instead of
across whole-system re-runs.)

```
IRSim_r(p)     = 1/(M(M-1)) * Σ_{i≠j} cos( E(o_r^i), E(o_r^j) )     # M = 3 models
Diversity_r(p) = 1 − IRSim_r(p)
Diversity_r    = mean_p Diversity_r(p)

# Optional Vendi Score over the set {o_r^A, o_r^B, o_r^C}:
#   K = cosine-similarity matrix (M×M), normalized so trace(K/M) = 1, eigenvalues λ_k
#   VS = exp( − Σ_k λ_k log λ_k )        # 1 = all identical, up to M = all distinct
```

**H2 link (analysis, document but lighter weight).** Regress a config's *embedded* diversity against
its quality (Metric 1 / Metric 2) across configurations, controlling for proposer quality so the gain
is attributed to **diversity**, not to a single dominant model. Per-role diversity also localises
*which* role is most model-sensitive (informs design hypotheses DH3 leader-bottleneck, DH5 per-role
asymmetry).

**Output** (`eval/metrics/diversity.json`): per-`(role, paper)` similarity/diversity; per-role
aggregate; optional Vendi; embedding model id.

**Notes.** Embedding cosine conflates style and substance; treat the number as a coarse signal and
lean on Metric 2 (issue-level coverage) for the substantive claim. Source: ScholarPeer RDS (Eq. 1)
adapted; Mixture-of-Agents (Li et al. 2025) for the diversity-vs-quality framing.

---

## 4. Decision score alignment (Spearman ρ)  *(Core · objective anchor)*

**Serves.** A **judge-independent**, bias-immune cross-check: does the config's predicted decision
score rank papers the way human scores do. The only metric with no LLM in the scoring loop — the
robustness anchor against judge self-preference.

**Inputs.** Config numeric score per paper `s_{c,p}` (requires **P2**). Human ground truth per paper
`h_p = mean(ratings_p)` from the dataset. `stratum` for the split.

**Method.** Across the paper set, rank-correlate config scores with human mean scores. Report overall
**and** split by `stratum` (controversial vs normal). Report a p-value / bootstrap CI.

**Formula.**

```
h_p = mean(ratings_p)
ρ   = Spearman rank correlation between {s_{c,p}}_p and {h_p}_p
    = 1 − 6 Σ d_i² / (n(n²−1))         # d_i = rank diff; no-ties form
```

Integer 1–10 scores produce many ties → use the **tie-corrected** form (Pearson correlation on ranks,
i.e. `scipy.stats.spearmanr`, which also returns the p-value).

**Output** (`eval/metrics/decision_alignment.json`): per-config ρ (overall + per stratum), p-value/CI,
and the raw `(s_{c,p}, h_p)` pairs.

**Notes.** n≈30 with ties → noisy; always report the CI. This measures recommendation **calibration**,
not feedback quality — keep it framed as an anchor, not a quality metric. Source: ScholarPeer §4.2.

---

## 5. Cost & inference time  *(Core · control)*

**Serves.** Practical viability + a confound control (does heterogeneity buy quality merely by being
more expensive?) + budgeting for the Successive-Halving protocol.

**Inputs.** `trace.jsonl` per `(config, paper)`: `llm_call` records (`tokens_in`, `tokens_out`,
`model`, `agent_role`) and `run_footer.duration_ms`. Price table `eval/prices.json` (**P3**).

**Method.** Sum tokens over all `llm_call` records per run; read wall-clock from `run_footer`; price
each call by its model. Aggregate per config as mean ± SEM over papers.

**Formula.**

```
input_tokens_run  = Σ_calls tokens_in
output_tokens_run = Σ_calls tokens_out
time_run_s        = run_footer.duration_ms / 1000

cost_run = Σ_calls ( tokens_in/1e6 · price_in(model) + tokens_out/1e6 · price_out(model) )

# per config, over n papers:
mean ± SEM  where  SEM = stdev / sqrt(n)
```

**Output** (`eval/metrics/cost_time.json`): per-run tokens/cost/time (+ per-role token breakdown from
`agent_role`); per-config mean ± SEM.

**Notes.** Token-per-role breakdown is free here (the `llm_call` records carry `agent_role`) and is
useful for the leader-bottleneck analysis. Source: MAMORX §5 (cost analysis).

---

## Optional

> Implement only after the five core metrics are in place.

### O1. H-Max score  *(absolute quality vs human ceiling)*

**Serves.** "Are we approaching human quality?" — absolute, human-anchored review quality. Not
required by H1/H2 (which are relative, hetero-vs-homo), hence optional.

**Inputs.** One config `final_review.md` + that paper's `human_reviews[]`. Judge pool from P4.

**Method.** An (search-enabled if available) expert LLM judge scores the single AI review on a **1–10**
scale **per dimension** (`technical_accuracy`, `constructive_value`, `analytical_depth`,
`significance`, `overall`), calibrated against the **strongest points made by any human reviewer** on
that dimension ("Expert Baseline").

**Anchor rubric.**

```
1  = misses critical points the human reviewers raised
5  = matches the strongest points across the set of human reviewers
10 = transformative relative to the collective human reviews
```

**Aggregate.** Per-dimension H-Max + average; macro-average over papers per config.

**Output** (`eval/metrics/hmax.json`): per-paper per-dimension scores; per-config aggregates; judge id.

**Notes.** Judge-dependent → inherits self-preference risk; use P4 and report per judge. Source:
ScholarPeer §4.2 (H-Max), Appendix F.3 rubric.

### O2. Precision / Jaccard  *(overlap diagnostics — appendix only)*

Computed for free from the Metric 2 alignment. **Not** quality signals (they penalize valid novel
comments). Report in an appendix table for MARG comparability only.

```
Precision = |C_gen ←∩ C_real| / |C_gen|
intersection = ( |C_gen ←∩ C_real| + |C_gen →∩ C_real| ) / 2
Jaccard      = intersection / ( |C_gen| + |C_real| − intersection )
```

Source: MARG §6.2.
