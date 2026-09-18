"""Example custom test tool a team would publish back into the catalog.

The factory pipeline calls this the same way locally and in CI:
    python eval_harness.py --baseline 0.80
"""
from __future__ import annotations

import argparse
import json
import sys


def f1(tp: int, fp: int, fn: int) -> float:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", type=float, default=0.80)
    args = p.parse_args()
    # Stand-in confusion matrix for the simulated fraud-ranker
    score = f1(tp=88, fp=7, fn=5)
    report = {"metric": "f1", "value": round(score, 4), "baseline": args.baseline, "gate": "pass" if score >= args.baseline else "fail"}
    print(json.dumps(report))
    return 0 if report["gate"] == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
