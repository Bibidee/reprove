# MEGA PROMPT — Finish REPROVE for submission

You have been given an already-built REPROVE repository. Treat it as a near-complete release candidate, not as a blank starter. Your job is to finish current-toolchain compatibility, deploy the real contracts to GenLayer Studionet 61999, deploy the frontend to Vercel, execute a live end-to-end proof, and leave a submission-ready repository with evidence.

## Non-negotiable network

Use **GenLayer Studionet, chain ID 61999** only.

- RPC: `https://studio.genlayer.com/api`
- Explorer: `https://explorer-studio.genlayer.com`

Do not use Studio Dev / 61997. Stop rather than silently switching networks.

## Non-negotiable clean-room frontend

Do not copy, inspect for inspiration, adapt, import or structurally reproduce any frontend from any repository under `github.com/ometere123`.

Do not use PATHCLOCK as a frontend reference. Preserve REPROVE's distinct research-journal visual language, cool glacier/navy/cobalt/violet/magenta/cyan palette, contextual navigation, Replication Atlas, protocol paper, notebook and archive-record interaction model.

Do not add dashboard/sidebar/control-room patterns. Do not add `/console`, `/release`, `/proof`, `/dashboard`, `/account`, `/protocol`, `/settings`, `/incidents`, `/settlements` or `/agreements`.

The only public application routes are:

- `/`
- `/lab`
- `/claim/[studyKey]`
- `/attempt/[attemptKey]`
- `/archive/[recordKey]`

Run `python3 scripts/release_check.py` repeatedly. Treat a guard failure as a release blocker.

## Product invariants you may not weaken

REPROVE evaluates a replication under a frozen protocol. It does not claim universal scientific truth.

There are four semantic outcomes and they must remain distinct:

- `REPLICATED`
- `FAILED_TO_REPLICATE`
- `PROTOCOL_DEVIATION`
- `INCONCLUSIVE`

`FAILED_TO_REPLICATE` means the protocol was satisfied, evidence was sufficient, required evidence was present, but the registered outcome criterion was not met. It must never be used as a substitute for protocol deviation or insufficient evidence.

`INCONCLUSIVE` is a first-class safe non-decision. Never convert it into failure, refund, positive result or reward.

The leader and validators must independently retrieve public evidence and compare the material assessment fields. Preserve the evidence snapshot receipts: each source binds URL/origin/fetch status, bounded content-window SHA-256 and length; validator receipts and the aggregate snapshot digest must match the leader. Do not replace this with schema validation, range checking, JSON-format checking or a single LLM call whose answer is merely stored.

Do not add a fallback winner/result. Malformed or incoherent assessment output must resolve safely, not default to REPLICATED or FAILED_TO_REPLICATE.

The LLM must never choose a wei amount. Reward amounts are frozen in StudyRegistry. ResearchPool applies them deterministically.

Valid positive and negative replications must remain reward-neutral: `REPLICATED` and `FAILED_TO_REPLICATE` are eligible for the same fixed reward. `PROTOCOL_DEVIATION` and `INCONCLUSIVE` are not automatically reward-eligible.

Keep the finalized-parent boundary. `ReplicationEngine` must emit the ResearchPool registration message with `on="finalized"`. A merely ACCEPTED evaluation must not create the ResearchPool child transaction. Then verify that deterministic child transaction itself reaches FINALIZED before presenting the archive/reward as fully settled.

## Phase 1 — inspect before changing

Read, in order:

1. `README.md`
2. `ARCHITECTURE.md`
3. `CLEAN_ROOM_FRONTEND.md`
4. `REVIEW_TARGET.md`
5. `DEPLOYMENT_RUNBOOK.md`
6. all three contracts
7. unit/direct tests
8. the frontend route/surface/domain/consensus code
9. `scripts/release_check.py`

Then write a short internal gap list. Do not redesign working architecture because of personal taste.

## Phase 2 — current GenLayer compatibility

Use current official GenLayer docs and installed SDK/tooling as the authority. The handoff targets the stable GenLayer JS `1.1.8` interface and Python/test versions recorded in `requirements.txt`, but if the current official Studionet toolchain requires a compatibility change, make the smallest correct change and document it.

Critical checks:

- contract schemas generate successfully;
- no `from __future__ import annotations` / string-u256 schema regression;
- nondeterministic web and LLM calls occur only inside nondet execution;
- storage writes and cross-contract messages occur after consensus in deterministic context;
- cross-contract view calls and finalized-only emits match the current SDK syntax;
- EOA value withdrawal syntax is supported on Studionet;
- GenVM linter has no deployment-blocking errors;
- no evidence retrieval redirects/private hosts are accidentally treated as authenticated independent evidence;
- optional frozen `allowed_origins` / `required_origins` policies are enforced exactly and cannot be bypassed by paths, ports, userinfo or alternate host syntax.

Run:

```bash
python3 -m py_compile contracts/*.py
pytest -q tests/unit
genvm-lint check contracts/study_registry.py
genvm-lint check contracts/replication_engine.py
genvm-lint check contracts/research_pool.py
pytest -q tests/direct
python3 scripts/release_check.py
```

If a supplied direct test needs adapting to current fixture APIs, fix the test and contract only as necessary. Add tests instead of deleting difficult coverage.

Add/confirm tests for at least:

- duplicate study key;
- immutable study content / close-only lifecycle;
- non-creator close rejected;
- duplicate attempt key;
- non-owner attempt submission rejected;
- closed study blocks new attempts;
- 1 and 9 evidence items rejected;
- duplicate exact evidence URL rejected;
- non-HTTPS URL rejected;
- localhost/private ranges rejected;
- unsupported evidence kind rejected;
- missing source → safe inconclusive path;
- contradictory evidence → safe inconclusive path;
- protocol deviation distinct from negative replication;
- malformed LLM output never becomes a positive verdict;
- validator disagreement rejects consensus;
- ResearchPool rejects calls from non-engine address;
- duplicate archive record rejected;
- accepted/provisional evaluation cannot register a pool record;
- reward cap;
- insufficient pool balance;
- equal reward for REPLICATED / FAILED_TO_REPLICATE;
- zero automatic reward for PROTOCOL_DEVIATION / INCONCLUSIVE;
- double withdrawal rejected;
- multiple studies sharing the pool remain accounting-isolated.

## Phase 3 — frontend correctness

Work from `web/`.

```bash
npm install
npm run typecheck
npm run build
```

Fix every build/type error. Keep the five routes only.

The browser must talk directly to GenLayer. Do not add Supabase, Firebase, Prisma, Postgres, MongoDB, server wallets, hidden AI endpoints, adjudication APIs, cron jobs or a backend source of truth.

Use injected EIP-1193 wallet only. Do not add WalletConnect, Snaps or private keys to the frontend.

Contract state is authoritative. `localStorage` may cache the last transaction ID for recovery, but it must never decide protocol state, verdict, finality, reward or ownership.

Make transaction UX correct:

- A write begins with wallet signature.
- Submitted/consensus states are visible.
- ACCEPTED is presented only as provisional.
- If appealable, the UI may expose an appeal action with the SDK-provided minimum bond.
- READY_TO_FINALIZE can expose finalization.
- FINALIZED must be separately verified.
- After finalization, reread contract state.
- The archive page must be sourced from ResearchPool, not from a client-side assumption that the assessment finalized. Do not label the child record fully settled until its own transaction is verified FINALIZED in the live proof.
- UNDETERMINED must never create a success banner or reward claim.

Inspect responsive behaviour at phone, tablet and desktop widths. Do not compress the desktop replication matrix into unreadable columns; allow controlled horizontal scroll or a mobile record view.

Accessibility: keyboard interaction, field labels, visible focus, status text not colour-only, readable error messages and semantic headings.

## Phase 4 — deploy to Studionet 61999

Use a funded deployment wallet and the current GenLayer CLI. Select Studionet and double-check chain ID 61999 before any deployment.

Use `deploy/deployScript.ts` or a minimally corrected equivalent. Deployment order must stay:

1. StudyRegistry
2. ReplicationEngine with Registry and blank Pool
3. ResearchPool with Registry + Engine
4. `ReplicationEngine.set_pool_once(ResearchPool)`

Every deployment and configuration transaction must reach FINALIZED. Do not record an ACCEPTED deployment as canonical.

After deployment, populate `deployments/studionet.json` with real addresses and transaction IDs and verify all explorer pages.

Read back:

- Registry stats
- Engine config
- Pool config

The address graph must be mutually correct.

## Phase 5 — Vercel

Configure and deploy the `web/` directory with:

```text
NEXT_PUBLIC_GENLAYER_CHAIN_ID=61999
NEXT_PUBLIC_GENLAYER_RPC_URL=https://studio.genlayer.com/api
NEXT_PUBLIC_GENLAYER_EXPLORER=https://explorer-studio.genlayer.com
NEXT_PUBLIC_STUDY_REGISTRY_ADDRESS=<registry>
NEXT_PUBLIC_REPLICATION_ENGINE_ADDRESS=<engine>
NEXT_PUBLIC_RESEARCH_POOL_ADDRESS=<pool>
NEXT_PUBLIC_REPROVE_DEMO=false
```

The production deployment must build from the final source commit. Record the Vercel production URL in the README and deployment manifest or a release record.

Do not leave stale contract addresses in Vercel.

## Phase 6 — live demonstration

Use a non-sensitive synthetic research example. The bundled `web/public/demo-evidence/` fixture is intended for this.

For a stronger submission, serve some evidence from the Vercel origin and at least one key source from the public GitHub raw origin after the repository is pushed, so the demo does not pretend one host is multiple independent sources.

Suggested flow:

1. Wallet A registers a study with immutable protocol/outcome/evidence rules.
2. Wallet A funds the replication pool.
3. Wallet B begins an attempt.
4. Wallet B submits typed public evidence and a reported result.
5. Capture the evaluation transaction while ACCEPTED/provisional and show that the UI says it is not final.
6. If possible, verify appeal controls without actually disrupting the canonical demo; otherwise document the SDK capability and preserve a clean final path.
7. Finalize the evaluation.
8. Wait for the finalized-only child message, identify the ResearchPool child transaction, verify that child reaches FINALIZED, and only then treat the archive/reward as fully settled.
9. Open `/archive/[recordKey]` directly in a fresh/incognito browser without a wallet. It must render from chain state.
10. Verify the fixed reward was reserved only after finalization.
11. Withdraw a small claimable reward; verify no double withdrawal and no cross-study accounting leak.

Also execute at least one safe negative/uncertain path. Prefer an `INCONCLUSIVE` attempt caused by a deliberately unavailable or insufficient evidence source, and show it does not receive a reward.

## Phase 7 — evidence bundle for reviewers

Update README/release docs with:

- final source commit SHA;
- canonical addresses;
- deployment transaction links;
- engine→pool configuration transaction;
- production Vercel URL;
- one study registration tx;
- one pool funding tx;
- one attempt-creation tx;
- one evaluation tx with its provisional and final states;
- archive record key;
- reward/withdrawal tx where applicable;
- final Direct Mode count;
- CI run link.

Make it trivial for a reviewer to verify source ↔ deployment ↔ frontend.

## Phase 8 — final adversarial audit

Before submission, review this repository as if trying to reject it.

Ask:

- Could a single operator secretly decide the result? If yes, fix it.
- Does the validator actually reconstruct the material result? If not, fix it.
- Can missing evidence accidentally become FAILED_TO_REPLICATE? If yes, fix it.
- Can ACCEPTED trigger reward/archive? If yes, fix it.
- Can the UI claim the archive/reward is fully settled before the ResearchPool child transaction is FINALIZED? If yes, fix it.
- Can the same finalized outcome be registered twice? If yes, fix it.
- Can reward accounting exceed deposited balance? If yes, fix it.
- Can a researcher edit a frozen study? If yes, fix it.
- Can one evidence URL count twice? If yes, fix it.
- Can another wallet submit somebody else's notebook? If yes, fix it.
- Can a public archive record disappear because it depended on localStorage? If yes, fix it.
- Does any page look structurally like PATHCLOCK or another `ometere123` frontend? If yes, redesign that page without importing/copying from those projects.

Then rerun every test/build/guard and only call the repository submission-ready if all live proofs are real.

## Deliverable back to the owner

Return one compact release report containing:

- submission-ready YES/NO;
- final commit SHA;
- exact test/lint/build results;
- Studionet 61999 contract addresses;
- explorer links;
- production URL;
- canonical demo study/attempt/archive keys;
- canonical transaction hashes;
- any remaining limitation, even if small.

Do not claim a test, deployment, finalization, frontend write or archive record that you did not actually verify.
