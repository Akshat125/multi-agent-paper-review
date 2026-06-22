"""Budget estimator for the homogeneous-vs-heterogeneous review experiments.

Standalone, stdlib-only. Prices each stage of the Successive-Halving protocol
(generation + LLM-as-judge metrics) from ``eval/prices.json`` and an empirical
per-role token profile measured from a real run trace
(``eval/outputs/20260622T103210Z/trace.jsonl``).

Run::

    python eval/estimate.py
    python eval/estimate.py --eur-per-usd 0.92

The cost of this study is dominated by Metric 1 (pairwise win-rate judging),
NOT by generation: ~30B-class open models generate a full multi-agent review
for well under one cent, while each judge call must re-read the paper.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
PRICES_PATH = EVAL_DIR / "prices.json"

# --------------------------------------------------------------------------- #
# Token model
# --------------------------------------------------------------------------- #
# Empirical per-role profile from the qwen3-8b homogeneous run on a 35.8k-char
# paper (eval/outputs/20260622T103210Z/trace.jsonl). The leader reads the full
# paper TWICE (initial plan + aggregation) and is the only input-heavy role;
# the three experts receive only a short task brief, not the full paper.
#
#   role         tokens_in   tokens_out   (paper was ~9.0k tokens / 35.8k chars)
#   leader          24310        2917
#   clarity           678        1915
#   experiments       664        2030
#   impact            542        1667
#
# Only the leader input scales with paper size (it contains the paper ~2x).
# We split the leader input into a paper-proportional part (~2 * paper_tokens)
# and a fixed remainder (expert outputs fed back + prompts).

CHARS_PER_TOKEN = 4.0
MEAN_PAPER_CHARS = 40_760          # eval_sample_30.json mean
MAX_PAPER_CHARS = 83_435           # worst case in the set

LEADER_PAPER_MULTIPLIER = 2.0      # paper appears ~twice in leader context
LEADER_FIXED_IN = 6_310            # 24310 - 2*9000 (expert outputs + prompts)
LEADER_OUT = 2_917

EXPERT_PROFILE = {                 # paper-size-independent (task brief only)
    "clarity": {"in": 678, "out": 1915},
    "experiments": {"in": 664, "out": 2030},
    "impact": {"in": 542, "out": 1667},
}

ROLES = ("leader", "clarity", "experiments", "impact")


def paper_tokens(chars: int) -> float:
    return chars / CHARS_PER_TOKEN


def role_tokens(role: str, p_tokens: float) -> tuple[float, float]:
    """(tokens_in, tokens_out) for one role on a paper of `p_tokens` tokens."""
    if role == "leader":
        return LEADER_PAPER_MULTIPLIER * p_tokens + LEADER_FIXED_IN, LEADER_OUT
    e = EXPERT_PROFILE[role]
    return float(e["in"]), float(e["out"])


# --------------------------------------------------------------------------- #
# Judge call token model (Metric 1 win-rate, ScholarPeer SxS)
# --------------------------------------------------------------------------- #
JUDGE_SYS_TOKENS = 1_200           # SxS system prompt
REVIEW_TOKENS = 1_350             # one final_review.md (~5.3k chars)
JUDGE_OUT_TOKENS = 2_000          # THOUGHT (5 dims) + JSON

# Recall (Metric 2) per (config, paper) unit, rough MARG 3-stage profile.
RECALL_IN_PER_UNIT = 16_000
RECALL_OUT_PER_UNIT = 2_750
RECALL_HUMAN_IN_PER_PAPER = 7_500   # cached human extraction, shared across configs
RECALL_HUMAN_OUT_PER_PAPER = 2_500


# --------------------------------------------------------------------------- #
# Prices
# --------------------------------------------------------------------------- #
def load_prices() -> dict[str, dict[str, float]]:
    raw = json.loads(PRICES_PATH.read_text(encoding="utf-8"))
    return {k: {"in": float(v["in"]), "out": float(v["out"])} for k, v in raw.items()}


PRICES = load_prices()


def price(model: str) -> dict[str, float]:
    if model not in PRICES:
        raise KeyError(f"no price for {model!r}")
    return PRICES[model]


def usd(model: str, t_in: float, t_out: float) -> float:
    p = price(model)
    return t_in / 1e6 * p["in"] + t_out / 1e6 * p["out"]


# --------------------------------------------------------------------------- #
# Stage costs
# --------------------------------------------------------------------------- #
def gen_cost_for_config(models: dict[str, str], p_tokens: float) -> float:
    """Generation cost of one (config, paper) run, role-priced."""
    total = 0.0
    for role in ROLES:
        t_in, t_out = role_tokens(role, p_tokens)
        total += usd(models[role], t_in, t_out)
    return total


def winrate_cost(
    n_configs: int,
    n_papers: int,
    judges: list[str],
    *,
    judge_paper_tokens: float,
    anchored: bool = False,
    orders: int = 2,
) -> tuple[float, int]:
    """Pairwise SxS judging cost. Returns (usd, n_calls).

    Full design: every unordered config pair, both orders, every judge, every paper.
    Anchored: each config vs a single anchor only (n_configs-1 pairs) -> cheaper,
    noisier ranking (useful only as a pilot pruning signal).
    orders: 2 = position-debiased (both A/B orders); 1 = single order.
    """
    n_pairs = (n_configs - 1) if anchored else len(list(combinations(range(n_configs), 2)))
    n_calls = n_pairs * n_papers * len(judges) * orders
    t_in = JUDGE_SYS_TOKENS + judge_paper_tokens + 2 * REVIEW_TOKENS
    cost = 0.0
    for _ in range(n_pairs * n_papers * orders):
        for j in judges:
            cost += usd(j, t_in, JUDGE_OUT_TOKENS)
    return cost, n_calls


def recall_cost(n_configs: int, n_papers: int, judge: str) -> float:
    units = n_configs * n_papers
    gen = usd(judge, RECALL_IN_PER_UNIT * units, RECALL_OUT_PER_UNIT * units)
    human = usd(judge, RECALL_HUMAN_IN_PER_PAPER * n_papers, RECALL_HUMAN_OUT_PER_PAPER * n_papers)
    return gen + human


# --------------------------------------------------------------------------- #
# Scenario definition
# --------------------------------------------------------------------------- #
@dataclass
class Scenario:
    name: str
    pool: dict[str, str]            # {A,B,C: slug}
    judges: list[str]               # default judge set (both stages unless overridden)
    judge_recall: str
    # design
    pilot_configs: int = 12
    pilot_papers: int = 5
    full_configs: int = 4
    full_papers: int = 25
    full_replicates: int = 1
    pilot_anchored: bool = False
    judge_truncate_paper: bool = True   # abstract+intro only in judge prompt
    recall_on_full_only: bool = True
    # stage-specific judge overrides (supervisor: 1 metric / lighter judging in pilot)
    pilot_judges: list[str] | None = None
    full_judges: list[str] | None = None
    pilot_orders: int = 2           # 2 = position-debiased; 1 = single order
    recall_in_pilot: bool = False   # supervisor: only ONE metric in stage 1
    notes: str = ""
    breakdown: dict = field(default_factory=dict)

    def judge_paper_tokens(self) -> float:
        if self.judge_truncate_paper:
            return 2_400  # abstract + intro
        return paper_tokens(MEAN_PAPER_CHARS)

    def compute(self) -> float:
        pmean = paper_tokens(MEAN_PAPER_CHARS)
        # --- generation -------------------------------------------------- #
        # Average a homogeneous run and a maximally-heterogeneous run as a
        # representative per-run generation cost (role mix barely matters since
        # generation is dominated by the leader's model).
        homo = {r: self.pool["A"] for r in ROLES}
        het = {"leader": self.pool["A"], "clarity": self.pool["B"],
               "experiments": self.pool["C"], "impact": self.pool["A"]}
        gen_homo = gen_cost_for_config(homo, pmean)
        gen_het = gen_cost_for_config(het, pmean)
        per_run = (gen_homo + gen_het) / 2

        pilot_runs = self.pilot_configs * self.pilot_papers
        full_runs = self.full_configs * self.full_papers * self.full_replicates
        gen_total = per_run * (pilot_runs + full_runs)

        # --- win-rate ---------------------------------------------------- #
        jpt = self.judge_paper_tokens()
        pilot_judges = self.pilot_judges or self.judges
        full_judges = self.full_judges or self.judges
        wr_pilot, n_pilot = winrate_cost(
            self.pilot_configs, self.pilot_papers, pilot_judges,
            judge_paper_tokens=jpt, anchored=self.pilot_anchored, orders=self.pilot_orders,
        )
        wr_full, n_full = winrate_cost(
            self.full_configs, self.full_papers, full_judges,
            judge_paper_tokens=jpt, anchored=False, orders=2,
        )
        wr_total = wr_pilot + wr_full

        # --- recall ------------------------------------------------------ #
        rc = recall_cost(self.full_configs, self.full_papers, self.judge_recall)
        if self.recall_in_pilot:
            rc += recall_cost(self.pilot_configs, self.pilot_papers, self.judge_recall)
        elif not self.recall_on_full_only:
            rc += recall_cost(3, self.pilot_papers, self.judge_recall)

        total = gen_total + wr_total + rc
        self.breakdown = {
            "generation_usd": gen_total,
            "per_run_usd": per_run,
            "n_gen_runs": pilot_runs + full_runs,
            "winrate_pilot_usd": wr_pilot,
            "winrate_full_usd": wr_full,
            "winrate_calls": n_pilot + n_full,
            "pilot_calls": n_pilot,
            "full_calls": n_full,
            "recall_usd": rc,
            "total_usd": total,
        }
        return total


# --------------------------------------------------------------------------- #
# Candidate portfolios
# --------------------------------------------------------------------------- #
# Pool = three ~30B-class open models from DIFFERENT families (the paper's
# heterogeneity variable). Judges = strong, out-of-suite, different families,
# none overlapping the pool family.
VALUE_POOL = {
    "A": "qwen/qwen3-32b",
    "B": "meta-llama/llama-3.3-70b-instruct",
    "C": "google/gemma-3-27b-it",
}

JUDGES_FRONTIER = ["openai/gpt-5", "anthropic/claude-sonnet-4.5"]
JUDGES_STRONG_MID = ["openai/gpt-5-mini", "google/gemini-2.5-flash"]
JUDGES_STRONG_MID3 = ["openai/gpt-5-mini", "google/gemini-2.5-flash", "anthropic/claude-haiku-4.5"]
JUDGES_BUDGET = ["deepseek/deepseek-v3.2", "openai/gpt-oss-120b"]


def scenarios() -> list[Scenario]:
    return [
        Scenario(
            name="S. Supervisor-aligned (1 metric in pilot)",
            pool=VALUE_POOL, judges=JUDGES_STRONG_MID, judge_recall="openai/gpt-5-mini",
            pilot_judges=["openai/gpt-5-mini"], pilot_anchored=True, pilot_orders=2,
            full_judges=JUDGES_STRONG_MID, recall_in_pilot=False,
            notes="Stage 1: win-rate ONLY, 1 judge, anchored-to-baselines. "
                  "Stage 2: 2 judges round-robin + recall (+ diversity/spearman, free).",
        ),
        Scenario(
            name="S2. Supervisor-aligned + frontier final judge",
            pool=VALUE_POOL, judges=JUDGES_STRONG_MID, judge_recall="openai/gpt-5-mini",
            pilot_judges=["openai/gpt-5-mini"], pilot_anchored=True, pilot_orders=2,
            full_judges=["openai/gpt-5", "google/gemini-2.5-flash"],
            notes="Cheap pilot; spend on a frontier judge ONLY in the final layer.",
        ),
        Scenario(
            name="A. Recommended (mid judges, truncated paper)",
            pool=VALUE_POOL, judges=JUDGES_STRONG_MID, judge_recall="openai/gpt-5-mini",
            recall_in_pilot=True,
            notes="2 strong judges, abstract+intro, full round-robin pilot, recall in BOTH stages.",
        ),
        Scenario(
            name="B. Recommended + replication (R=2 full stage)",
            pool=VALUE_POOL, judges=JUDGES_STRONG_MID, judge_recall="openai/gpt-5-mini",
            full_replicates=2,
            notes="Same as A but 2 replicates in full stage for variance estimates.",
        ),
        Scenario(
            name="C. Mid judges, FULL paper in judge prompt",
            pool=VALUE_POOL, judges=JUDGES_STRONG_MID, judge_recall="openai/gpt-5-mini",
            judge_truncate_paper=False,
            notes="No truncation; tests cost of feeding full paper to the judge.",
        ),
        Scenario(
            name="D. 3 mid judges (stronger bias guardrail)",
            pool=VALUE_POOL, judges=JUDGES_STRONG_MID3, judge_recall="openai/gpt-5-mini",
            notes="3 out-of-suite judge families instead of 2.",
        ),
        Scenario(
            name="E. Frontier judges (gpt-5 + claude-sonnet)",
            pool=VALUE_POOL, judges=JUDGES_FRONTIER, judge_recall="openai/gpt-5-mini",
            notes="Best judge quality; shows why frontier judges blow the budget.",
        ),
        Scenario(
            name="F. Frontier judges + anchored pilot",
            pool=VALUE_POOL, judges=JUDGES_FRONTIER, judge_recall="openai/gpt-5-mini",
            pilot_anchored=True,
            notes="Frontier judges but pilot uses anchored (vs-baseline) pairing only.",
        ),
        Scenario(
            name="G. Budget judges (deepseek + gpt-oss-120b)",
            pool=VALUE_POOL, judges=JUDGES_BUDGET, judge_recall="openai/gpt-oss-120b",
            judge_truncate_paper=False,
            notes="Cheapest credible out-of-suite judges, even with full paper.",
        ),
        Scenario(
            name="H. Single judge gpt-5 (truncated)  [violates P4]",
            pool=VALUE_POOL, judges=["openai/gpt-5"], judge_recall="openai/gpt-5-mini",
            notes="One frontier judge only. Cheaper than 2 judges but breaks the >=2-family guardrail.",
        ),
        Scenario(
            name="I. gpt-5 + gemini-2.5-flash (truncated)",
            pool=VALUE_POOL, judges=["openai/gpt-5", "google/gemini-2.5-flash"],
            judge_recall="openai/gpt-5-mini",
            notes="One frontier + one mid judge (P4-valid), paper truncated.",
        ),
    ]


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def fmt(usd_val: float, rate: float) -> str:
    return f"${usd_val:6.2f} / EUR {usd_val * rate:6.2f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eur-per-usd", type=float, default=0.92)
    args = ap.parse_args()
    rate = args.eur_per_usd

    print("=" * 96)
    print("EXPERIMENT BUDGET ESTIMATE  (USD list prices -> EUR @ %.2f)" % rate)
    print("Design: Successive Halving. Pilot 12 cfg x 5 papers -> promote 4 -> full 4 cfg x 25 papers")
    print("Pool (cheap, ~30B, 3 families): %s" % ", ".join(VALUE_POOL.values()))
    print("=" * 96)

    per_run_demo = (gen_cost_for_config({r: VALUE_POOL["A"] for r in ROLES},
                                        paper_tokens(MEAN_PAPER_CHARS)))
    print(f"\nSanity: one full multi-agent review (All-{VALUE_POOL['A']}, mean paper) "
          f"= {per_run_demo*100:.3f} US-cents / {per_run_demo*rate*100:.3f} EUR-cents")
    print(f"        worst-case paper ({MAX_PAPER_CHARS} chars) leader-in scales accordingly.\n")

    rows = []
    for sc in scenarios():
        total = sc.compute()
        rows.append((sc, total))

    header = f"{'scenario':<48}{'gen':>11}{'win-rate':>12}{'recall':>10}{'TOTAL (EUR)':>14}"
    print(header)
    print("-" * len(header))
    for sc, total in rows:
        b = sc.breakdown
        wr = b["winrate_pilot_usd"] + b["winrate_full_usd"]
        flag = ""
        eur = total * rate
        if eur <= 25:
            flag = "  <= 25 OK"
        elif eur <= 50:
            flag = "  <= 50 (no buffer)"
        else:
            flag = "  OVER 50"
        print(f"{sc.name:<48}"
              f"{b['generation_usd']*rate:>10.2f}"
              f"{wr*rate:>12.2f}"
              f"{b['recall_usd']*rate:>10.2f}"
              f"{eur:>13.2f}{flag}")

    print("\nDetail (USD), scenario S (supervisor-aligned):")
    sc = rows[0][0]
    b = sc.breakdown
    print(f"  generation   : {b['generation_usd']:.2f}  ({b['n_gen_runs']} runs @ {b['per_run_usd']*100:.3f} c/run)")
    print(f"  win-rate pilot: {b['winrate_pilot_usd']:.2f}  ({b['pilot_calls']} judge calls)")
    print(f"  win-rate full : {b['winrate_full_usd']:.2f}  ({b['full_calls']} judge calls)")
    print(f"  recall (final): {b['recall_usd']:.2f}")
    print(f"  TOTAL        : ${b['total_usd']:.2f}  =  EUR {b['total_usd']*rate:.2f}")
    print("\nNote: list prices; OpenRouter often routes cheaper. Judge output tokens dominate")
    print("once the paper is truncated, so capping THOUGHT length is the next lever.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
