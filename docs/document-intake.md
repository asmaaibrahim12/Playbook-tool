# Document Intake

**🟢 stable** · Trunk: `data-and-docs` · Owner: #trunk-data-and-docs

Receives an uploaded document, validates and stores it, and emits an event the rest of the pipeline listens for.

## Should you use this?

**It does**

- Accept an upload over HTTP and validate type, size and page count
- Store it against a user with a retention clock and an audit trail
- Emit document.received so extraction and anything else can pick it up
- Serve the original back, with every access logged

**It does not**

- Read anything out of the document — see document-extraction
- Accept bulk or batch upload; this is one document per request
- Accept files over 20 MB or 40 pages
- Store anything outside the EU

**Build your own if**

- You need batch ingest of thousands of documents. This is built for a person uploading one thing, and the per-request overhead will hurt you
- Your documents never need to be served back to a user, in which case you want object storage rather than this

## How much of this can you do without us?

### L3 — you extend it yourself

Open to pull requests. You can change the capability, not only call it.

- Run the eval on your own data: **yes**
- Contribution: **open — raise a PR, not a ticket**

> **Next rung:** Already at L3. Two Orchards have merged changes here; the Business Orchard added page-count validation in May.

## By market

| Market | Status | Obligation | Channel |
|---|---|---|---|
| DE | ✅ live | Einkommensteuererklärung, EÜR | ELSTER |
| UK | ✅ live | Self Assessment | HMRC |
| ES | ✅ live | Renta | AEAT |

## Regulatory boundary

Automated (software may do this):

- Accepting, storing and serving a document
- Applying a retention policy

Requires a licensed human:

- Nothing. Intake moves bytes and never reads them, so the advice boundary does not apply here.

*Basis: §3 StBerG does not reach storage.*

## Does it actually work?

Upload a corpus of known-good and known-bad files and assert the accept/reject decision and the emitted event. Run it yourself: `npx @taxfix/data-docs eval --set <your-set> --capability document-intake`

| Metric | Value | Source | Measured on | As of |
|---|---|---|---|---|
| accept_decision_accuracy | 0.999 | **assumed** | mixed valid/invalid corpus, n=8,000 | 2026-09-30 |
| p99_upload_latency_ms | 840 ms | **assumed** | DE production traffic | 2026-09-30 |

**Known failure modes**

- Scanned TIFFs from older office scanners are rejected as unsupported
- A document uploaded twice within the same session creates two records

**Fallback:** A rejected upload returns the reason to the caller, who decides whether to ask the user for a different file.

## Cost

≈ €0.004 per document stored per year (as of 2026-09-30)

> Cost per document retained, not per upload. Retention is the cost that compounds; the upload itself is close to free.

## Who depends on this

| Orchard | Market | Since | Criticality |
|---|---|---|---|
| self-serve | DE | 2019-01-01 | blocking |
| assisted | DE | 2023-01-01 | blocking |
| self-serve | UK | 2024-07-02 | blocking |

## Who do you ask

- Channel: #trunk-data-and-docs
- Response target: 4 hours

## Integrate

```
HTTP  https://api.internal.taxfix/data-docs/v1/documents
```

SDKs: `@taxfix/data-docs-js`, `taxfix-data-docs-py`

---

*Generated from `capabilities/document-intake.yaml`. Do not edit this page — edit the manifest.*
