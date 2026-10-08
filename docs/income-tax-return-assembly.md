# Income Tax Return Assembly

**🟢 stable** · Trunk: `tax-core-and-submission` · Owner: #trunk-tax-core

Assembles a complete, validated income tax return from captured facts and hands it to the market's submission channel.

## Should you use this?

**It does**

- Validate a return against the statutory schema for the market and year
- Assemble annexes (Anlage N, S, EÜR, …) from supplied facts
- Submit via the market's channel and return the receipt

**It does not**

- Capture the underlying facts — see data-and-docs capabilities
- Support VAT-liable sole traders in DE
- Handle corporate returns or non-residents

**Build your own if**

- Never. Statutory schema changes land here once; a second implementation is a compliance liability, not an engineering choice.

## By market

| Market | Status | Obligation | Channel |
|---|---|---|---|
| DE | ✅ live | Einkommensteuererklärung | ELSTER |
| UK | ✅ live | Self Assessment | HMRC |
| ES | ✅ live | Renta | AEAT |

> **DE** — PUBLISHED GAP — Kleinunternehmer have been able to file the income tax return via Taxfix since tax year 2024, but taxfix.de/umsatzsteuerpflichtig states it is "not yet supported" for VAT-liable self-employed users who have paid €19.99/month since 18 Mar 2026. Same capability, different Orchard, not reused. This is the worked example in the prioritisation framework.

## Regulatory boundary

Automated (software may do this):

- Schema validation
- Arithmetic
- Transmission of a return the taxpayer has approved

Requires a licensed human:

- Any contested position on the return

*Basis: §3 StBerG; UK and ES bundle review inside the subscription tiers.*

## Does it actually work?

**You can verify this yourself.**

Statutory schema conformance plus regression against prior-year returns.

| Metric | Value | Source | Measured on | As of |
|---|---|---|---|---|
| submission_acceptance_rate | 0.994 | **assumed** | DE ELSTER submissions | 2026-09-30 |

**Known failure modes**

- ELSTER pre-fill is unavailable to users who already hold an ELSTER account and requires a postal activation code — which structurally excludes most self-employed users from automated retrieval

**Fallback:** Rejected submissions route to the Assisted Orchard's advisor queue.

## Cost

≈ €0.11 per return submitted (as of 2026-09-30)

> Cost per ACCEPTED submission. A rejected return costs this again plus the advisor minutes spent diagnosing it, so acceptance rate is the number that moves the cost, not the per-call price.

## Who depends on this

| Orchard | Market | Since | Criticality |
|---|---|---|---|
| self-serve | DE | 2019-01-01 | blocking |
| assisted | DE | 2023-01-01 | blocking |
| self-serve | UK | 2024-07-02 | blocking |
| self-serve | ES | 2022-04-01 | blocking |

## Support and contribution

- Channel: #trunk-tax-core
- Response target: 4 hours
- Contribution: **review-required**

## Integrate

```
HTTP  https://api.internal.taxfix/tax-core/v1/returns
```

SDKs: `@taxfix/tax-core-js`

---

*Generated from `capabilities/income-tax-return-assembly.yaml`. Do not edit this page — edit the manifest.*
