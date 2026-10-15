"""Assignment 1, Parts B to D: build the tables in reports/LAB_01.json from your runs. This file is yours.

Read every trace in runs/ and the comments in the tracker, decide each run's
success with your eval/check_triage.check, and compute the `results` entry for
each way (direct, workflow, agent, hybrid) and the computed fields of `analysis`.
Write them into reports/LAB_01.json and leave every other field (part0,
worst_case, verdict) as you set it. Every field is defined in checks/FORMATS.md,
section 7. The checker recomputes the counts and means the same way, so compute
them here, from the traces, never by hand.

    python -m eval.summarize
"""

import json
import math
from collections import Counter
from pathlib import Path

import yaml

from eval.check_triage import check
from harness import ROOT
from harness.tracker import Tracker

WAYS = ("direct", "workflow", "agent", "hybrid")
FREE_BACKENDS = ("never-stops",)


def load_runs(root: Path) -> list[dict]:
    """One dict per finished evaluation run on the real model, with what the report needs."""
    answers = yaml.safe_load((root / "fixtures" / "answers.yaml").read_text())["eval"]
    tracker = Tracker(root)
    runs = []
    for path in sorted((root / "runs").glob("*.jsonl")):
        if path.name.startswith("_"):
            continue
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        start = rows[0]
        if start["type"] != "run_start" or start["backend"] in FREE_BACKENDS or start["issue"] not in answers:
            continue
        if not any(r["type"] == "run_end" for r in rows):
            continue  # unfinished
        calls = [r for r in rows if r["type"] == "model_call"]
        end = next(r for r in rows if r["type"] == "end")
        runs.append({
            "way": start["way"], "issue": start["issue"], "sweep": start["sweep"],
            "passed": check(tracker, start["run_id"], start["issue"], answers[start["issue"]]),
            "prompt": sum(c["usage"]["prompt_tokens"] for c in calls),
            "output": sum(c["usage"]["output_tokens"] for c in calls),
            "cached": sum(c["usage"]["cache_read_input_tokens"] for c in calls),
            "cost": sum(c["cost_usd"] or 0 for c in calls),  # an unpriced call counts 0
            "elapsed": next(r for r in rows if r["type"] == "run_end")["elapsed_s"],
            "tools": [r["name"] for r in rows if r["type"] == "tool_call"],
            "prompts_by_call": [c["usage"]["prompt_tokens"] for c in calls],
            "ended": end["terminal_reason"],
        })
    return runs


def mean(values):
    return sum(values) / len(values)


def percentile(values, p):
    """Nearest rank."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p / 100 * len(ordered)) - 1)]


def way_entry(runs: list[dict], issues: list[int]) -> dict:
    per_issue = {str(i): sum(r["passed"] for r in runs if r["issue"] == i) for i in issues}
    by_sweep = Counter()
    for r in runs:
        by_sweep[r["sweep"]] += r["passed"]
    return {
        "runs": len(runs),
        "passes": sum(r["passed"] for r in runs),
        "per_issue": per_issue,
        "sweep_min": min(by_sweep.values()),
        "sweep_max": max(by_sweep.values()),
        "all_ten": sum(1 for i in issues
                       if sum(r["issue"] == i for r in runs) >= 10
                       and per_issue[str(i)] == sum(r["issue"] == i for r in runs)),
        "mean_prompt_tokens": mean([r["prompt"] for r in runs]),
        "mean_output_tokens": mean([r["output"] for r in runs]),
        "mean_cached_tokens": mean([r["cached"] for r in runs]),
        "p50_latency_s": percentile([r["elapsed"] for r in runs], 50),
        "p95_latency_s": percentile([r["elapsed"] for r in runs], 95),
        "mean_cost_usd": mean([r["cost"] for r in runs]),
        "mean_tool_calls": mean([len(r["tools"]) for r in runs]),
        "max_tool_calls": max(len(r["tools"]) for r in runs),
    }


def analysis_fields(results: dict, runs_by_way: dict) -> dict:
    out = {}
    d, w, a = results.get("direct"), results.get("workflow"), results.get("agent")
    if d and a:
        out["ratio_agent_over_direct_tokens"] = (
            (a["mean_prompt_tokens"] + a["mean_output_tokens"]) / (d["mean_prompt_tokens"] + d["mean_output_tokens"]))
    if w and a:
        m = a["mean_cost_usd"] / w["mean_cost_usd"]
        issues = list(w["per_issue"])
        f = sum(1 for i in issues if w["per_issue"][i] < 5 and a["per_issue"][i] >= 5) / len(issues)
        c = w["mean_cost_usd"]
        out.update({"m_agent_over_workflow_cost": m, "f": f, "workflow_cost": c,
                    "all_agent_cost": c * m, "blended_cost": c * ((1 - f) + f * m)})
    if a:
        sequences = Counter(tuple(r["tools"]) for r in runs_by_way["agent"])
        out["path_entropy"] = {"distinct_sequences": len(sequences),
                               "top3_share": sum(n for _, n in sequences.most_common(3)) / a["runs"]}
    if "hybrid" in results:
        out["hybrid_handoffs"] = sum(r["ended"] != "completed" for r in runs_by_way["hybrid"])
    return out


def measured_worst_case(agent_runs: list[dict]) -> dict:
    """F and A as checks/FORMATS.md section 4 defines them. Printed for you; worst_case is yours to set."""
    firsts = [r["prompts_by_call"][0] for r in agent_runs]
    steps = [b - a for r in agent_runs for a, b in zip(r["prompts_by_call"], r["prompts_by_call"][1:])]
    return {"F": mean(firsts), "A": mean(steps)}


def main(root: Path = ROOT) -> None:
    report_path = root / "reports" / "LAB_01.json"
    report = json.loads(report_path.read_text())
    answers = yaml.safe_load((root / "fixtures" / "answers.yaml").read_text())["eval"]
    runs = load_runs(root)
    runs_by_way = {way: [r for r in runs if r["way"] == way] for way in WAYS}
    for way, way_runs in runs_by_way.items():
        if way_runs:
            report["results"][way] = way_entry(way_runs, sorted(answers))
            print(f"{way}: {len(way_runs)} runs, {report['results'][way]['passes']} passes")
    measured = {w: report["results"][w] for w in WAYS if runs_by_way[w]}
    report["analysis"].update(analysis_fields(measured, runs_by_way))
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    if runs_by_way["agent"]:
        print("measured for worst_case (set it yourself):", measured_worst_case(runs_by_way["agent"]))


if __name__ == "__main__":
    main()
