# Eval sets

One directory per capability. Each holds a held-out labelled set plus the
expected-output file the runner compares against.

The point of these living here, beside the manifests, is that
`evaluation.self_service: true` has to be literally true: an Orchard clones the
repo and runs the eval against its own data without asking the Trunk team for
anything. If verifying a capability requires us, we are the only ones who can
say whether it works, and that is a bottleneck on trust rather than on delivery.

    npx @taxfix/data-docs eval --set evals/document-extraction --market DE

Prototype note: the sets themselves are not included here. Real documents are
customer tax data and do not belong in a repo — in practice these would be
pointers into the eval store with access controlled separately.
