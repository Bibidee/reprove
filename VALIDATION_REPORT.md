# REPROVE validation report

This report records the current repository checks and the completed live smoke-test lifecycle on Studionet 61999. It is an evidence record, not a claim that every remaining release gate is complete.

## Current local and production checks

- Unit tests: pytest -q tests/unit — 37 passed.
- Direct integration tests: pytest -q tests/direct — 13 passed.
- Release check: scripts/release_check.py — RELEASE CHECK OK.
- The production frontend is served at https://the-reprove.vercel.app.
- The latest correct Vercel production deployment is reprove-2fokk0lnv-bibidees-projects.vercel.app, reported READY.

The clean-room release check covers the expected frontend routes, including /, /lab, /claim/[studyKey], /attempt/[attemptKey], and /archive/[recordKey]. A fresh source-parity deployment of all three contracts, plus the final adversarial evidence matrix, remains a release gate.

## Live smoke-test lifecycle

Network: Studionet 61999  
Study key: smoke-test-2026e  
Study title: Preregistered replication smoke test

Creator: 0xFf203Bb65942F50CB81A8AF98c5F5bd9d8a79b54  
Researcher: 0x4A7D76b8C4668a3426d6d54eC24b41Fa87b532f5

### Registration and funding

- Registration transaction: 0xe605e15a8ad93958a37ded4c82f2537164566e85dec39e85d129cb3d181be3dd
- Funding transaction: 0x58442aa98023e25e99b5341e24bf5655db85998004288f39ef30094d96c2822b
- Both transactions finalized successfully.
- The funded research pool contained 1 GEN.

### Attempt matrix

- Attempt 01: 0x7b46ee59f098b66a7881cb64224f9d939f6aad98d7cc378f3ed43b47f8bddf5b — assessed INCONCLUSIVE; no reward.
- Attempt 02: 0xb409d251db7bba24a625b4fb6b7263f59d074f27d4c531fe855b0f713ecdb3df — parent evaluation UNDETERMINED; no record or reward.
- Attempt 03: 0x7673dfe5ef39214e28adda331129d241800dec3643f4311fea90f9f6eaac72f1 — assessed INCONCLUSIVE; no reward.
- Attempt 04: 0x08fa232eb54e7741991b6c4f9ef49efecef90f8cfef772bcc819ad9e2019e4a4 — complete two-origin evidence package; assessed REPLICATED.

Attempt 04 evidence used dataset, method, analysis, and result-table receipts from raw GitHub and jsDelivr, with sample size 1000, effect 13.3%, and zero reported errors.

### Evaluation and reward reservation

- Parent evaluation transaction: 0x32807397fdad7ae9f045b37ef996f2860c9fd1214bbb88a18900399ea8ca1e16
- Result: REPLICATED
- Evidence sufficiency: SUFFICIENT
- Protocol: SATISFIED
- Required evidence: YES
- Evidence snapshot digest: 4c4d525aef58d74bc2ab708ebe3303a6a63d1d6d0a6071d48bd3dd40148f1a29
- ResearchPool child transaction: 0x8bb14eed9995f1bdc75756b6e5683d368cd70df8f10b2d805ed4dfda9c35c211
- Archive record: https://the-reprove.vercel.app/archive/smoke-test-2026e%3Aattempt-2026e-04
- The archive record showed REWARD RESERVED for 1 GEN.

### Withdrawal and close

- Withdrawal transaction: 0x596679f34d5899c800de578184c802a68aa0c6c14e8fc580c2ad08fb70b85676
- Withdrawal finalized successfully for 1 GEN.
- Post-withdrawal reads confirmed get_claimable(researcher) = 0.
- The study pool read confirmed available_wei = 0 and rewarded_attempts = 1.
- Close transaction: 0xc6e521e4979488a59a4c3b34401aeedb5740a1f4d947815e413e8fad32cd73a3
- Close finalized successfully; the canonical page now reports CLOSED.

No reclaim transaction was submitted: the entire 1 GEN pool had already been withdrawn, so there was no remaining settled balance. Submitting a zero-balance reclaim would have been an unnecessary failing transaction.

## Deployment status and remaining gates

deployments/studionet.json remains the last verified canonical deployment manifest. A fresh three-contract source-parity deployment was started, but the fresh Engine and Pool addresses did not produce verifiable deployed code and must not be treated as released addresses.

Remaining release work:

1. Complete and verify a fresh source-parity deployment of Registry, Engine, and ResearchPool.
2. Re-run the clean-checkout GenVM/schema and frontend checks after that deployment.
3. Expand the adversarial lifecycle matrix and attach its receipts.
4. Commit and push the final evidence updates without including generated build artifacts.

