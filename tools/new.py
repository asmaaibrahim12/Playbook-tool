#!/usr/bin/env python3
"""Scaffold a new capability manifest.

Nobody should have to read a JSON Schema to add a capability. This writes a
file with every field already in place, in the order a builder reads them, with
a one-line note on each saying what it is for. Fill the TODOs, run the
validator, and it will tell you what is still missing.

    python3 tools/new.py receipt-matching --trunk data-and-docs
    python3 tools/validate.py
"""
import argparse
import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "capability.schema.json").read_text())
TRUNKS = SCHEMA["properties"]["metadata"]["properties"]["trunk"]["enum"]

TEMPLATE = """\
apiVersion: capability.taxfix.internal/v1
kind: Capability

metadata:
  name: {name}
  title: {title}
  trunk: {trunk}
  owner: "#trunk-{trunk}"          # the TEAM, not a person — people leave
  summary: TODO one sentence, under 240 characters
  lifecycle: experimental          # experimental | beta | stable | deprecated
  tags: []

# ─── 1. Does it do what I need? ──────────────────────────────────────────────
scope:
  does:
    - TODO something a caller can rely on
  does_not:
    - TODO an explicit non-goal
    # In practice this is the most-read field in the file. Be generous.

# ─── 2. Should I not use it at all? ──────────────────────────────────────────
build_your_own_if:
  - TODO a condition under which a team SHOULD build their own instead
  # Required. A catalogue that never says "don't use me" gets found out later.

# ─── 3. Does it work where I am? ─────────────────────────────────────────────
availability:
  markets:
    - market: DE                   # DE | UK | ES
      status: in-progress          # live | in-progress | not-supported
      obligation: TODO e.g. UStVA
      channel: TODO e.g. ELSTER
  # advice_boundary: uncomment where the regulatory line matters
  # advice_boundary:
  #   automated:
  #     - TODO what software may do alone
  #   requires_licensed_human:
  #     - TODO what must route to a licensed advisor
  #   basis: TODO e.g. §3 StBerG

# ─── 4. Is it good enough for my risk? ───────────────────────────────────────
evaluation:
  self_service: false              # can a consuming team run this eval unaided?
  method: TODO how someone proves this works, including the command to run
  eval_set_ref: ./evals/{name}/
  metrics:
    - name: TODO
      value: 0.0
      measured_on: TODO which set or population
      as_of: "{today}"
      source: assumed              # measured | assumed — be honest
  known_failure_modes:
    - TODO where it breaks
  human_fallback: TODO what happens below the caller's threshold

# ─── 5. What does it cost me? ────────────────────────────────────────────────
cost:
  unit: TODO e.g. per document processed
  amount_eur: 0.0
  measure: TODO cost per SUCCESSFUL outcome, not per call
  as_of: "{today}"
  source: assumed

# ─── 6. How do I call it? ────────────────────────────────────────────────────
interface:
  protocol: http                   # http | grpc | event | library | mcp
  entrypoint: TODO
  spec_ref: ./openapi/{name}.yaml  # referenced, never copied
  auth: TODO
  sdk: []

# ─── 7. Who else relies on it? ───────────────────────────────────────────────
consumers: []
  # - orchard: business            # self-serve | assisted | business
  #   market: DE
  #   since: "{today}"
  #   criticality: blocking        # blocking | important | convenience

# ─── 8. Who do I ask? ────────────────────────────────────────────────────────
support:
  channel: "#trunk-{trunk}"
  response_target: TODO e.g. 1 business day
  contribution: open               # open | review-required | closed
  contribution_guide: ./CONTRIBUTING.md
"""


def main():
    ap = argparse.ArgumentParser(description="Scaffold a capability manifest.")
    ap.add_argument("name", help="kebab-case identifier, e.g. receipt-matching")
    ap.add_argument("--trunk", choices=TRUNKS, required=True)
    ap.add_argument("--force", action="store_true", help="overwrite an existing file")
    a = ap.parse_args()

    out = ROOT / "capabilities" / f"{a.name}.yaml"
    if out.exists() and not a.force:
        print(f"{out.relative_to(ROOT)} already exists. Use --force to overwrite.",
              file=sys.stderr)
        return 1

    out.write_text(TEMPLATE.format(
        name=a.name,
        title=a.name.replace("-", " ").title(),
        trunk=a.trunk,
        today=datetime.date.today().isoformat(),
    ))

    print(f"Wrote {out.relative_to(ROOT)}\n")
    print("Next:")
    print("  1. Replace the TODOs. The comments say what each field is for.")
    print("  2. python3 tools/validate.py     — it will name anything still missing")
    print("  3. python3 tools/render.py       — regenerate the docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
