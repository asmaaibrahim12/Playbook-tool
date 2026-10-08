# Capability Playbook

A working prototype for a problem shared platform teams keep hitting: the teams
who consume a platform can't tell what already exists, how to use it, or when
they should just build their own.

Wiki pages go stale because the documentation is a separate thing from what it
describes. When the two drift apart, nothing breaks — so they drift apart.

Here each capability is **one manifest**, living next to the code. Both the page
a person reads and the index an agent queries are generated from it.

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

Four failures, exit code 1. Only the first is about documentation; the rest are
operating-model rules (below).

**3. Generate the human-readable docs**

```bash
python3 tools/render.py        # writes docs/, then open docs/index.md
```

**4. Query it the way an agent would**

```bash
python3 tools/catalogue.py search "extract fields from an invoice"
python3 tools/catalogue.py describe document-extraction
python3 tools/catalogue.py consumers-of income-tax-return-assembly
python3 tools/catalogue.py can-i "file an income tax return" \
        --orchard business --market DE
```

That last one is the question a builder actually asks. Try it with
`"file a VAT advance return"` too — nothing in the catalogue does that, and the
output says so instead of guessing.

**5. Add a capability**

```bash
python3 tools/new.py receipt-matching --trunk data-and-docs
```

Writes a manifest with every field in place, in the order a builder reads them,
each with a line saying what it is for. Fill the TODOs and run the validator —
it refuses a manifest that still has them, so a half-written entry can't reach
the catalogue.

**6. Both surfaces in a browser**

```bash
python3 server.py        # → http://localhost:8000
```

| Route | What it is |
|---|---|
| `/` | the catalogue, plus a box to ask it a question |
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
| 3 | Does it work where I am? | `availability.markets`, `availability.advice_boundary` |
| 4 | Is it good enough for my risk? | `evaluation` |
| 5 | What does it cost me? | `cost` |
| 6 | How do I call it? | `interface` |
| 7 | Who else relies on it? | `consumers` |
| 8 | Who do I ask? | `support` |

`interface` sits sixth on purpose. Nobody needs an entrypoint for a capability
they've already decided against, and putting it first — as most service
catalogues do — makes the file read backwards for its main reader.

Three fields carry most of the weight:

| Field | Why |
|---|---|
| `scope.does_not` + `build_your_own_if` | Both required. A catalogue that only says yes doesn't get believed. The first is what it can't do; the second is when you shouldn't ask it to. |
| `evaluation.self_service` | First field in its section. The platform owns *how* you prove a capability is safe to ship; each consuming team sets its own threshold. If they can't run the eval on their own data, only the platform team can say whether it works. That's a bottleneck on trust, and no uptime dashboard shows it. |
| `availability` | Market differences as data, not forked code. Some markets let software act alone; others need a licensed human in the loop, so the legal boundary is configured per capability rather than assumed globally. |

The envelope borrows [Backstage](https://backstage.io)'s `apiVersion` / `kind` /
`metadata`, a small closed set of kinds, and specs referenced rather than copied.
It drops Backstage's `spec` wrapper, which is a Kubernetes convention that buys
nothing here beyond an extra level on every path.

## The rules CI enforces

`tools/validate.py` checks more than schema shape:

- A manifest still carrying `TODO` fails. Scaffolding is not documentation.
- Metrics older than 180 days fail. An unproven claim can't sit there forever.
- A capability can't be `stable` while `self_service` is false.
- A capability serving two or more teams can't refuse pull requests — that's the
  definition of a service desk.
- Anything another team's roadmap depends on must declare a human fallback.

The GitHub workflow adds two more: every service directory needs a manifest, and
the committed docs must match what the manifests generate. So shipping *is*
documenting, and nobody hand-edits generated output.

## What this prototype doesn't do

`catalogue.py` ranks by **lexical overlap**, not meaning. It can't tell a
capability that does the thing from one that merely uses the same words — which
produced a real bug in testing: asked about VAT advance returns, it matched the
word "return" in an unrelated capability and answered *available*.

A score threshold didn't fix it, because the score wasn't the problem. The fix
was to stop merging two different claims into one answer:

- **which capability you meant** is a *guess* from word overlap
- **whether it's live in your market** is a *fact* the manifest declares

`can-i` now returns those separately, with `does` and `does_not` in between, so
you verify before you trust. In production the matcher would be embeddings over
the same manifests; separating the guess from the fact would stay the same shape.

Every accuracy, cost and throughput number in the manifests is invented. That
isn't left to a comment: each metric and the cost block carry a required
`source` field set to `assumed`, so the generated docs print it and the API
returns it. A consuming team can't mistake a placeholder for a measurement.

The eval sets aren't included — real tax documents are customer data and don't
belong in a repo.
