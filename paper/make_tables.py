"""Generate every LaTeX table and numeric macro from results/."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS, TABLES = ROOT / "results", ROOT / "paper" / "tables"
LABEL = {"rule_based": "rule-based SOP", "react": "ReAct loop",
         "reflection": "reflection", "transactional": "finality gate",
         "planner": "planner (this paper)"}
ORDER = ["rule_based", "reflection", "react", "transactional", "planner"]


def load(name):
    return json.loads((RESULTS / f"{name}.json").read_text())


def pct(x, p=1):
    return f"{x*100:.{p}f}"


def money(c, p=2):
    return f"{c/100:,.{p}f}"


def ci(entry, scale=0.01, p=2):
    return (f"{entry['point']*scale:.{p}f} "
            f"[{entry['low']*scale:.{p}f}, {entry['high']*scale:.{p}f}]")


def table_main(e1):
    rows = {r["policy"]: r for r in e1["policies"]}
    out = [r"\begin{tabular}{lrrrr}", r"\toprule",
           r"policy & exact (\%) & mean gap (\$) & paired (\$) & pre-det.\ (\%) \\",
           r"\midrule"]
    for name in ORDER:
        r = rows[name]
        bold = r"\bfseries " if name == "planner" else ""
        out.append(
            f"{bold}{LABEL[name]} & {ci(r['ci']['exact_rate'], 100, 1)} & "
            f"{ci(r['ci']['mean_excess'])} & {money(r['paired']['mean_pair_excess'])} & "
            f"{pct(r['premature_rate'])} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def table_paired(e1):
    out = [r"\begin{tabular}{lrr}", r"\toprule",
           r"comparison & mean gap (\$) & exact rate (pp) \\", r"\midrule"]
    for name in ORDER[:-1]:
        d = e1["planner_vs"][name]
        g, e = d["mean_gap"], d["exact_rate"]
        out.append(f"planner $-$ {LABEL[name]} & {ci(g)} & "
                   f"{ci(e, 100, 1)} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def table_ablation(e2):
    out = [r"\begin{tabular}{lrrr}", r"\toprule",
           r"variant & exact (\%) & mean gap (\$) & cost of removal (\$) \\",
           r"\midrule"]
    for r in e2["rows"]:
        delta = "---"
        if "vs_planner_mean_gap" in r:
            delta = ci(r["vs_planner_mean_gap"])
        out.append(f"{r['variant'].replace('_', ' ')} & {pct(r['exact_rate'])} & "
                   f"{money(r['mean_excess'])} & {delta} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def table_shield(e5):
    rows = {r["policy"]: r for r in e5["rows"]}
    out = [r"\begin{tabular}{llrrrr}", r"\toprule",
           r"policy & shield & exact (\%) & mean gap (\$) & paired (\$) & pre-det.\ (\%) \\",
           r"\midrule"]
    for subj in ("optimistic", "majority", "react", "eager"):
        for key, lbl in ((subj, "none"), (f"{subj}+expected", "expected"),
                         (f"{subj}+downside", "downside")):
            if key not in rows:
                continue
            r = rows[key]
            name = subj if lbl == "none" else ""
            out.append(f"{name} & {lbl} & {pct(r['exact_rate'])} & "
                       f"{money(r['mean_excess'])} & {money(r['paired'])} & "
                       f"{pct(r['premature_rate'])} \\\\")
        out.append(r"\addlinespace")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def table_transfer(e4):
    out = [r"\begin{tabular}{llrrr}", r"\toprule",
           r"split & prior & gate (\$) & planner (\$) & difference (\$) \\",
           r"\midrule"]
    seen = set()
    for r in e4["rows"]:
        if (r["split"], r["prior"]) in seen:
            continue
        seen.add((r["split"], r["prior"]))
        out.append(f"{r['split']} & {r['prior']} & {money(r['gate'])} & "
                   f"{money(r['planner'])} & {ci(r['difference'])} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def table_archetype(e1):
    """Where the margin over the gate comes from, by situation."""
    rows = {r["policy"]: r for r in e1["policies"]}
    gate, plan = rows["transactional"]["by_archetype"], rows["planner"]["by_archetype"]
    keys = sorted(set(gate) & set(plan),
                  key=lambda a: plan[a]["mean_excess"] - gate[a]["mean_excess"])
    out = [r"\begin{tabular}{lrrr}", r"\toprule",
           r"archetype & gate (\$) & planner (\$) & difference (\$) \\", r"\midrule"]
    for a in keys:
        d = plan[a]["mean_excess"] - gate[a]["mean_excess"]
        out.append(f"{a.replace('_', ' ')} & {money(gate[a]['mean_excess'])} & "
                   f"{money(plan[a]['mean_excess'])} & {money(d)} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def macros(e1, e2, e3, e4, e5):
    rows = {r["policy"]: r for r in e1["policies"]}
    p, g = rows["planner"], rows["transactional"]
    vs = e1["planner_vs"]["transactional"]
    ab = {r["variant"]: r for r in e2["rows"]}
    sh = {r["policy"]: r for r in e5["rows"]}
    defs = {
        "nTasks": e1["corpus"]["n_tasks"],
        "nPairs": e1["corpus"]["n_pairs"],
        "nSeeds": len(e1["seeds"]),
        "nGrades": f"{e1['n_grades']:,}",
        "bootReplicates": f"{e1['bootstrap']['replicates']:,}",
        "bootUnits": p["ci"]["exact_rate"]["n_units"],
        "planExact": pct(p["exact_rate"]),
        "planGap": money(p["mean_excess"]),
        "planGapCI": ci(p["ci"]["mean_excess"]),
        "gateExact": pct(g["exact_rate"]),
        "gateGap": money(g["mean_excess"]),
        "gateGapCI": ci(g["ci"]["mean_excess"]),
        "vsGateGap": ci(vs["mean_gap"]),
        "vsGateExact": ci(vs["exact_rate"], 100, 1),
        "planPassK": ci(p["ci"]["pass_all"], 100, 1),
        "gatePassK": ci(g["ci"]["pass_all"], 100, 1),
        "reactPassK": ci(rows["react"]["ci"]["pass_all"], 100, 1),
        "costSettings": e3["n_settings"],
        "costPlannerBetter": e3["planner_better"],
        "ablShield": ci(ab["no-shield"]["vs_planner_mean_gap"]) if "no-shield" in ab else "0",
        "ablVoi": ci(ab["no-voi"]["vs_planner_mean_gap"]) if "no-voi" in ab else "0",
        "ablPrior": ci(ab["no-conditional-prior"]["vs_planner_mean_gap"]),
        "ablRule": ci(ab["fixed-escalate"]["vs_planner_mean_gap"]),
        "settleMarginal": f"{e1['prior']['settle_rate']:.2f}",
        "settleLate": f"{e1['prior']['settle_rate_after']['600']:.2f}",
        "optPrem": pct(sh["optimistic"]["premature_rate"]),
        "optShieldPrem": pct(sh["optimistic+downside"]["premature_rate"]),
        "optPaired": money(sh["optimistic"]["paired"]),
        "optShieldPaired": money(sh["optimistic+downside"]["paired"]),
        "optShieldGap": money(sh["optimistic+downside"]["mean_excess"]),
        "optGap": money(sh["optimistic"]["mean_excess"]),
        "transferHidden": ci(next(r for r in e4["rows"]
                                  if r["split"] == "hidden"
                                  and r["prior"] == "fitted on public")["difference"]),
        "wrongPrior": money(next(r for r in e4["rows"]
                                 if r["split"] == "hidden"
                                 and r["prior"] == "deliberately wrong")["planner"]),
    }
    return "\n".join([r"% Generated by paper/make_tables.py -- do not edit."] +
                     [rf"\newcommand{{\{k}}}{{{v}}}" for k, v in defs.items()])


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    e1, e2, e3 = load("e1_main"), load("e2_ablation"), load("e3_costs")
    e4, e5 = load("e4_transfer"), load("e5_shield")
    (TABLES / "main.tex").write_text(table_main(e1))
    (TABLES / "paired.tex").write_text(table_paired(e1))
    (TABLES / "ablation.tex").write_text(table_ablation(e2))
    (TABLES / "shield.tex").write_text(table_shield(e5))
    (TABLES / "transfer.tex").write_text(table_transfer(e4))
    (TABLES / "archetype.tex").write_text(table_archetype(e1))
    (ROOT / "paper" / "numbers.tex").write_text(macros(e1, e2, e3, e4, e5) + "\n")
    for f in sorted(TABLES.glob("*.tex")):
        print(f"  {f.relative_to(ROOT)}")
    print("  paper/numbers.tex")


if __name__ == "__main__":
    main()
