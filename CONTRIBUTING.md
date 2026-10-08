# Contributing to a Trunk capability

Inner source posture is declared per capability in `spec.support.contribution`.

- **open** — raise a PR, don't raise a ticket. The Trunk reviews within the
  stated response target. This is the default for anything serving 2+ Orchards.
- **review-required** — PRs welcome, but a Trunk engineer must approve the
  design before you build. Used where a statutory schema is involved.
- **closed** — the Trunk owns this outright. Should be rare and justified.

## Graduating a capability from an Orchard

1. Open a PR adding a manifest with `lifecycle: experimental` and
   `graduated_from: <your-orchard>`.
2. Ship it to one more Orchard. Reach is proven, not asserted.
3. Add an eval set and set `evaluation.self_service: true`.
4. The Trunk takes ownership and the lifecycle moves to `beta`.

A capability cannot reach `stable` while `self_service` is false — see
`tools/validate.py`. If consumers cannot verify it without asking us, we are
the bottleneck, whatever the uptime says.
