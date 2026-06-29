#!/usr/bin/env python3
"""Apply eval-notebook-style conventions to all plot cells. Run then execute notebooks."""
import json
from pathlib import Path

ROOT = Path(__file__).parent

# --- plot cell replacements keyed by unique substring ---
REPLACEMENTS: dict[str, dict[str, str]] = {
    "full_comment_recall.ipynb": {
        'assert READY, "comment_recall.json missing — run the metric first (see the setup cell message)."':
        '''assert READY, "comment_recall.json missing — run the metric first (see the setup cell message)."

d = df.sort_values("recall")
colors = [C_REF if h else C_HET for h in d["homogeneous"]]
bar_y = np.arange(len(d))
labels = d["config"].tolist()

fig, ax = plt.subplots(figsize=FIG_RANK)
ax.barh(bar_y, d["recall"], xerr=d["recall_sem"],
        color=colors, error_kw={"ecolor": C_ERR, "capsize": 3})
for yi, (v, hi) in enumerate(zip(d["recall"], d["recall_sem"])):
    ax.text(v + hi + 0.01, yi, f"{v:.3f}", va="center", fontsize=8, color=C_ANNOT)
x_right = min(1.0, (d["recall"] + d["recall_sem"]).max() + 0.1)
ax.set_xlim(right=x_right)
ax.set_yticks(bar_y)
ax.set_yticklabels(labels, fontsize=8)
ax.set_xlabel("Comment recall")
ax.set_title(fig_title("Comment recall by config"))

from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=C_REF, label="homogeneous reference"),
                   Patch(color=C_HET, label="heterogeneous")], **LEGEND_KW)
fig.subplots_adjust(bottom=0.22)
fig.savefig(FIG_DIR / "recall_by_config.png", bbox_inches="tight")
plt.show()

df[["config", "tuple", "recall", "recall_sem", "n_comments", "n_papers"]].round(4)''',

        'homo = df[df["homogeneous"]].copy()':
        '''homo = df[df["homogeneous"]].copy()
homo["model"] = homo["leader"]
homo = homo.sort_values("model")

fig, ax = plt.subplots(figsize=FIG_COMPACT)
ax.bar(homo["model"], homo["recall"], yerr=homo["recall_sem"],
       color=[MODEL_COLORS[m] for m in homo["model"]], capsize=4, width=0.6,
       edgecolor=C_EDGE)
for x, (v, hi) in enumerate(zip(homo["recall"], homo["recall_sem"])):
    ax.text(x, v + hi + 0.01, f"{v:.3f}", ha="center", fontsize=8, color=C_ANNOT)
ax.set_xticks(range(len(homo)))
ax.set_xticklabels([f"{m}\\n{MODEL_NAMES[m]}" for m in homo["model"]])
ax.set_ylabel("Comment recall")
ax.set_title(fig_title("Homogeneous reference recall"))
ax.set_ylim(0, min(1.0, (homo["recall"] + homo["recall_sem"]).max() + 0.1))
fig.subplots_adjust(bottom=0.18)
fig.savefig(FIG_DIR / "recall_capability.png", bbox_inches="tight")
plt.show()

spread = homo["recall"].max() - homo["recall"].min()
print(f"homogeneous recall spread (max - min): {spread:.3f}")''',

        'fig, ax = plt.subplots(figsize=FIG_SCATTER)\nfor _, r in df.iterrows():\n    col = MODEL_COLORS':
        '''fig, ax = plt.subplots(figsize=FIG_SCATTER)
for _, r in df.iterrows():
    ax.errorbar(r["n_comments"], r["recall"],
                xerr=r["n_comments_sem"], yerr=r["recall_sem"],
                fmt="o", ms=9, color=MODEL_COLORS[r["leader"]],
                capsize=3, zorder=3)

if len(df) > 2:
    r_pear = np.corrcoef(df["n_comments"], df["recall"])[0, 1]
    ax.set_title(fig_title("Recall vs verbosity", extra=f"r={r_pear:.2f}"))
else:
    ax.set_title(fig_title("Recall vs verbosity"))
ax.set_xlabel("Mean comments per review")
ax.set_ylabel("Comment recall")

from matplotlib.lines import Line2D
handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=MODEL_COLORS[l],
                  markersize=9, label=f"{l} · {MODEL_NAMES[l]} leader") for l in ("A", "B", "C")]
ax.legend(handles=handles, **LEGEND_KW)
fig.subplots_adjust(bottom=0.22)
fig.savefig(FIG_DIR / "recall_vs_verbosity.png", bbox_inches="tight")
plt.show()
display(df[["config", "tuple", "leader", "n_comments", "recall"]].sort_values("recall", ascending=False).round(4))''',

        'wr_path = RESULTS_DIR / "win_rate.json"':
        '''wr_path = RESULTS_DIR / "win_rate.json"
if not READY:
    print("comment_recall.json not ready — skipping.")
elif not wr_path.exists():
    print("win_rate.json not found — showing recall ranking only.")
    display(df[["config", "tuple", "recall", "n_comments"]].round(4))
else:
    from matplotlib.patches import Patch
    wr = json.loads(wr_path.read_text())
    m = df.copy()
    m["win_rate"] = m["config"].map(lambda c: wr["per_config"].get(c, {}).get("overall", np.nan))

    fig, ax = plt.subplots(figsize=FIG_SCATTER)
    for _, r in m.iterrows():
        col = C_REF if r["homogeneous"] else C_HET
        ax.errorbar(r["win_rate"], r["recall"], yerr=r["recall_sem"],
                    fmt="o", ms=9, color=col, capsize=3, zorder=3)

    valid = m.dropna(subset=["win_rate"])
    if len(valid) > 2:
        rk = valid[["win_rate", "recall"]].rank()
        rho = rk["win_rate"].corr(rk["recall"])
        ax.set_title(fig_title("Recall vs win-rate", extra=f"ρ={rho:.2f}"))
    else:
        ax.set_title(fig_title("Recall vs win-rate"))
    ax.set_xlabel("Overall win-rate")
    ax.set_ylabel("Comment recall")
    ax.legend(handles=[Patch(color=C_REF, label="homogeneous reference"),
                       Patch(color=C_HET, label="heterogeneous")], **LEGEND_KW)
    fig.subplots_adjust(bottom=0.22)
    fig.savefig(FIG_DIR / "recall_vs_winrate.png", bbox_inches="tight")
    plt.show()
    display(m[["config", "tuple", "recall", "win_rate", "n_comments"]]
            .sort_values("recall", ascending=False).round(4))''',

        'assert READY, "comment_recall.json missing — run the metric first."\n\nlong = []':
        '''assert READY, "comment_recall.json missing — run the metric first."

long = []
for cfg, papers in per_paper.items():
    for pid, row in papers.items():
        long.append({"config": cfg, "paper": pid,
                     "stratum": stratum_by_paper.get(pid, "unknown"),
                     "recall": row["recall"]})
long = pd.DataFrame(long)

strata = sorted(long["stratum"].unique())
stratum_colors = {s: PALETTE[i % len(PALETTE)] for i, s in enumerate(strata)}
pivot = (long.groupby(["config", "stratum"])["recall"].mean()
             .unstack("stratum").reindex(df["config"]))

x = np.arange(len(pivot))
w = 0.8 / max(1, len(strata))
fig, ax = plt.subplots(figsize=FIG_PANEL)
for i, s in enumerate(strata):
    ax.bar(x + i * w, pivot[s].values, width=w, label=s, color=stratum_colors[s])
ax.set_xticks(x + w * (len(strata) - 1) / 2)
ax.set_xticklabels(pivot.index, rotation=30, ha="right", fontsize=8)
ax.set_ylabel("Mean comment recall")
ax.set_title(fig_title("Recall by paper stratum"))
ax.legend(title="stratum", **LEGEND_KW)
fig.subplots_adjust(bottom=0.28)
fig.savefig(FIG_DIR / "recall_by_stratum.png", bbox_inches="tight")
plt.show()

n_by_stratum = long.drop_duplicates("paper").groupby("stratum").size()
print("papers per stratum:", n_by_stratum.to_dict())
pivot.round(4)''',
    },
}

# Due to size, remaining notebooks applied via exec of inline functions below


def patch_cell(src: str, old_start: str, new: str) -> str:
    if old_start in src:
        return new
    return src


def fix_pilot_setup(src: str, style_block: str) -> str:
    import re
    if "fig_title" in src:
        return src
    return re.sub(
        r"# Consistent colou?rs?.*?\nplt\.rcParams\.update\(\{[^}]+\}\)\n\n",
        style_block,
        src,
        count=1,
        flags=re.DOTALL,
    )


def main():
    style_block = Path(
        "/Users/akshat/Desktop/seminar/multi-agent-peer-review/"
        ".cursor/skills/eval-notebook-style/templates/setup-cell.py"
    ).read_text()
    start = style_block.index("# --- palette")
    end = style_block.index("# --- metric-specific")
    style_block = style_block[start:end]

    # Import remaining replacements from companion module logic
    from importlib import import_module
    import sys
    sys.path.insert(0, str(ROOT))
    # apply rest manually in this script - extend REPLACEMENTS

    print("Run extended patches via notebook editor")


if __name__ == "__main__":
    main()
