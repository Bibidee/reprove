# REPROVE validation report

## Canonical V2 submission proof

The audited contract source commit was:

`b47515c5fcf5146c64f75e300fc23f7d69daa85b`

No production contract source was changed for the deployment or evidence
update. The fresh corrected Studionet deployment is:

- StudyRegistry: `0x951c60F2f7F61265734afb6d6Bd14790F1641110`
- ReplicationEngine: `0xC5105F140a8c6c22fC17f255D7A3C8359DF3AEe4`
- ResearchPool: `0x8B7c19f8876ABD24CCb176359F357377C5438b6F`
- Engine -> Pool configuration: `0x5be901423a92cd2bbd1afcb63fee42bc201ea5add6ac1ee190c3abaf37ff5487`

All four deployed binding reads matched the fresh addresses above. The
configuration transaction finalized successfully.

The canonical clean lifecycle used two distinct wallets:

- Creator / funder: `0x7c65ce913f5665c11f1219048112c84cd6cb2a4b`
- Researcher: `0x2cd419603eba593074653930ddc4073d4fd8fc60`

Study: `reprove-v2-final-20261006212039`

Attempt: `reprove-v2-final-attempt-20261006212039`

Record: `reprove-v2-final-20261006212039:reprove-v2-final-attempt-20261006212039`

The finalized lifecycle transactions are:

- Registration: `0x45c78a9fe756f37839bcba9b47d277fcdf36193b2599deaa6bf07e4223c4f2f6`
- Funding, `0.02 GEN`: `0xca7b77c04f92698310a3b4c282049b5186a97405bbef420586bc4e5a4a008eaf`
- Begin attempt: `0x42d5d0531c6f9ca031e4fb824c1402c4e3974a2c152ac8c157371416cd1c1d3d`
- Capsule commitment: `0x2b9d0f64241f06fbd6c71df31b9d499ac3ae0e81e4981856e1117991b165227d`
- Evaluation: `0x2f6cd29903f0b660f34cc9f5b7294bf5779378d4e437f04a5150c11243c9f377`
- Finalized ResearchPool child: `0x195cfa750db8d191abb55e95dd16243444010c7bd45a33587704b7f70c021f91`
- Researcher withdrawal, `0.01 GEN`: `0xef48cb626032b6ae5b4bceb25d2776f27d3c0e3fcc1f27f32215d2e2ab75de18`
- Study closure: `0xc0f5e98b70bac6d3e5f5a49227ed1dde92f4be0b0b21bd6143eb44a7a48fd782`
- Creator reclaim, `0.01 GEN`: `0x6f620de9ae7605581f0efdaff88dc34d38b628150db5fc77db3b1bf6642fcea8`

Frozen and finalized identifiers:

- Study digest: `6cc38e4bb71db0377dcae3af741300254e0034e5232afb2b0687148f3d735756`
- Capsule digest: `d5b0adc7679ce24a7278244711210e37058c18d5eb82123130a6aa8d37a53d53`
- Assessment digest: `37bd7f63808d45eba28d81ebba13ad1fcbde70eff5a2fe04815b5ba632bf0235`
- Verdict: `REPLICATED`
- Reward reserved: `10000000000000000` wei (`0.01 GEN`)
- Amount withdrawn: `0.01 GEN`
- Amount reclaimed: `0.01 GEN`

The final canonical reads were:

- StudyRegistry: study status `CLOSED`, revision `2`.
- ReplicationEngine: attempt state `ASSESSED`; `active_attempts = 0`,
  `assessed_attempts = 1`.
- ResearchPool: certificate version `2`, verdict `REPLICATED`,
  `finalized_records = 1`, `available_wei = 0`, and `rewarded_attempts = 1`.
- Researcher claimable balance: `0`.
- Post-reclaim readiness: ineligible only for `NO_REMAINING_BALANCE`; there
  were no active-attempt or pending-archive reasons.

The evaluation independently recomputed the frozen fixed-point result:

- Profile: `ONE_SAMPLE_THRESHOLD`
- Mean: `879200 / 10`
- Threshold: `500 / 1000`
- Threshold outcome: `YES`
- Reported result match: `YES`
- Protocol compliance: `SATISFIED`
- Evidence sufficiency: `SUFFICIENT`
- Required evidence: `YES`
- Provenance: `VERIFIED`
- Artifact integrity: `VERIFIED`

The production frontend is [https://reprove.vercel.app](https://reprove.vercel.app).
The canonical public archive is:

[https://reprove.vercel.app/archive/reprove-v2-final-20261006212039%3Areprove-v2-final-attempt-20261006212039](https://reprove.vercel.app/archive/reprove-v2-final-20261006212039%3Areprove-v2-final-attempt-20261006212039)

The production home, lab, clean study page, and archive page were opened from
a fresh unauthenticated browser context. The current production domain did
not require Vercel authentication.

## Additional live evidence

The earlier live study `reprove-v2-live-20261006200820` is retained as
additional evidence only. It completed a valid `REPLICATED` attempt, reward
withdrawal, closure, and reclaim, but it also contained one earlier finalized
`INCONCLUSIVE` attempt. Its final counters were therefore `0 active / 2
assessed / 2 finalized`, which is internally consistent but is not the
canonical submission proof.

## Historical evidence

Earlier V1-style receipts and the pre-audit deployment remain historical
provenance only. They are not mixed with the canonical V2 proof above.

## Verification results

- Unit tests: 38 passed.
- Direct tests: 71 passed.
- GenVM lint/validation: all three contract checks passed.
- Release check: passed.
- Frontend typecheck: passed.
- Frontend production build: passed.
- `npm audit --omit=dev`: 0 vulnerabilities.
