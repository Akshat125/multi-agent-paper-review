"""Budget estimator for the homogeneous-vs-heterogeneous review experiments.

Standalone, stdlib-only. Prices every stage of the plan (generation + LLM-as-judge
metrics) from three real sources so the number is grounded, not guessed:

* ``eval/prices.json``        — per-provider USD/1M token rates. The three pool
  models are priced at the **pinned** OpenRouter providers (see
  ``review_agent/src/utils/openrouter.py::PROVIDER_ROUTING``), not the cheapest
  default endpoint.
* ``eval/batches.json``       — the actual config matrix and pool aliases.
* ``dataset/eval_sample_30.json`` — real per-paper character counts.

The per-role generation token profile is measured from a real grounded-expert run
(``eval/reviews/pilot/All-A__RZwtbg3qYD/trace.jsonl``, qwen homogeneous, 52,140-char
paper, 3 delegations). Crucially this reflects the expert-grounding change: every
expert now reads the full paper, and the leader re-sends the paper on each of its
~4 calls, so generation is a much larger slice of the budget than the pre-grounding
estimate assumed.

Run::

    python eval/estimate.py
    python eval/estimate.py --eur-per-usd 0.92
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
ROOT = EVAL_DIR.parent
PRICES_PATH = EVAL_DIR / "prices.json"
BATCHES_PATH = EVAL_DIR / "batches.json"
DATASET_PATH = ROOT / "dataset" / "eval_sample_30.json"

# --------------------------------------------------------------------------- #
# Measured token profile (eval/reviews/pilot/All-A__RZwtbg3qYD/trace.jsonl)
# --------------------------------------------------------------------------- #
# Grounded-expert run on a 52,140-char paper, 3 delegations (=4 leader calls):
#   role      calls  tokens_in  tokens_out
#   leader      4       86,812      1,476     (paper re-sent each call)
#   clarity     1       17,094      2,230
#   experiments 1       17,066      2,281
#   impact      1       16,967      2,212
#
# Model: only the input scales with paper size. paper_tokens = chars / CHARS_PER_TOKEN.
#   leader_in  = LEADER_CALLS * paper_tokens + LEADER_FIXED_IN
#   expert_in  = paper_tokens + EXPERT_FIXED_IN
# Fitted so the model reproduces the trace at 52,140 chars (paper_tokens ~= 14,897).
CHARS_PER_TOKEN = 3.5
LEADER_CALLS = 4              # 3 delegations + 1 aggregation (the designed path)
LEADER_FIXED_IN = 27_200     # accumulated expert outputs + prompts + tool overhead
LEADER_OUT = 1_476
EXPERT_FIXED_IN = 2_150      # expert system + task prompt (paper-independent)
EXPERT_OUT = 2_240

EXPERT_ROLES = ("clarity", "experiments", "impact")
ROLES = ("leader",) + EXPERT_ROLES

# --------------------------------------------------------------------------- #
# Judge token model (Metric 1 win-rate, ScholarPeer H.2 SxS)
# --------------------------------------------------------------------------- #
# build_comparison_prompt feeds the FULL paper + both reviews + the H.2 system
# prompt; output is THOUGHT (5 dimensions) + a 5-field JSON. Each comparison is
# run in BOTH presentation orders (position debiasing) => 2 calls.
JUDGE_SYS_TOKENS = 800        # ScholarPeer H.2 system prompt
REVIEW_TOKENS = 1_200        # one final_review.md (~4.1k chars measured)
JUDGE_OUT_TOKENS = 2_000     # THOUGHT(5 dims) + JSON
JUDGE_ORDERS = 2

# Metric 2 comment-recall (full stage only), per (config, paper) unit.
RECALL_PROMPT_IN = 2_700     # candidate review + matching instructions (excl. paper)
RECALL_OUT = 2_750
RECALL_HUMAN_EXTRA_IN = 1_500   # human-comment extraction prompt, once per paper
RECALL_HUMAN_OUT = 2_500

WINRATE_JUDGES = ("openai/gpt-5-mini", "deepseek/deepseek-v3.2")
RECALL_JUDGE = "openai/gpt-5-mini"


def paper_tokens(chars: int) -> float:
    return chars / CHARS_PER_TOKEN


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
def load_prices() -> dict[str, dict[str, float]]:
    raw = json.loads(PRICES_PATH.read_text(encoding="utf-8"))
    return {k: {"in": float(v["in"]), "out": float(v["out"])} for k, v in raw.items()}


def load_batch(run_set: str) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Return (pool alias->slug, configs role->slug) for one run-set in batches.json."""
    spec = json.loads(BATCHES_PATH.read_text(encoding="utf-8"))[run_set]
    pool = spec["pool"]
    configs = {
        cid: {role: pool[alias] for role, alias in roles.items()}
        for cid, roles in spec["configs"].items()
    }
    return pool, configs


def load_paper_chars() -> dict[str, int]:
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    papers = data["papers"] if isinstance(data, dict) else data
    return {(p.get("paper_id") or p.get("id")): len(p["paper_text"]) for p in papers}


PRICES = load_prices()


def usd(model: str, t_in: float, t_out: float) -> float:
    entry = PRICES.get(model) or PRICES.get(model.removeprefix("openrouter/"))
    if entry is None:
        raise KeyError(f"no price for {model!r} in prices.json")
    return t_in / 1e6 * entry["in"] + t_out / 1e6 * entry["out"]


# --------------------------------------------------------------------------- #
# Stage costs
# --------------------------------------------------------------------------- #
def gen_cost(config_models: dict[str, str], chars: int) -> float:
    """Generation cost of one (config, paper) run, each role priced at its model."""
    pt = paper_tokens(chars)
    total = usd(config_models["leader"], LEADER_CALLS * pt + LEADER_FIXED_IN, LEADER_OUT)
    for role in EXPERT_ROLES:
        total += usd(config_models[role], pt + EXPERT_FIXED_IN, EXPERT_OUT)
    return total


def generation_total(configs: dict[str, dict[str, str]], chars_by_paper: list[int]) -> float:
    return sum(
        gen_cost(models, chars)
        for models in configs.values()
        for chars in chars_by_paper
    )


def winrate_total(n_configs: int, chars_by_paper: list[int], judges: tuple[str, ...]) -> tuple[float, int]:
    """Pairwise SxS judging: every config pair, both orders, every judge, every paper."""
    n_pairs = len(list(combinations(range(n_configs), 2)))
    cost = 0.0
    calls = 0
    for chars in chars_by_paper:
        judge_in = JUDGE_SYS_TOKENS + paper_tokens(chars) + 2 * REVIEW_TOKENS
        for _pair in range(n_pairs):
            for judge in judges:
                cost += JUDGE_ORDERS * usd(judge, judge_in, JUDGE_OUT_TOKENS)
                calls += JUDGE_ORDERS
    return cost, calls


def recall_total(n_configs: int, chars_by_paper: list[int], judge: str) -> float:
    cost = 0.0
    for chars in chars_by_paper:
        pt = paper_tokens(chars)
        cost += usd(judge, pt + RECALL_HUMAN_EXTRA_IN, RECALL_HUMAN_OUT)  # once per paper
        cost += n_configs * usd(judge, pt + RECALL_PROMPT_IN, RECALL_OUT)  # per config
    return cost


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eur-per-usd", type=float, default=0.92)
    ap.add_argument("--full-survivors", type=int, default=3,
                    help="heterogeneous configs promoted to the full stage (default 3)")
    args = ap.parse_args()
    rate = args.eur_per_usd

    pool, pilot_configs = load_batch("pilot")
    chars = load_paper_chars()
    pilot_ids = ["RZwtbg3qYD", "tKn6gpvlUX", "WKfb1xGXGx", "KgiMUvJcwm", "unDQOUah0F"]
    pilot_chars = [chars[p] for p in pilot_ids]
    full_chars = [chars[p] for p in chars if p not in pilot_ids]

    # Full stage = 3 homogeneous references + N promoted heterogeneous configs.
    homog = {c: m for c, m in pilot_configs.items() if len(set(m.values())) == 1}
    heterog = [c for c in pilot_configs if c not in homog]
    full_config_ids = list(homog) + heterog[: args.full_survivors]
    full_configs = {c: pilot_configs[c] for c in full_config_ids}
    n_full = len(full_configs)

    # ---- stage costs ----
    gen_pilot = generation_total(pilot_configs, pilot_chars)
    gen_full = generation_total(full_configs, full_chars)
    gen = gen_pilot + gen_full

    wr_pilot, calls_pilot = winrate_total(len(pilot_configs), pilot_chars, WINRATE_JUDGES)
    wr_full, calls_full = winrate_total(n_full, full_chars, WINRATE_JUDGES)
    winrate = wr_pilot + wr_full

    recall = recall_total(n_full, full_chars, RECALL_JUDGE)  # full stage only
    diversity = 0.0  # local SentenceTransformer
    spearman = 0.0   # uses ratings already in the reviews

    total = gen + winrate + recall

    def line(label: str, val: float) -> str:
        return f"  {label:<34}${val:7.2f}   EUR {val * rate:7.2f}   {val / total * 100:4.1f}%"

    print("=" * 78)
    print("EXPERIMENT BUDGET ESTIMATE  (pinned-provider prices; grounded token profile)")
    print("=" * 78)
    print(f"Pool   : A={pool['A']}  B={pool['B']}  C={pool['C']}")
    print(f"Pinned : qwen->SiliconFlow  mistral->Venice  llama->DeepInfra (fp8, >=131k ctx)")
    print(f"Design : pilot {len(pilot_configs)} cfg x {len(pilot_chars)} papers"
          f"  ->  full {n_full} cfg x {len(full_chars)} papers")
    print(f"Judges : win-rate {list(WINRATE_JUDGES)}  | recall {RECALL_JUDGE}")
    print("-" * 78)
    print(line("generation (210 reviews)", gen))
    print(f"      pilot {gen_pilot:.2f} + full {gen_full:.2f} "
          f"(per-review avg {gen / (len(pilot_configs)*len(pilot_chars) + n_full*len(full_chars)):.4f})")
    print(line("win-rate judging", winrate))
    print(f"      pilot {wr_pilot:.2f} ({calls_pilot} calls) + full {wr_full:.2f} ({calls_full} calls)")
    print(line("comment recall (full only)", recall))
    print(line("diversity (local)", diversity))
    print(line("spearman (free)", spearman))
    print("-" * 78)
    print(f"  {'TOTAL':<34}${total:7.2f}   EUR {total * rate:7.2f}")
    cap = 50.0
    print(f"  {'$50 key cap':<34}{'fits ' + format(cap/total, '.2f') + ' runs' if total else '-':>20}")
    print("=" * 78)
    print("Notes:")
    print("- Generation is now ~{:.0f}% of spend (was ~5% pre-grounding): experts read the".format(gen / total * 100))
    print("  full paper and the leader re-sends it on each of its ~4 calls.")
    print("- Win-rate '--dimension overall' does NOT cut cost: one judge call always")
    print("  returns all dimensions; the flag only filters aggregation.")
    print("- Latency: one qwen homogeneous review took ~7 min (4 sequential LLM calls).")
    print("  210 reviews at concurrency 4 is a multi-hour generation stage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
