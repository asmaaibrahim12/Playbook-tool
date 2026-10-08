# Capability Playbook

A working prototype for a problem shared platform teams keep hitting: the teams
who consume a platform can't tell what already exists, how to use it, or when
they should just build their own.

Wiki pages go stale because the documentation is a separate thing from what it
describes. When the two drift apart, nothing breaks — so they drift apart.

Here each capability is **one manifest**, living next to the code. Both the page
a person reads and the index an agent queries are generated from it, so they
can't disagree.

```
capabilities/*.yaml          the single source
      │
      ├── tools/render.py    → docs/*.md      a person browses these
      ├── tools/catalogue.py → search, can-i  an agent queries these
      └── tools/validate.py  → CI gate        keeps it honest
```

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

## What's in a manifest

The envelope is [Backstage](https://backstage.io)'s — `apiVersion`, `kind`,
`metadata`, `spec`, a small closed set of kinds, specs referenced rather than
copied. Three additions are specific to this problem:

| Field | Why |
|---|---|
| `does_not` + `build_your_own_if` | Both required. A catalogue that only says yes doesn't get believed. Being willing to send a team away is what makes the yes worth anything. |
| `evaluation.self_service` | The platform owns *how* you prove a capability is safe to ship; each consuming team sets its own threshold. If they can't run the eval on their own data, the platform team is the only one who can say it works — a bottleneck on trust that no uptime dashboard shows. |
| `scope.jurisdictions` + `advice_boundary` | Market differences as data, not forked code. Some markets allow software to act alone; others require a licensed human in the loop. |

## The rules CI enforces

`tools/validate.py` checks more than schema shape:

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

Every accuracy, cost and throughput number in the manifests is invented and
marked `ASSUMPTION`. The eval sets aren't included — real tax documents are
customer data and don't belong in a repo.
