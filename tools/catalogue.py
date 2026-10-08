#!/usr/bin/env python3
"""The agent surface over the same manifests humans read.

Exposes four tools, shaped as an MCP server would expose them. The MCP spec of
28 July 2026 is stateless request/response, so this runs as an ordinary HTTP
service.

ONE source (capabilities/*.yaml), TWO surfaces: the docs a human reads and the
index an agent queries are the same bytes.

Usage:
  python3 tools/catalogue.py search "extract data from an invoice"
  python3 tools/catalogue.py describe document-extraction
  python3 tools/catalogue.py can-i "file an income tax return" --orchard business --market DE
  python3 tools/catalogue.py consumers-of income-tax-return-assembly
"""
import argparse
import os
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_all(cap_dir=None):
    cap_dir = cap_dir or ROOT / "capabilities"
    return [yaml.safe_load(p.read_text()) for p in sorted(cap_dir.glob("*.yaml"))]


def _tokens(text):
    return set(re.findall(r"[a-z]{3,}", text.lower()))


STOP = _tokens("the and for with from that this you your can does not able into")


def tool_search(query, docs):
    """Rank capabilities against a natural-language need."""
    q = _tokens(query) - STOP
    results = []
    for d in docs:
        m, s = d["metadata"], d
        haystack = " ".join([
            m["name"], m.get("title", ""), m["summary"],
            " ".join(m.get("tags", [])),
            " ".join(s["scope"]["does"]),
        ])
        hits = q & (_tokens(haystack) - STOP)
        if not hits:
            continue
        # A capability that explicitly does NOT do the thing is still a useful
        # answer — it saves the builder from trying.
        excluded = q & (_tokens(" ".join(s["scope"]["does_not"])) - STOP)
        results.append({
            "name": m["name"],
            "title": m.get("title", m["name"]),
            "trunk": m["trunk"],
            "lifecycle": m["lifecycle"],
            "summary": m["summary"].strip(),
            "score": len(hits),
            "matched_on": sorted(hits),
            "caution": sorted(excluded) or None,
        })
    return sorted(results, key=lambda r: -r["score"])


def tool_describe(name, docs):
    for d in docs:
        if d["metadata"]["name"] == name:
            return d
    return {"error": f"no capability named '{name}'"}


def tool_can_i(need, orchard, market, docs):
    """The question a builder actually asks: can the platform already do this
    for my Orchard in my market, or do I build it myself?

    The matcher is lexical overlap, not semantics. It cannot tell the
    difference between a capability that does the thing and one that merely
    uses the same words, so this tool reports its own confidence rather than
    asserting.
    """
    ranked = tool_search(need, docs)
    if not ranked:
        return {
            "answer": "no-capability-found",
            "guidance": "Nothing in the catalogue matches. Raise it in the Trunk "
                        "channel before building — but you are not blocked.",
        }
    top = ranked[0]
    tied = [r["name"] for r in ranked[1:] if r["score"] == top["score"]]

    # A single weak token, or a tie, means the matcher guessed. Say so instead
    # of naming a winner.
    if top["score"] < 2 or tied:
        return {
            "answer": "no-confident-match",
            "candidates": [r["name"] for r in ranked[:3]],
            "matcher": "lexical overlap on does/summary/tags — not semantic",
            "guidance": "The catalogue found overlapping words but cannot tell "
                        "whether any of these does what you asked. Read their "
                        "'does' and 'does_not' before assuming, and if none fits, "
                        "raise it in the Trunk channel.",
        }
    full = tool_describe(top["name"], docs)
    juris = {j["market"]: j for j in full["availability"]["markets"]}
    j = juris.get(market)

    uses_it_now = [c for c in full["consumers"]
                   if c["orchard"] == orchard and c.get("market") == market]

    if j is None:
        verdict, guidance = "not-available-in-market", (
            f"{top['name']} exists but declares no support for {market}."
        )
    elif j["status"] == "live" and uses_it_now:
        verdict, guidance = "available", (
            f"Use {top['name']}. Entrypoint: "
            f"{full['spec']['interface']['entrypoint']}"
        )
    elif j["status"] == "live":
        # Live in the market, but THIS Orchard is not yet a consumer. That is
        # the most dangerous answer to get wrong: a flat "yes" sends a builder
        # into an integration that will fail on a scope exclusion.
        verdict, guidance = "live-but-check-scope", (
            f"{top['name']} is live in {market}, but the {orchard} Orchard is not "
            f"currently a consumer. Read does_not before integrating — if your "
            f"case is excluded, this is a platform gap to raise with "
            f"{full['metadata']['owner']}, not something to rebuild."
        )
    elif j["status"] == "in-progress":
        verdict, guidance = "in-progress", (
            f"{top['name']} is being built for {market}. Talk to "
            f"{full['metadata']['owner']} before starting your own — "
            f"contribution is '{full['spec']['support']['contribution']}'."
        )
    else:
        verdict, guidance = "not-supported", (
            f"{top['name']} explicitly does not support {market}."
        )

    # Two different kinds of claim, kept apart on purpose. Which capability you
    # meant is a GUESS the matcher made from word overlap. Whether that
    # capability is available in your market is a FACT the manifest declares.
    return {
        "match": {
            "capability": top["name"],
            "how": "guess — lexical overlap on does/summary/tags, not semantic",
            "other_candidates": [r["name"] for r in ranked[1:3]] or None,
            "verify": "Confirm this is the capability you meant by reading "
                      "does / does_not below. If none of the candidates does "
                      "what you asked, the catalogue has no answer for you.",
        },
        "does": full["scope"]["does"],
        "does_not": full["scope"]["does_not"],
        "if_that_is_the_right_capability": {
            "market_status": verdict,
            "guidance": guidance,
            "market_note": (j or {}).get("notes"),
            "your_orchard_already_uses_it": bool(uses_it_now),
            "build_your_own_if": full["build_your_own_if"],
            "evaluation_self_service": full["evaluation"]["self_service"],
            "owner": full["metadata"]["owner"],
        },
    }


def tool_consumers_of(name, docs):
    """Which teams depend on this, read off the manifests."""
    d = tool_describe(name, docs)
    if "error" in d:
        return d
    consumers = d["consumers"]
    return {
        "capability": name,
        "orchard_count": len({c["orchard"] for c in consumers}),
        "market_count": len({c.get("market") for c in consumers if c.get("market")}),
        "blocking_for": [f"{c['orchard']}/{c.get('market','-')}"
                         for c in consumers if c.get("criticality") == "blocking"],
        "consumers": consumers,
    }


def main():
    p = argparse.ArgumentParser(description="Trunk capability catalogue (agent surface)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search"); s.add_argument("query")
    d = sub.add_parser("describe"); d.add_argument("name")
    c = sub.add_parser("can-i")
    c.add_argument("need")
    c.add_argument("--orchard", required=True, choices=["self-serve", "assisted", "business"])
    c.add_argument("--market", required=True, choices=["DE", "UK", "ES"])
    co = sub.add_parser("consumers-of"); co.add_argument("name")

    a = p.parse_args()
    docs = load_all()

    if a.cmd == "search":
        out = tool_search(a.query, docs)
    elif a.cmd == "describe":
        out = tool_describe(a.name, docs)
    elif a.cmd == "can-i":
        out = tool_can_i(a.need, a.orchard, a.market, docs)
    else:
        out = tool_consumers_of(a.name, docs)

    json.dump(out, sys.stdout, indent=2, ensure_ascii=False, default=str)
    print()


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # Piping into head/less closes stdout early. Exit quietly instead of
        # printing a traceback over a live demo.
        try:
            sys.stdout.close()
        except Exception:
            pass
        os._exit(0)
