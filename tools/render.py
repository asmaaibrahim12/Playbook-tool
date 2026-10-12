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

# The ladder, written out once here and once in the schema's enum description.
# Nowhere else — a level means the same thing on every page because every page
# is generated from the same field.
LADDER = {
    "L0": ("L0 — we build it, ticket closed",
           "Every change goes through the Trunk. Nothing here you can do unaided."),
    "L1": ("L1 — we build it, and write down how",
           "Documented, but the work still lands on the Trunk's backlog."),
    "L2": ("L2 — you build on it without us",
           "Integrate straight from the spec and the SDK. No Trunk ticket in your path."),
    "L3": ("L3 — you extend it yourself",
           "Open to pull requests. You can change the capability, not only call it."),
}
CONTRIB = {"open": "open — raise a PR, not a ticket",
           "review-required": "review required — PRs welcome, Trunk approves",
           "closed": "closed — the Trunk is the only author"}


def render_one(d):
    m, s = d["metadata"], d
    L = [f"# {m.get('title', m['name'])}", ""]
    L.append(f"**{BADGE[m['lifecycle']]}** · Trunk: `{m['trunk']}` · Owner: {m['owner']}")
    if m.get("graduated_from"):
        L.append(f"> Graduated from the **{m['graduated_from']}** Orchard via inner source.")
    L += ["", m["summary"].strip(), ""]

    L += ["## Should you use this?", ""]
    L += ["**It does**", ""] + [f"- {x}" for x in s["scope"]["does"]] + [""]
    L += ["**It does not**", ""] + [f"- {x}" for x in s["scope"]["does_not"]] + [""]
    L += ["**Build your own if**", ""] + [f"- {x}" for x in s["build_your_own_if"]] + [""]

    ss = s["self_service"]
    head, meaning = LADDER[ss["level"]]
    L += ["## How much of this can you do without us?", "", f"### {head}", "", meaning, "",
          f"- Run the eval on your own data: **{'yes' if ss['can_run_eval'] else 'no'}**"
          + ("" if ss["can_run_eval"]
             else " — only the Trunk can say whether this works for your case. "
                  "That is a bottleneck on trust, and no uptime dashboard shows it."),
          f"- Contribution: **{CONTRIB[ss['can_contribute']]}**", ""]
    if ss.get("to_reach_next_level"):
        L += [f"> **Next rung:** {ss['to_reach_next_level'].strip()}", ""]

    if s["availability"]["markets"]:
        L += ["## By market", "", "| Market | Status | Obligation | Channel |", "|---|---|---|---|"]
        for j in s["availability"]["markets"]:
            L.append(f"| {j['market']} | {STATUS[j['status']]} | "
                     f"{j.get('obligation','—')} | {j.get('channel','—')} |")
        L.append("")
        for j in s["availability"]["markets"]:
            if j.get("notes"):
                L += [f"> **{j['market']}** — {j['notes'].strip()}", ""]

    if s["availability"].get("advice_boundary"):
        ab = s["availability"]["advice_boundary"]
        L += ["## Regulatory boundary", "",
              "Automated (software may do this):", ""]
        L += [f"- {x}" for x in ab["automated"]]
        L += ["", "Requires a licensed human:", ""]
        L += [f"- {x}" for x in ab["requires_licensed_human"]]
        if ab.get("basis"):
            L += ["", f"*Basis: {ab['basis'].strip()}*"]
        L.append("")

    ev = s["evaluation"]
    L += ["## Does it actually work?", "", ev["method"].strip(), "",
          "| Metric | Value | Source | Measured on | As of |", "|---|---|---|---|---|"]
    for mt in ev["metrics"]:
        src = "measured" if mt.get("source") == "measured" else "**assumed**"
        L.append(f"| {mt['name']} | {mt['value']}{(' ' + mt['unit']) if mt.get('unit') else ''} "
                 f"| {src} | {mt['measured_on']} | {mt['as_of']} |")
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
    L += ["## Who do you ask", "",
          f"- Channel: {sp['channel']}",
          f"- Response target: {sp.get('response_target','—')}", ""]

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

    trunk = sorted({d["metadata"]["trunk"] for d in docs})
    levels = [d["self_service"]["level"] for d in docs]
    at_l2 = sum(1 for l in levels if l in ("L2", "L3"))

    index = ["# Capability catalogue — " + ", ".join(f"`{t}`" for t in trunk), "",
             f"**{at_l2} of {len(docs)} capabilities are at L2 or above** — a consuming "
             "team can build on them without a ticket. That number is read off the "
             "manifests, not estimated.", "",
             "Every page here is generated from a manifest. If a page is wrong, "
             "the manifest is wrong — and CI will tell you.", "",
             "| Capability | Self-service | Status | Orchards | Summary |",
             "|---|---|---|---|---|"]
    for d in docs:
        m, s = d["metadata"], d
        n_orch = len({c["orchard"] for c in s["consumers"]})
        index.append(f"| [{m.get('title', m['name'])}](./{m['name']}.md) "
                     f"| **{s['self_service']['level']}** "
                     f"| {BADGE[m['lifecycle']]} | {n_orch} | {m['summary'].strip()[:80]}… |")
        (outdir / f"{m['name']}.md").write_text(render_one(d))

    index += ["",
              "**L0** we build it and close the ticket · **L1** we build it and write "
              "down how · **L2** you build on it without us · **L3** you extend it "
              "yourself.", "",
              "The level is a required field in every manifest, so moving a capability "
              "up a rung is a commit someone can review — not a claim in a slide.", ""]
    (outdir / "index.md").write_text("\n".join(index) + "\n")
    print(f"Rendered {len(docs)} capability page(s) + index to {outdir}/")
    print(f"Self-service: {at_l2}/{len(docs)} at L2 or above")


if __name__ == "__main__":
    main()
