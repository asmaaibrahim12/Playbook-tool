# Contributing to a Trunk capability

Every capability declares how much a consuming team can do without us, in
`self_service`. The rung is the contract.

| Level | What it means for you | What it costs us |
|---|---|---|
| **L0** | File a ticket. We build it. | A person, every time |
| **L1** | It's documented, but the work is still ours | A person, every time, with less explaining |
| **L2** | Integrate from the spec and the SDK, no ticket | Review and support only |
| **L3** | Change the capability yourself | Review only |

`can_contribute` is the inner-source posture:

- **open** — raise a PR, don't raise a ticket. The Trunk reviews within the
  stated response target. Required for anything serving 2+ Orchards, and
  required at L3.
- **review-required** — PRs welcome, but a Trunk engineer must approve the
  design before you build. Used where a statutory schema is involved.
- **closed** — the Trunk owns this outright. Should be rare, justified, and
  never on a capability two Orchards depend on.

## Moving a capability up a rung

This is the only platform roadmap item that reduces our own ticket volume, so
it is the one we track.

1. **To reach L1** — write the manifest honestly. `scope.does_not` and
   `build_your_own_if` are what stop teams discovering the gap mid-integration.
2. **To reach L2** — ship an eval set a consuming team can run on their own
   data, and set `can_run_eval: true`. CI refuses L2 without it: a team that
   can't verify the thing isn't self-serving, whatever else is true.
3. **To reach L3** — set `can_contribute: open` and mean it. The first merged
   PR from another Orchard is the proof, not the setting.

Below L2, `to_reach_next_level` is required. "Not self-service yet" has to be a
plan with a named blocker, not a status that sits there for a year.

## Graduating a capability from an Orchard

1. Open a PR adding a manifest with `lifecycle: experimental` and
   `graduated_from: <your-orchard>`.
2. Ship it to one more Orchard. Reach is proven, not asserted.
3. Add an eval set and set `self_service.can_run_eval: true`.
4. The Trunk takes ownership and the lifecycle moves to `beta`.

A capability cannot reach `stable` while consumers can't verify it themselves —
see `tools/validate.py`. If they have to ask us, we are the bottleneck, whatever
the uptime says.
