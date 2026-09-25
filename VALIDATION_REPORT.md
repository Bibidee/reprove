# REPROVE validation report

This report records the current repository checks and the corrected live
Studionet 61999 smoke lifecycle. It does not claim the release gate is
complete until the creator closes the study and the final canonical readback
is recorded.

## Verification

- `pytest -q tests/unit`: 38 passed.
- `pytest -q tests/direct`: 23 passed.
- GenVM lint and validation passed for StudyRegistry, ReplicationEngine, and
  ResearchPool. The generated schemas contain 7, 8, and 9 methods
  respectively.
- The adversarial suite covers unavailable, changed, conflicting, insufficient,
  and prompt-injection evidence; exact bounded evidence-window hashes; replay
  protection; unauthorized engine/reclaim calls; duplicate records; reward
  caps; pool insolvency; and excessive withdrawals.
- Frontend `typecheck` and production `build` pass with the real Next.js
  toolchain. The build exposes `/`, `/lab`, `/claim/[studyKey]`,
  `/attempt/[attemptKey]`, and `/archive/[recordKey]`.
- `scripts/release_check.py`: `RELEASE CHECK OK`.

## Corrected deployment

Network: GenLayer Studionet, chain `61999`
RPC: `https://studio.genlayer.com/api`
Frontend: [reprove.vercel.app](https://reprove.vercel.app)
READY deployment: `reprove-ax0k88w4j-bibidees-projects.vercel.app`

The exact addresses, finalized deployment/configuration transaction hashes,
source hashes, schema hashes, and method counts are recorded in
`deployments/studionet.json`. All three deployed-source parity checks passed;
Engine → ResearchPool binding is verified.

## Live two-wallet lifecycle

Study: `final-smoke-2026f` — Final payout ledger smoke claim
Creator: `0xFf203Bb65942F50CB81A8AF98c5F5bd9d8a79b54`
Researcher: `0x4A7D76b8C4668a3426d6d54eC24b41Fa87b532f5`
Pool: `0xE8516139d8e6A70de9DEC8FA67535409df250f81`

### Registration, funding, and attempt

- Registration: `0x5499c2606d1db42c832af5c1f9f989e2e5175e86215cafaf6037657adc6423cf` — finalized, successful.
- Funding: `0x4da5f506b69ddd6633eaa8458eb831c18e427f59aa4cf67d57ddddac43eb3a8d` — 1 GEN, finalized, successful.
- Attempt `final-smoke-attempt-01`: `0x447de1935669e76a940531e08e18d33c1919b9cbd231657f65f51ff7fa88ec8e` — finalized, successful.

### Evidence and evaluation

The submitted evidence contained all four required kinds — DATASET, METHOD,
ANALYSIS, and RESULT_TABLE — across the raw GitHub and jsDelivr origins.

- README evidence window: 4,962 chars, SHA-256
  `6972e64492f2cdde1f5bba5c329abcfad572cc854925342d8ffd0a9d16f63c94`.
- Validation-report evidence window: 5,033 chars, SHA-256
  `28a0e9cda33c414611fe0f8676880761661478c3009102cb52719fab63e45a34`.
- Parent evaluation: `0x4cf96721c5f8b057be228f43b99e2be5ec1073df9d74cb4f5040e961ceb795d4` — finalized, successful, `REPLICATED`.
- Evidence snapshot digest: `79a2bfea2974b20f17039cfccc8038da0b86ac098741fb251a490255a3ccd8fa`.
- Finalized ResearchPool child: `0x4e7b8e16a22c81d446bce40b02fa097c99c07986efb5e0d1f5981ef44a7d3fe6` — `register_finalized_outcome`, finalized, successful.
- Assessment digest: `b52d4b4362da33b9bb03d063353cd54a1f9dc66c56980b56deef9c04f53a4442`.
- Archive: [final-smoke-2026f:final-smoke-attempt-01](https://reprove.vercel.app/archive/final-smoke-2026f%3Afinal-smoke-attempt-01).

The archive readback showed `SATISFIED`, `SUFFICIENT`, outcome `YES`, verdict
`REPLICATED`, reward reserved `1 GEN`, and the same evidence snapshot digest.

### Withdrawal

- Withdrawal: `0x5e58afe98e570e7df3afa8424d23992e6204af3ac2a2ccaad49c676371744c3b` — 1 GEN, finalized, successful.
- Canonical post-withdrawal reads: `get_claimable(researcher) = 0`,
  `get_study_pool.available_wei = 0`, `rewarded_attempts = 1`.

No reclaim transaction is expected because the entire 1 GEN pool was withdrawn;
submitting a zero-balance reclaim would be an unnecessary failing transaction.

### Closure and final canonical reads

- Study close: `0x173532a9338f44e2cf164f39a1b5629227bfe20efc270af6a2df3aae9637da07` — finalized, majority agree, successful.
- Canonical `get_study(final-smoke-2026f)`: `CLOSED`.
- Canonical `get_attempt(final-smoke-attempt-01)`: `ASSESSED`.
- Canonical `get_study_pool(final-smoke-2026f)`: `available_wei = 0`,
  `rewarded_attempts = 1`.
- Canonical `get_claimable(researcher)`: `0`.
- The live production page now reads `CLOSED`, shows finalized reward state,
  and exposes reclaim only as a disabled-by-balance final action; no reclaim
  transaction was submitted because no settled balance remained.

The final commit and push are now the remaining repository handoff actions.

An earlier deployment-scoped browser-cache defect displayed a stale evaluation
transaction when the same attempt key was reused across deployments. The
frontend now scopes cached evaluation IDs by the configured Engine address,
including the finality-check path. The finality mapper also consumes
GenLayer's canonical `status_name` field, while archive, reward, and lifecycle
displays remain canonical contract reads.
