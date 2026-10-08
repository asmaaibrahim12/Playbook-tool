# Trunk Capability Playbook — working prototype

Task 3 of the Director of Product, Platform case study. Built for the
**Data & Docs** Trunk (plus one Tax Core capability, to show cross-Trunk reach).

## The one idea

**One source, two surfaces.**

Notion pages go stale because the documentation is a *separate artefact* from
the thing it describes. Nothing breaks when they diverge, so they diverge.

Here, each capability is one manifest in `capabilities/`. Humans read generated
docs. Agents query a generated index. Neither is authored by hand, so neither
can drift from the other — and CI fails if a capability ships without one.

Staleness stops being a discipline problem and becomes a build error.

```
capabilities/*.yaml   ← the single source of truth, lives beside the code
        │
        ├──► tools/render.py    ──► docs/*.md        (human surface)
        ├──► tools/catalogue.py ──► search/can-i/…   (agent surface, MCP-shaped)
        └──► tools/validate.py  ──► CI gate          (keeps it honest)
```

## Try it

```bash
pip install pyyaml jsonschema

# 1. The gate
python3 tools/validate.py                 # passes
python3 tools/validate.py demo/failing    # fails, with 4 specific reasons

# 2. The human surface
python3 tools/render.py && open docs/index.md

# 3. The agent surface
python3 tools/catalogue.py search "extract fields from an invoice"
python3 tools/catalogue.py can-i "file an income tax return" \
        --orchard business --market DE
python3 tools/catalogue.py consumers-of income-tax-return-assembly
```

## Three design decisions worth defending

**1. The schema has a `does_not` and a `build_your_own_if`, and both are required.**

A catalogue that only says yes is not trusted. The fastest way to lose an
Orchard is to oversell: they try the capability on the case it was never going
to handle, it fails, and now they distrust the whole platform. Telling a team
*not* to use you is what makes the yes credible.

**2. Evaluation is platform-owned; thresholds are Orchard-owned.**

The schema requires `evaluation.self_service`, and `validate.py` refuses to let
a capability reach `stable` while it is false. If an Orchard cannot run the eval
against its own data unaided, the Trunk is the sole arbiter of whether the thing
works — which is a bottleneck for *trust*, the kind that uptime dashboards never
show. Five Orchards each inventing their own accuracy bar is how a company ships
an agent that is quietly wrong about tax.

**3. Jurisdiction is data, not forked code.**

`scope.jurisdictions` models `market × obligation × channel` as rows. Germany's
UStVA, the UK's MTD quarterly update and Spain's modelo 303 are three dialects
of one capability: recurring, machine-verifiable filing from a running ledger.
`advice_boundary` is per-capability for the same reason — Germany is
software-only under §3 StBerG, while the UK and Spain bundle human review inside
the subscription. Same capability, three human-in-the-loop configurations.

## Where this lives, how it stays current, who owns it

**Lives** in the Trunk's own repo, next to the code it describes — not in a
docs repo and not in Notion. The manifest is reviewed in the same PR as the
change it documents.

**Stays current** through `.github/workflows/capability-catalogue.yml`, which
enforces three things: every manifest is valid and its metrics are under 180
days old; every service directory has a manifest; and the committed docs match
what the manifests generate. Nobody has to remember.

**Owned** by the Trunk team, as a team (`spec.metadata.owner` rejects a person —
individuals leave). The catalogue *index* across all Trunks is owned by platform
product, which is the job being hired for.

## Prior art borrowed deliberately

- **Backstage** — the thin `apiVersion`/`kind`/`metadata`/`spec` envelope, a small
  closed set of kinds, and specs embedded by reference so the OpenAPI document
  stays single-source. 3,000+ adopting companies; 700 squads at Spotify.
- **Team Topologies** — Thinnest Viable Platform, as the guard against over-build.
- **InnerSource Commons** — the maturity model behind `CONTRIBUTING.md`, which is
  how a consuming team graduates from raising a ticket to raising a PR.
- **MCP (spec of 28 Jul 2026)** — now stateless request/response, so exposing
  this catalogue to agents is an ordinary HTTP service, not new infrastructure.
  `tools/catalogue.py` is shaped as those four tools would be.

## What the matcher cannot do, said out loud

`catalogue.py` ranks capabilities by **lexical overlap** on their summary, tags
and `does` list. It has no semantics, so it cannot tell a capability that does
the thing from one that merely uses the same words.

That surfaced a real bug while testing. Ask it `can-i "file a VAT advance
return"` and nothing in this catalogue files VAT advance returns — but
`expense-categorisation` mentions VAT, and its `does` list contains the word
"return" (as in *return a reason string*), so it matched twice and the tool
reported **available**. A confidently wrong answer, which is the exact failure
the playbook exists to prevent.

A score threshold didn't fix it, because the problem isn't the score. The fix
was to stop collapsing two different kinds of claim into one answer:

- **which capability you meant** is a *guess* the matcher made from word overlap
- **whether that capability is live in your market** is a *fact* the manifest declares

`can-i` now returns those as separate keys — `match` (labelled a guess, with the
other candidates) and `if_that_is_the_right_capability` (the manifest's facts) —
with `does` and `does_not` in between, so you verify before you trust. In
production the matcher would be embeddings over the same manifests; the
separation of guess from fact would still be the right shape.

## Honesty about the data

Every accuracy, cost and straight-through figure in the manifests is marked
`# ASSUMPTION` and is invented. **Taxfix has never published an AI accuracy,
automation-rate or straight-through-processing metric anywhere.** The structural
facts — the €19.99/month subscription from 18 Mar 2026, the income tax return
published as "not yet supported" for VAT-liable users, the StBerG boundary, the
ELSTER pre-fill exclusion — are sourced and real. The performance numbers are
placeholders showing the *shape* of what the manifest should carry.
