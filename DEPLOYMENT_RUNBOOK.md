# Deployment runbook — Studionet 61999

## 1. Verify the network before any write

Target only:

- GenLayer Studionet
- chain ID `61999`
- RPC `https://studio.genlayer.com/api`
- explorer `https://explorer-studio.genlayer.com`

Do not substitute Studio Dev 61997.

## 2. Fresh install and validation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m py_compile contracts/*.py
pytest -q tests/unit
genvm-lint check contracts/study_registry.py
genvm-lint check contracts/replication_engine.py
genvm-lint check contracts/research_pool.py
pytest -q tests/direct
python3 scripts/release_check.py

cd web
npm install
npm run typecheck
npm run build
cd ..
```

If any current SDK/tooling drift causes a failure, fix it minimally and rerun the complete suite. Do not redesign the product or weaken contract invariants to silence a test.

## 3. Deploy the three contracts

Use the GenLayer CLI with the Studionet network selected and the funded deployer configured. The included `deploy/deployScript.ts` deploys in this order:

1. StudyRegistry
2. ReplicationEngine(registry, empty pool)
3. ResearchPool(registry, engine)
4. `ReplicationEngine.set_pool_once(pool)`

The script waits for finalization and writes `deployments/studionet.json`.

## 4. Verify deployment bindings

Read:

- `ReplicationEngine.get_config()` — registry and pool addresses must match the manifest.
- `ResearchPool.get_config()` — registry and engine addresses must match the manifest.
- `StudyRegistry.get_stats()` — must respond successfully.

Confirm the deployed source corresponds to the final repository commit.

## 5. Configure Vercel

Set:

```text
NEXT_PUBLIC_GENLAYER_CHAIN_ID=61999
NEXT_PUBLIC_GENLAYER_RPC_URL=https://studio.genlayer.com/api
NEXT_PUBLIC_GENLAYER_EXPLORER=https://explorer-studio.genlayer.com
NEXT_PUBLIC_STUDY_REGISTRY_ADDRESS=<canonical registry>
NEXT_PUBLIC_REPLICATION_ENGINE_ADDRESS=<canonical engine>
NEXT_PUBLIC_RESEARCH_POOL_ADDRESS=<canonical pool>
NEXT_PUBLIC_REPROVE_DEMO=false
```

Deploy `web/` as the Vercel project root.

## 6. Live proof path

Use at least two wallets where possible: study creator/funder and replicator.

Create a study with a frozen protocol and fixed reward. Fund the study. Begin an attempt. Publish evidence on public HTTPS URLs. Submit the attempt. Capture the evaluation transaction while provisional. Verify the UI explicitly says the result is not final. Allow or trigger parent evaluation finalization. Verify the ResearchPool child transaction is created only after parent finalization, then separately verify that deterministic child reaches FINALIZED before treating the archive/reward as fully settled. Verify reward reservation is equal for REPLICATED and FAILED_TO_REPLICATE and zero for deviation/inconclusive paths. Withdraw a small claimable amount and verify accounting.

## 7. Evidence-source quality

For the submission demo, do not use only one origin. The bundled fixture can be served by Vercel, but mirror at least one core source to a second public origin such as the repository's raw GitHub content. Register the evidence policy before the attempt and keep the URLs stable during the demo.

When possible, freeze `allowed_origins` and at least one `required_origin` in the demo study after the final production origins are known. After evaluation, capture the stored evidence snapshot digest and source receipts so reviewers can see that the assessment commits to the exact bounded evidence windows used during consensus.
