# Capability catalogue — `data-and-docs`

**2 of 3 capabilities are at L2 or above** — a consuming team can build on them without a ticket. That number is read off the manifests, not estimated.

Every page here is generated from a manifest. If a page is wrong, the manifest is wrong — and CI will tell you.

| Capability | Self-service | Status | Orchards | Summary |
|---|---|---|---|---|
| [Document Extraction](./document-extraction.md) | **L2** | 🟡 beta | 3 | Extracts tax-relevant fields from uploaded documents (payslips, invoices, receip… |
| [Document Intake](./document-intake.md) | **L3** | 🟢 stable | 2 | Receives an uploaded document, validates and stores it, and emits an event the r… |
| [Expense Categorisation](./expense-categorisation.md) | **L1** | 🔵 experimental | 1 | Assigns a chart-of-accounts category and VAT treatment to a transaction or extra… |

**L0** we build it and close the ticket · **L1** we build it and write down how · **L2** you build on it without us · **L3** you extend it yourself.

The level is a required field in every manifest, so moving a capability up a rung is a commit someone can review — not a claim in a slide.

