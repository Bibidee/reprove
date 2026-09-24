# Validation report

This report records the checks completed against the current checkout and the live
Studionet 61999 smoke lifecycle. It does not claim a 4/5 score: deployed-source
parity hashes and a reward-eligible evidence run remain separate release evidence.

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

## Live Studionet smoke lifecycle

The canonical production frontend is `https://the-reprove.vercel.app` and the
study used for the smoke lifecycle is `reprove-live-2026-09` on chain 61999.

```text
creator:   0x4a7d…32f5
researcher: 0xff20…9b54
study registration: 0x71691c280d2a5899d8f29516b408f664b6b48285156e79ef656c195bd0f9a2db
pool funding (10 GEN): 0xeaa5b4c44bcff93b124f2ca05b40495a0a15e2f29177d519904535e9fd7c73c3
attempt registration: 0x0deb5d9f9817e6e87e7fbbaf33a70429801046660c697eee346b7c65eb7a76a8
corrected attempt registration: 0x28f997f110524beffecd7fd68dfbd254caf9229e3f980092721718cef079f3ef
corrected evaluation: 0x103d0a54adb2001684f772bff8ae88bb593e7758a13bd9f22814d3ebbea2ade0
close study: 0x95249586ef000343564293094dbb46ce7c8bf3d104b664ea7604f135d3a4a21b
reclaim settled remainder: 0xaf55c110125fd927f20763158b391ee4bbbae336a028f71b607c111e790c223b
```

Both attempts reached finality and were archived as `INCONCLUSIVE`; the corrected
archive evidence digest was
`518fe7fb776c5f36599e9ba4cb137d8b92943e13e66e064061fba74ff6b771a3`.
Because the submitted URLs were robots.txt windows rather than scientific records,
no reward was issued and no ResearchPool reward child transaction or researcher
withdrawal exists. After close finality, the canonical pool readback was `0 GEN`
following the finalized reclaim above.

## Requires recipient environment

The live frontend is hosted at `https://the-reprove.vercel.app` and reads the
verified Studionet 61999 deployment addresses from the Production environment.
Deployed-source parity hashes and a reward-eligible lifecycle with a finalized
ResearchPool child transaction remain required before this report can support a
4/5 claim.
