# REPROVE

REPROVE is a GenLayer-native preregistration and scientific replication protocol designed for GenLayer Studionet (chain ID **61999**).

A study creator freezes a claim, replication protocol, outcome rule, typed evidence policy, optional exact origin allow/require lists, and optional fixed reward policy before results are known. A replicator opens a notebook, publishes typed public evidence, and submits a reported result. GenLayer validators independently retrieve the same public evidence and determine one of four bounded outcomes:

- `REPLICATED`
- `FAILED_TO_REPLICATE`
- `PROTOCOL_DEVIATION`
- `INCONCLUSIVE`

The semantic evaluation does **not** claim universal scientific truth. It evaluates one replication against one frozen protocol and outcome rule. Each consensus assessment also commits to bounded evidence-window SHA-256 receipts, so the stored assessment digest binds the exact evidence representation used by consensus rather than only the submitter's URLs.

## Architecture

REPROVE uses three coherent Intelligent Contracts:

1. `StudyRegistry` — immutable preregistration and study lifecycle.
2. `ReplicationEngine` — evidence retrieval, leader/validator semantic reconstruction, bounded outcome storage, finalized-only message emission.
3. `ResearchPool` — creator-funded study pools; receives finalized-only outcomes, publishes public archive records, reserves equal fixed rewards for valid positive and negative replication outcomes, supports safe closed-pool reclaim, and uses pull withdrawals.

The parent-finality boundary is intentional: `ReplicationEngine` emits `register_finalized_outcome(...)` to `ResearchPool` with `on="finalized"`. A merely accepted/provisional evaluation cannot create the ResearchPool child transaction. The child transaction is deterministic but still has its own GenLayer lifecycle; the live release proof must verify that child reaches `FINALIZED` before describing the archive/reward as fully settled.

## Frontend routes

Exactly five public routes are used:

- `/`
- `/lab`
- `/claim/[studyKey]`
- `/attempt/[attemptKey]`
- `/archive/[recordKey]`

There are no dashboard, console, release, proof, account, protocol, settings or copied project routes.

## Network

- Network: GenLayer Studionet
- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`
- Explorer: `https://explorer-studio.genlayer.com`

Do not deploy this handoff to Studio Dev / chain 61997.

## Local verification

```bash
python3 -m py_compile contracts/*.py
pytest -q tests/unit
python3 scripts/release_check.py
```

After installing GenLayer development dependencies:

```bash
pip install -r requirements.txt
genvm-lint check contracts/study_registry.py
genvm-lint check contracts/replication_engine.py
genvm-lint check contracts/research_pool.py
pytest -q tests/direct
```

Frontend:

```bash
cd web
npm install
npm run typecheck
npm run build
npm run dev
```

## Deployment

The repository intentionally contains **no private key**. The current verified
Studionet deployment, including finalized deployment/configuration receipts,
source hashes, schemas, and Engine → ResearchPool binding, is recorded in
`deployments/studionet.json`. See `DEPLOYMENT_RUNBOOK.md` and
`MEGA_PROMPT_FOR_AGENT.md`.

The deployment script writes canonical addresses and transaction IDs to
`deployments/studionet.json` after all three contracts and the engine-to-pool
configuration transaction finalize.

## Production frontend

The verified production frontend is deployed at [the-reprove.vercel.app](https://the-reprove.vercel.app).
The current production deployment is `reprove-ax0k88w4j-bibidees-projects.vercel.app`
(READY, 2026-09-24), with the public alias at the-reprove.vercel.app.
The live smoke-test receipts and frontend behavior are recorded in
`VALIDATION_REPORT.md`, including the finalized close-study receipt and the
zero-balance reclaim decision.

## Demo evidence

`web/public/demo-evidence/` contains a synthetic, non-medical example dataset/method/result package for exercising the product. It is a UI and consensus fixture only. For the live demo, the agent should publish at least one evidence source from a second independent public origin before evaluating the seeded attempt, so the evidence story is stronger than a single-origin demonstration.

## Important boundaries

- `ACCEPTED` is provisional and must never be presented as final.
- `UNDETERMINED` is a first-class non-decision.
- `FAILED_TO_REPLICATE` is not a protocol failure.
- `PROTOCOL_DEVIATION` is distinct from a negative replication result.
- `INCONCLUSIVE` must not release a reward.
- The LLM never chooses payout amounts. Reward amounts are frozen in the study and applied deterministically.
- Local browser storage is never the source of truth. It may cache a transaction ID only; contract state and GenLayer transaction state remain authoritative.
