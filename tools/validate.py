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
    for metric in doc["evaluation"]["metrics"]:
        as_of = datetime.date.fromisoformat(str(metric["as_of"]))
        age = (today - as_of).days
        if age > MAX_METRIC_AGE_DAYS:
            problems.append(
                f"{name}: metric '{metric['name']}' is {age} days old "
                f"(limit {MAX_METRIC_AGE_DAYS}) — re-run the eval or drop the claim"
            )
    return problems


def check_placeholders(doc, name):
    """A scaffolded manifest should not pass until it has been filled in.
    Without this the whole loop breaks: tools/new.py writes TODOs, the
    validator says fine, and a half-written entry reaches the catalogue."""
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and "TODO" in node:
            found.append(path)

    walk(doc, "")
    if not found:
        return []
    shown = ", ".join(found[:4]) + (f" and {len(found) - 4} more" if len(found) > 4 else "")
    return [f"{name}: still scaffolded — TODO left at {shown}"]


def check_trust_rules(doc, name):
    """Rules that encode the operating model, not just the data shape."""
    problems = []
    meta, ss = doc["metadata"], doc["self_service"]
    level = ss["level"]

    # You cannot claim a level you have not earned. A team that cannot verify a
    # capability against its own data is still dependent on us, whatever the
    # integration looks like.
    if level in ("L2", "L3") and not ss["can_run_eval"]:
        problems.append(
            f"{name}: claims {level} but can_run_eval is false — a team that cannot "
            "verify it without us is not self-serving, whatever else is true"
        )

    # L3 means they extend it. That is impossible if we refuse their changes.
    if level == "L3" and ss["can_contribute"] != "open":
        problems.append(
            f"{name}: claims L3 but can_contribute is '{ss['can_contribute']}' — "
            "extending a capability means merging someone else's change"
        )

    # A capability serving several Orchards that refuses PRs is a service desk.
    orchards = {c["orchard"] for c in doc["consumers"]}
    if len(orchards) >= 2 and ss["can_contribute"] == "closed":
        problems.append(
            f"{name}: serves {len(orchards)} Orchards but can_contribute is 'closed' — "
            "shared capability must accept PRs or it becomes a queue"
        )

    # Stable means supported, and support that only we can give is not support.
    if meta["lifecycle"] == "stable" and not ss["can_run_eval"]:
        problems.append(
            f"{name}: lifecycle 'stable' requires self_service.can_run_eval=true"
        )

    # Anything another team's roadmap depends on needs a stated fallback.
    blocking = [c for c in doc["consumers"] if c.get("criticality") == "blocking"]
    if blocking and not doc["evaluation"].get("human_fallback"):
        problems.append(
            f"{name}: {len(blocking)} blocking consumer(s) but no human_fallback declared"
        )

    # Below L2 we should be able to say what would move it up.
    if level in ("L0", "L1") and not ss.get("to_reach_next_level"):
        problems.append(
            f"{name}: at {level} with no to_reach_next_level — if we cannot say what "
            "would raise it, it will stay there"
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
        problems += check_placeholders(doc, name)
        problems += check_freshness(doc, name, today)
        problems += check_trust_rules(doc, name)

    print(f"Validated {len(files)} manifest(s) in {cap_dir.name}/")
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for p in problems:
            print(f"  FAIL  {p}")
        return 1

    # Reported only once everything passes, on purpose. A self-service level is
    # a claim; until the rules above hold, counting it would be reporting what
    # teams wrote down rather than what they earned.
    levels = [yaml.safe_load(f.read_text())["self_service"]["level"] for f in files]
    at_l2 = sum(1 for l in levels if l in ("L2", "L3"))
    print(f"Self-service: {at_l2}/{len(files)} at L2 or above "
          f"({', '.join(sorted(levels))})")
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
