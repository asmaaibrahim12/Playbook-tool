#!/usr/bin/env python3
"""CI gate. A capability that ships without a valid manifest fails the build.

This is the whole answer to "Notion docs go stale": staleness stops being a
discipline problem and becomes a failing pipeline.

Usage: python3 tools/validate.py [capabilities_dir]
Exit code 1 on any violation.
"""
import json
import sys
import pathlib
import datetime

import yaml
import jsonschema

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "capability.schema.json").read_text())

# Freshness policy: a metric older than this is treated as unproven.
MAX_METRIC_AGE_DAYS = 180


def check_freshness(doc, name, today):
    """Schema validity is not enough — a manifest can be well-formed and stale."""
    problems = []
    for metric in doc["spec"]["evaluation"]["metrics"]:
        as_of = datetime.date.fromisoformat(str(metric["as_of"]))
        age = (today - as_of).days
        if age > MAX_METRIC_AGE_DAYS:
            problems.append(
                f"{name}: metric '{metric['name']}' is {age} days old "
                f"(limit {MAX_METRIC_AGE_DAYS}) — re-run the eval or drop the claim"
            )
    return problems


def check_trust_rules(doc, name):
    """Rules that encode the operating model, not just the data shape."""
    problems = []
    spec = doc["spec"]
    meta = doc["metadata"]

    # A stable capability whose eval cannot be run by its consumers makes the
    # Trunk the sole arbiter of whether it works. That is a bottleneck for trust.
    if meta["lifecycle"] == "stable" and not spec["evaluation"]["self_service"]:
        problems.append(
            f"{name}: lifecycle 'stable' requires evaluation.self_service=true — "
            "consumers must be able to verify it without asking the Trunk"
        )

    # A capability with consumers in 2+ Orchards that is still closed to
    # contribution contradicts the inner-source model.
    orchards = {c["orchard"] for c in spec["consumers"]}
    if len(orchards) >= 2 and spec["support"]["contribution"] == "closed":
        problems.append(
            f"{name}: serves {len(orchards)} Orchards but contribution is 'closed' — "
            "shared capability must accept PRs or it becomes a queue"
        )

    # Blocking consumers deserve a stated fallback.
    blocking = [c for c in spec["consumers"] if c.get("criticality") == "blocking"]
    if blocking and not spec["evaluation"].get("human_fallback"):
        problems.append(
            f"{name}: {len(blocking)} blocking consumer(s) but no human_fallback declared"
        )

    return problems


def main():
    cap_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "capabilities"
    today = datetime.date.today()
    files = sorted(cap_dir.glob("*.yaml"))

    if not files:
        print(f"No manifests found in {cap_dir}", file=sys.stderr)
        return 1

    problems = []
    for path in files:
        doc = yaml.safe_load(path.read_text())
        name = path.stem
        try:
            jsonschema.validate(doc, SCHEMA)
        except jsonschema.ValidationError as e:
            loc = ".".join(str(p) for p in e.absolute_path) or "(root)"
            problems.append(f"{name}: schema violation at {loc}: {e.message}")
            continue
        problems += check_freshness(doc, name, today)
        problems += check_trust_rules(doc, name)

    print(f"Validated {len(files)} manifest(s) in {cap_dir.name}/")
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for p in problems:
            print(f"  FAIL  {p}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
