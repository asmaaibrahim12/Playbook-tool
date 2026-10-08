# Document Extraction

**🟡 beta** · Trunk: `data-and-docs` · Owner: #trunk-data-and-docs

Extracts tax-relevant fields from uploaded documents (payslips, invoices, receipts, statements) and returns structured values with per-field confidence.

## Should you use this?

**It does**

- Classify an uploaded document into a known type
- Extract named fields with a confidence score per field
- Return provenance (page, bounding box) for every extracted value
- Flag low-confidence fields for human review rather than guessing

**It does not**

- Write values into a tax return — the caller decides what to accept
- Decide whether an expense is deductible (see advice_boundary)
- Handle handwritten documents above ~60% reliability
- Process documents in languages other than DE, EN, ES

**Build your own if**

- You need a document type not in the supported list AND volume is under ~500/month — the integration cost will exceed the benefit
- You need sub-200ms synchronous extraction inside a live user flow
- You are prototyping and do not yet know which fields you need

## By market

| Market | Status | Obligation | Channel |
|---|---|---|---|
| DE | ✅ live | Einkommensteuererklärung, EÜR, UStVA | ELSTER |
| UK | 🚧 in progress | Self Assessment, MTD quarterly update | HMRC MTD API |
| ES | 🚧 in progress | Renta, modelo 303 | AEAT |

> **DE** — ASSUMPTION: Lohnsteuerbescheinigung capture is live in the consumer app. Taxfix support docs state the consumer Document Manager does NOT yet auto-import values into the return ("planned for 2026"), so treat general auto-import as in-progress rather than live.

## Regulatory boundary

Automated (software may do this):

- Capture a value from a document
- Categorise against a chart of accounts
- Calculate a total from captured values
- Transmit a completed return the taxpayer has approved

Requires a licensed human:

- Asserting a contestable tax position
- Recommending a treatment where the law is ambiguous
- Preparing a UStVA on behalf of another person

*Basis: §3 StBerG reserves commercial tax assistance to licensed professions. §6 exceptions do not extend to preparing UStVA for others (BFH 7 June 2017, II R 22/15). DE is software-only; UK and ES bundle human review inside the subscription, so this boundary is configured per market rather than assumed globally.*

## Does it actually work?

**You can verify this yourself.**

Held-out labelled document set per type and market. Field-level exact match for structured fields, normalised match for free text. Run it yourself: `npx @taxfix/data-docs eval --set <your-set> --market DE`

| Metric | Value | Measured on | As of |
|---|---|---|---|
| field_accuracy_lohnsteuerbescheinigung | 0.97 | DE held-out set, n=4,200 | 2026-09-30 |
| field_accuracy_invoice | 0.89 | DE self-employed set, n=1,850 | 2026-09-30 |
| straight_through_rate | 0.71 fraction of documents needing no human touch | DE combined set | 2026-09-30 |

**Known failure modes**

- Scanned photos at an angle degrade bounding-box provenance
- Multi-page invoices with line items spanning a page break
- Non-standard invoice layouts from small foreign suppliers

**Fallback:** Fields below the caller's configured threshold are returned as needs_review. The Orchard decides the threshold; the Trunk does not.

## Cost

≈ €0.042 per document processed (as of 2026-09-30)

> Track cost per SUCCESSFUL extraction, not per call. An extraction that fails and escalates to a tax expert carries the advisor's minutes, which on the Expert tier are charged against a 20%-of-refund fee that does not scale with time spent.

## Who depends on this

| Orchard | Market | Since | Criticality |
|---|---|---|---|
| self-serve | DE | 2024-03-01 | important |
| business | DE | 2026-03-18 | blocking |
| assisted | DE | 2025-01-15 | important |

## Support and contribution

- Channel: #trunk-data-and-docs
- Response target: 1 business day
- Contribution: **open** — raise a PR, don't raise a ticket.

## Integrate

```
HTTP  https://api.internal.taxfix/data-docs/v1/extract
```

SDKs: `@taxfix/data-docs-js`, `taxfix-data-docs-py`

---

*Generated from `capabilities/document-extraction.yaml`. Do not edit this page — edit the manifest.*
