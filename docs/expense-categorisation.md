# Expense Categorisation

**🔵 experimental** · Trunk: `data-and-docs` · Owner: #trunk-data-and-docs
> Graduated from the **business** Orchard via inner source.

Assigns a chart-of-accounts category and VAT treatment to a transaction or extracted invoice, with confidence and an auditable reason.

## Should you use this?

**It does**

- Suggest a category from the market's chart of accounts
- Suggest a VAT rate and deductibility flag
- Return a short reason string for audit and for display to the user
- Learn per-account corrections (the user's own prior corrections win)

**It does not**

- Post to the ledger — suggestion only, the caller commits
- Decide private vs business use where the split is a judgement call
- Handle non-EU VAT regimes

**Build your own if**

- Your market's chart of accounts is not DE SKR03/SKR04, UK or ES
- You need deterministic rule-based categorisation for audit reasons rather than a model suggestion

## By market

| Market | Status | Obligation | Channel |
|---|---|---|---|
| DE | ✅ live | EÜR, UStVA | ELSTER |
| ES | 🚧 in progress | modelo 303, Verifactu | AEAT |
| UK | ⛔ not supported | MTD quarterly update | HMRC MTD API |

> **ES** — Verifactu obligation for autónomos lands before 1 Jul 2027.

## Regulatory boundary

Automated (software may do this):

- Suggesting a category
- Applying a statutory VAT rate

Requires a licensed human:

- Confirming deductibility where private use is contested
- Any position the taxpayer intends to defend against a challenge

*Basis: §3 StBerG. Suggestion is software; assertion is advice.*

## Does it actually work?

**You can verify this yourself.**

Labelled transaction set per market, stratified by category frequency. Top-1 accuracy plus a separate figure for the long tail, because headline accuracy is dominated by a handful of common categories.

| Metric | Value | Measured on | As of |
|---|---|---|---|
| top1_accuracy_overall | 0.92 | DE SKR03 set, n=12,000 | 2026-09-30 |
| top1_accuracy_long_tail | 0.64 | categories outside the top 20 by frequency | 2026-09-30 |

**Known failure modes**

- Long-tail categories are materially worse than the headline suggests
- Mixed private/business expenses are systematically over-categorised as business
- Subscription software invoices from US suppliers mis-handle reverse charge

**Fallback:** Below threshold, surface as uncategorised rather than guessing.

## Cost

≈ €0.008 per transaction (as of 2026-09-30)

> Cost per accepted suggestion, net of corrections.

## Who depends on this

| Orchard | Market | Since | Criticality |
|---|---|---|---|
| business | DE | 2026-03-18 | blocking |

## Support and contribution

- Channel: #trunk-data-and-docs
- Response target: 2 business days
- Contribution: **open** — raise a PR, don't raise a ticket.

## Integrate

```
HTTP  https://api.internal.taxfix/data-docs/v1/categorise
```

SDKs: `@taxfix/data-docs-js`

---

*Generated from `capabilities/expense-categorisation.yaml`. Do not edit this page — edit the manifest.*
