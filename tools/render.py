#!/usr/bin/env python3
"""The human surface. Renders the same manifests as browsable docs.

Humans do not read YAML and should not have to. But documentation written
separately from the thing it describes drifts — which is what happened to the
Notion pages. So the docs are GENERATED, never authored.

Usage: python3 tools/render.py [outdir]
"""
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent

BADGE = {"stable": "🟢 stable", "beta": "🟡 beta",
         "experimental": "🔵 experimental", "deprecated": "🔴 deprecated"}
STATUS = {"live": "✅ live", "in-progress": "🚧 in progress", "not-supported": "⛔ not supported"}


def render_one(d):
    m, s = d["metadata"], d["spec"]
    L = [f"# {m.get('title', m['name'])}", ""]
    L.append(f"**{BADGE[m['lifecycle']]}** · Trunk: `{m['trunk']}` · Owner: {m['owner']}")
    if m.get("graduated_from"):
        L.append(f"> Graduated from the **{m['graduated_from']}** Orchard via inner source.")
    L += ["", m["summary"].strip(), ""]

    L += ["## Should you use this?", ""]
    L += ["**It does**", ""] + [f"- {x}" for x in s["scope"]["does"]] + [""]
    L += ["**It does not**", ""] + [f"- {x}" for x in s["scope"]["does_not"]] + [""]
    L += ["**Build your own if**", ""] + [f"- {x}" for x in s["scope"]["build_your_own_if"]] + [""]

    if s["scope"].get("jurisdictions"):
        L += ["## By market", "", "| Market | Status | Obligation | Channel |", "|---|---|---|---|"]
        for j in s["scope"]["jurisdictions"]:
            L.append(f"| {j['market']} | {STATUS[j['status']]} | "
                     f"{j.get('obligation','—')} | {j.get('channel','—')} |")
        L.append("")
        for j in s["scope"]["jurisdictions"]:
            if j.get("notes"):
                L += [f"> **{j['market']}** — {j['notes'].strip()}", ""]

    if s["scope"].get("advice_boundary"):
        ab = s["scope"]["advice_boundary"]
        L += ["## Regulatory boundary", "",
              "Automated (software may do this):", ""]
        L += [f"- {x}" for x in ab["automated"]]
        L += ["", "Requires a licensed human:", ""]
        L += [f"- {x}" for x in ab["requires_licensed_human"]]
        if ab.get("basis"):
            L += ["", f"*Basis: {ab['basis'].strip()}*"]
        L.append("")

    ev = s["evaluation"]
    L += ["## Does it actually work?", "",
          f"{'**You can verify this yourself.**' if ev['self_service'] else '⚠️ **Not self-service** — you must ask the Trunk to verify. Treat that as a bottleneck.'}",
          "", ev["method"].strip(), "",
          "| Metric | Value | Measured on | As of |", "|---|---|---|---|"]
    for mt in ev["metrics"]:
        L.append(f"| {mt['name']} | {mt['value']}{(' ' + mt['unit']) if mt.get('unit') else ''} "
                 f"| {mt['measured_on']} | {mt['as_of']} |")
    L.append("")
    if ev.get("known_failure_modes"):
        L += ["**Known failure modes**", ""] + [f"- {x}" for x in ev["known_failure_modes"]] + [""]
    if ev.get("human_fallback"):
        L += [f"**Fallback:** {ev['human_fallback'].strip()}", ""]

    if s.get("cost"):
        c = s["cost"]
        L += ["## Cost", "",
              f"≈ €{c.get('amount_eur','?')} {c.get('unit','')} (as of {c.get('as_of','—')})", ""]
        if c.get("measure"):
            L += [f"> {c['measure'].strip()}", ""]

    L += ["## Who depends on this", "", "| Orchard | Market | Since | Criticality |", "|---|---|---|---|"]
    for c in s["consumers"]:
        L.append(f"| {c['orchard']} | {c.get('market','—')} | {c['since']} | {c.get('criticality','—')} |")
    L.append("")

    sp = s["support"]
    L += ["## Support and contribution", "",
          f"- Channel: {sp['channel']}",
          f"- Response target: {sp.get('response_target','—')}",
          f"- Contribution: **{sp['contribution']}**"
          + (" — raise a PR, don't raise a ticket." if sp["contribution"] == "open" else ""),
          ""]

    L += ["## Integrate", "",
          "```", f"{s['interface']['protocol'].upper()}  {s['interface']['entrypoint']}", "```", ""]
    if s["interface"].get("sdk"):
        L += ["SDKs: " + ", ".join(f"`{x}`" for x in s["interface"]["sdk"]), ""]
    L += ["---", "", "*Generated from `capabilities/" + m["name"] +
          ".yaml`. Do not edit this page — edit the manifest.*", ""]
    return "\n".join(L)


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs"
    outdir.mkdir(parents=True, exist_ok=True)
    docs = [yaml.safe_load(p.read_text())
            for p in sorted((ROOT / "capabilities").glob("*.yaml"))]

    index = ["# Trunk capability catalogue", "",
             "Every page here is generated from a manifest. If a page is wrong, "
             "the manifest is wrong — and CI will tell you.", "",
             "| Capability | Trunk | Status | Orchards | Summary |", "|---|---|---|---|---|"]
    for d in docs:
        m, s = d["metadata"], d["spec"]
        n_orch = len({c["orchard"] for c in s["consumers"]})
        index.append(f"| [{m.get('title', m['name'])}](./{m['name']}.md) | `{m['trunk']}` "
                     f"| {BADGE[m['lifecycle']]} | {n_orch} | {m['summary'].strip()[:80]}… |")
        (outdir / f"{m['name']}.md").write_text(render_one(d))
    (outdir / "index.md").write_text("\n".join(index) + "\n")
    print(f"Rendered {len(docs)} capability page(s) + index to {outdir}/")


if __name__ == "__main__":
    main()
