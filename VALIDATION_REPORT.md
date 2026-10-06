# REPROVE validation report

## Audit status

This branch contains the corrected REPROVE V2 implementation after the
milestone audit. The fixed-point threshold arithmetic, immutable provenance
binding, registration configuration, capsule UI, and deterministic reported
result schema have been corrected locally and are awaiting a fresh contract
deployment and lifecycle.

No V2 lifecycle is claimed by this report. The next stage is an independent
audit followed by a fresh Studionet deployment and two-wallet lifecycle using
the corrected contract sources.

## Historical evidence

The lifecycle receipts previously recorded below are historical V1-style
validation evidence from an earlier deployment. They are retained for
traceability only and must not be read as evidence that the corrected V2
contracts have completed a fresh live lifecycle.

- Historical frontend: [reprove.vercel.app](https://reprove.vercel.app)
- Historical study: `final-smoke-2026f`
- Historical parent evaluation, pool child, withdrawal, and close receipts are
  preserved in the repository history and prior deployment records.
- The historical flow demonstrated registration, funding, assessment, reward
  withdrawal, and closure, but predates the current audit corrections.

## Current verification target

The corrected branch must pass, before redeployment:

```text
python3 -m py_compile contracts/*.py
pytest -q tests/unit
pytest -q tests/direct
genvm-lint check contracts/study_registry.py
genvm-lint check contracts/replication_engine.py
genvm-lint check contracts/research_pool.py
python3 scripts/release_check.py
cd web && npm install && npm run typecheck && npm run build
npm audit --omit=dev
```

The current deployment manifest is intentionally marked as historical until
fresh corrected contracts are deployed. No deployment transaction or live
Studionet lifecycle is part of this audit.
