# Validation report

This report records the checks completed against the current checkout. The complete
two-wallet lifecycle is still pending wallet approvals and is intentionally not
claimed as complete here.

## Passed locally

```text
python3 -m py_compile contracts/*.py
PASS

bundled-python -m pytest -q tests/unit
37 passed

bundled-python -m pytest -q tests/direct
13 passed

bundled-python scripts/release_check.py
RELEASE CHECK OK
Routes: /, /lab, /claim/[studyKey], /attempt/[attemptKey], /archive/[recordKey]
Clean-room route/component/palette guards passed.

genvm-lint check contracts/study_registry.py
PASS: lint and semantic validation

genvm-lint check contracts/replication_engine.py
PASS: lint and semantic validation

genvm-lint check contracts/research_pool.py
PASS: lint and semantic validation

genvm-lint schema contracts/{study_registry,replication_engine,research_pool}.py
PASS: schemas generated

pnpm install --frozen-lockfile
PASS: 245 packages installed from the pinned lockfile

pnpm run typecheck
PASS

pnpm run build
PASS: Next.js 16.3.6 production build; routes generated successfully
```

## Requires recipient environment

The live frontend is hosted at `https://the-reprove.vercel.app` and reads the
verified Studionet 61999 deployment addresses from the Production environment.
The fresh two-wallet lifecycle, deployed-source parity hashes, and associated
transaction receipts remain required before this report can support a 4/5 claim.
