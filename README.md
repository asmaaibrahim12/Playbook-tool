# Capability Playbook

A working prototype for one Trunk team — `data-and-docs` — and the three
capabilities that make up its intake → extract → categorise pipeline.

It exists to answer one question, which is the question a platform team lives or
dies by: **how much of this can you do without us?**

Shared platform teams become queues. Not because they're slow, but because the
consuming teams can't tell what already exists, how to use it, or when they
should just build their own — so they ask. Every ask is a ticket, and the
tickets are what the headcount is really spent on.

Wiki pages are the usual answer and they go stale, because documentation written
separately from the thing it describes drifts. When the two drift apart nothing
breaks — so they drift apart.

Here each capability is **one manifest**, living next to the code, and every
manifest must declare where it sits on a four-rung self-service ladder:

| | |
|---|---|
| **L0** | we build it and close the ticket |
| **L1** | we build it and write down how |
| **L2** | you build on it without us |
| **L3** | you extend it yourself |

Because the rung is a required field rather than a claim in a slide, *"2 of 3
capabilities are at L2 or above"* is a number you can read off the files — and
moving one up a rung is a commit someone can review.

Both the page a person reads and the index an agent queries are generated from
those same manifests.

```
capabilities/*.yaml          the single source
      │
      ├── tools/render.py    → docs/*.md      a person browses these
      ├── tools/catalogue.py → search, can-i  an agent queries these
      ├── tools/validate.py  → CI gate        keeps it honest
      ├── tools/new.py       → scaffold       how a team adds one
      └── server.py          → HTTP           both surfaces, one deployment
```

`server.py` imports the query logic from `tools/catalogue.py` rather than
reimplementing it, so there is only one answer to "what does this capability do".

## Run it

Needs Python 3.9+ and two packages.

```bash
pip3 install pyyaml jsonschema
```

If that gives you `externally-managed-environment`, use
`pip3 install --user pyyaml jsonschema`.

**1. The CI gate, passing**

```bash
python3 tools/validate.py
```

**2. The gate catching a bad manifest** — the interesting one

```bash
python3 tools/validate.py demo/failing
```

Five failures, exit code 1. Only the first is about documentation. The rest are
operating-model rules (below) — including a manifest claiming L2 self-service
while its consumers can't run the eval, which is the rung nobody gets to skip.

**3. Generate the human-readable docs**

```bash
python3 tools/render.py        # writes docs/, then open docs/index.md
```

**4. Query it the way an agent would**

```bash
python3 tools/catalogue.py search "extract fields from an uploaded payslip"
python3 tools/catalogue.py describe document-extraction
python3 tools/catalogue.py consumers-of document-intake
python3 tools/catalogue.py can-i "extract fields from an uploaded payslip" \
        --orchard business --market DE
```

`can-i` is the question a builder actually asks, and the answer carries the
self-service rung next to the market status — because *live* at L0 still means
waiting on someone else's backlog.

Three queries worth running, because they behave differently:

| Query | What comes back |
|---|---|
| `"extract fields from an uploaded payslip"` | a confident match |
| `"file a VAT advance return"` | a **wrong** match, labelled as a guess — see below |
| `"reconcile a bank statement"` | nothing, said plainly |

**5. Add a capability**

```bash
python3 tools/new.py receipt-matching --trunk data-and-docs
```

Writes a manifest with every field in place, in the order a builder reads them,
each with a line saying what it is for. Fill the TODOs and run the validator —
it refuses a manifest that still has them, so a half-written entry can't reach
the catalogue.

The scaffold starts at **L0** with `can_run_eval: false`. That's deliberate: a
new capability is a ticket queue until someone does the work to make it
otherwise, and the file should say so from the first commit.

**6. Both surfaces in a browser**

```bash
python3 server.py        # → http://localhost:8000
```

| Route | What it is |
|---|---|
| `/` | the catalogue by self-service level, plus a box to ask it a question |
| `/ask` | the answer, with the guess and the facts rendered apart |
| `/c/{name}` | one capability page |
| `/api` | the endpoint index, so an agent can discover the rest |
| `/api/capabilities` · `/api/capabilities/{name}` | list and full manifest |
| `/api/search?q=` | rank capabilities against a need |
| `/api/can-i?need=&orchard=&market=` | the builder's question |
| `/healthz` | returns the manifest count, or 503 if one is broken |

## Deploy it

Railway picks this up from `requirements.txt` and `railway.json` with no extra
configuration. From the repo root:

```bash
npm i -g @railway/cli     # once
railway login
railway init              # or: railway link   to attach an existing project
railway up
railway domain            # generates the public URL
```

Or from the Railway dashboard: **New Project → Deploy from GitHub repo**, pick
this repository, and deploy. Nothing to set — no environment variables, no
database, no build step. `$PORT` is read from the environment and the health
check points at `/healthz`.

The same files work on anything that reads a `Procfile` (Render, Fly, Heroku).
Check Railway's current pricing before you leave it running; a small always-on
service is usually a few dollars a month.

## What's in a manifest

Fields are ordered by the questions a builder actually asks, in the order they
ask them. A manifest reads top to bottom as a decision.

| | Question | Field |
|---|---|---|
| 1 | Does it do what I need? | `scope.does` / `scope.does_not` |
| 2 | Should I not use it at all? | `build_your_own_if` |
| 3 | **How much can I do without you?** | **`self_service`** |
| 4 | Does it work where I am? | `availability.markets`, `availability.advice_boundary` |
| 5 | Is it good enough for my risk? | `evaluation` |
| 6 | What does it cost me? | `cost` |
| 7 | How do I call it? | `interface` |
| 8 | Who else relies on it? | `consumers` |
| 9 | Who do I ask? | `support` |

`interface` sits seventh on purpose. Nobody needs an entrypoint for a capability
they've already decided against, and putting it first — as most service
catalogues do — makes the file read backwards for its main reader.

`self_service` sits third because it changes the answer to everything below it.
A capability that is live, cheap and well-specified is still a ticket if you
can't move without the Trunk.

Three fields carry most of the weight:

| Field | Why |
|---|---|
| `self_service` | Its own section, not a flag buried in another one. `level` is the rung; `can_run_eval` and `can_contribute` are the two things that actually decide it. If a consuming team can't run the eval on their own data, only the platform team can say whether the thing works — a bottleneck on *trust*, which no uptime dashboard shows. If they can't raise a PR, every change is your backlog. `to_reach_next_level` is required below L2, so a low rung has to name what's missing instead of sitting there. |
| `scope.does_not` + `build_your_own_if` | Both required. A catalogue that only says yes doesn't get believed. The first is what it can't do; the second is when you shouldn't ask it to. |
| `availability` | Market differences as data, not forked code. Some markets let software act alone; others need a licensed human in the loop, so the legal boundary is configured per capability rather than assumed globally. |

The envelope borrows [Backstage](https://backstage.io)'s `apiVersion` / `kind` /
`metadata`, a small closed set of kinds, and specs referenced rather than copied.
It drops Backstage's `spec` wrapper, which is a Kubernetes convention that buys
nothing here beyond an extra level on every path.

## The rules CI enforces

`tools/validate.py` checks more than schema shape:

- A manifest still carrying `TODO` fails. Scaffolding is not documentation.
- Metrics older than 180 days fail. An unproven claim can't sit there forever.
- **You can't claim a rung you haven't earned.** L2 or above requires
  `can_run_eval: true`; L3 requires `can_contribute: open`. Otherwise the ladder
  becomes a vocabulary exercise and the ratio means nothing.
- **A low rung has to name its blocker.** L0 and L1 require
  `to_reach_next_level`, so "not self-service yet" is a plan, not a status.
- A capability can't be `stable` while its consumers can't verify it themselves.
- A capability serving two or more teams can't refuse pull requests — that's the
  definition of a service desk.
- Anything another team's roadmap depends on must declare a human fallback.

The ladder is enforced in exactly one place, `check_trust_rules`, and read
everywhere else. That's the point: the level on the page, the level in the API
response and the level CI checks are the same field.

The GitHub workflow adds two more: every service directory needs a manifest, and
the committed docs must match what the manifests generate. So shipping *is*
documenting, and nobody hand-edits generated output.

## What this prototype doesn't do

`catalogue.py` ranks by **lexical overlap**, not meaning. It can't tell a
capability that does the thing from one that merely uses the same words — which
produced a real bug in testing: asked to *file a VAT advance return*, it matched
"vat" and "return" in expense categorisation and answered *available*. Nothing
here files anything.

Run that query and you'll still see it pick the wrong capability. That's left in
deliberately, because a score threshold didn't fix it — the score wasn't the
problem. The fix was to stop merging two different claims into one answer:

- **which capability you meant** is a *guess* from word overlap
- **whether it's live in your market** is a *fact* the manifest declares

`can-i` now returns those separately, with `does` and `does_not` in between, so
you read what it actually does before you trust the verdict. In production the
matcher would be embeddings over the same manifests; separating the guess from
the fact would stay the same shape, and still be the part that matters.

Every accuracy, cost and throughput number in the manifests is invented. That
isn't left to a comment: each metric and the cost block carry a required
`source` field set to `assumed`, so the generated docs print it and the API
returns it. A consuming team can't mistake a placeholder for a measurement.

The eval sets aren't included — real tax documents are customer data and don't
belong in a repo.
