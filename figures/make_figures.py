"""Regenerate every figure from results/. No number is typed in here."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS, OUT = ROOT / "results", ROOT / "figures"
INK, ACCENT, MUTED, GOOD = "#1b1b1b", "#b3411b", "#8a8a8a", "#1f5f8b"
plt.rcParams.update({
    "font.size": 8.5, "axes.edgecolor": INK, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})
LABEL = {"rule_based": "rule-based SOP", "react": "ReAct loop",
         "reflection": "reflection", "transactional": "finality gate",
         "planner": "planner"}


def load(name):
    return json.loads((RESULTS / f"{name}.json").read_text())


def fig1_comparison():
    """Paired differences only. The marginal intervals are in the table, and
    plotting them alongside invited the reader to compare two things that
    overlap almost entirely and mean less than the paired number does."""
    d = load("e1_main")
    comps = d["planner_vs"]
    order = [n for n in ["rule_based", "reflection", "react", "transactional"]
             if n in comps]

    fig, ax = plt.subplots(figsize=(7.2, 2.2))
    for i, name in enumerate(order):
        c = comps[name]["mean_gap"]
        close = name == "transactional"
        colour = GOOD if close else MUTED
        ax.plot([c["low"] / 100, c["high"] / 100], [i, i], lw=2.4, color=colour,
                solid_capstyle="round")
        ax.plot([c["point"] / 100], [i], "o", ms=5, color=colour)
        ax.annotate(f"${c['point']/100:,.2f}", (c["point"] / 100, i),
                    textcoords="offset points", xytext=(0, 7), ha="center",
                    fontsize=7, color=colour)
    ax.axvline(0, lw=1.0, color=ACCENT, ls="--")
    ax.set_yticks(list(range(len(order))), [f"vs {LABEL[n]}" for n in order])
    ax.invert_yaxis()
    ax.set_ylim(len(order) - 0.4, -0.9)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlim(-400, 4)
    ax.set_xlabel("planner minus baseline, mean position gap ($), shared task resample")
    ax.set_title("Every interval lies below zero, including against the "
                 "strongest baseline", loc="left", fontsize=9)
    fig.savefig(OUT / "fig1_comparison.pdf")
    plt.close(fig)
    print("  fig1_comparison.pdf")


def fig2_costs():
    d = load("e3_costs")
    rows = d["rows"]
    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    xs = range(len(rows))
    for i, r in enumerate(rows):
        c = r["difference"]
        ax.plot([i, i], [c["low"] / 100, c["high"] / 100], lw=1.8, color=GOOD,
                solid_capstyle="round")
        ax.plot([i], [c["point"] / 100], "o", ms=3, color=GOOD)
    ax.axhline(0, lw=0.9, color=ACCENT, ls="--")
    ax.set_xticks(list(xs),
                  [f"{r['cogs_rate']:.1f}/{r['dispute_cost']//100}/{r['escalation_cost']//100}"
                   for r in rows], rotation=90, fontsize=5.5)
    ax.set_xlabel("cost of goods / dispute fee / escalation cost", labelpad=2)
    ax.set_ylabel("planner minus gate ($)")
    ax.set_title(f"The advantage holds in {d['planner_better']} of {d['n_settings']} "
                 f"cost settings; every interval is below zero",
                 loc="left", fontsize=9)
    fig.savefig(OUT / "fig2_costs.pdf")
    plt.close(fig)
    print("  fig2_costs.pdf")


def fig3_shield():
    d = load("e5_shield")
    rows = {r["policy"]: r for r in d["rows"]}
    subjects = ["optimistic", "majority", "react", "eager"]
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    for subj in subjects:
        pts = [(rows[k]["mean_excess"] / 100, rows[k]["premature_rate"] * 100)
               for k in (subj, f"{subj}+expected", f"{subj}+downside") if k in rows]
        moves = abs(pts[-1][1] - pts[0][1]) > 1 or abs(pts[-1][0] - pts[0][0]) > 5
        colour = GOOD if moves else MUTED
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o", ms=4.5, lw=1.2,
                color=colour, zorder=3 if moves else 2)
        ax.annotate(subj, pts[0], textcoords="offset points", xytext=(6, 5),
                    fontsize=7.5, color=colour)
        if moves:
            for (x, y), lbl in zip(pts[1:], ("expected", "downside")):
                ax.annotate(lbl, (x, y), textcoords="offset points", xytext=(6, -3),
                            fontsize=7, color=colour)
    ax.set_xlabel("mean position gap ($), worse to the right")
    ax.set_ylabel("irreversible action before\nthe outcome existed (%)")
    ax.set_ylim(-4, 74)
    ax.set_title("The shield moves the policy that was gambling, and leaves the "
                 "others where they were", loc="left", fontsize=9)
    fig.savefig(OUT / "fig3_shield.pdf")
    plt.close(fig)
    print("  fig3_shield.pdf")


def main():
    OUT.mkdir(exist_ok=True)
    fig1_comparison()
    fig2_costs()
    fig3_shield()


if __name__ == "__main__":
    main()
