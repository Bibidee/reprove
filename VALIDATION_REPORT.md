# Validation report

This handoff is intentionally not presented as live-deployed.

## Passed locally

```text
python3 -m py_compile contracts/*.py
PASS

pytest -q tests/unit
37 passed

python3 scripts/release_check.py
RELEASE CHECK OK
Routes: /, /lab, /claim/[studyKey], /attempt/[attemptKey], /archive/[recordKey]
Clean-room route/component/palette guards passed.

python3 -m py_compile tests/direct/*.py
PASS (syntax)

TypeScript compile against temporary local declarations
PASS
```

## Requires recipient environment

The local environment does not contain `genlayer`, `gltest` or `genvm-lint`, so Direct Mode and GenVM lint must be run after installing `requirements.txt`.

A package-registry `npm install --package-lock-only` attempt timed out in this environment, so a real Next.js dependency install/production build is also a required finishing step. Do not treat the temporary stub compile as a substitute for `npm run typecheck` and `npm run build`.

Live Studionet deployment, transaction finality, ResearchPool child finality and Vercel hosting require the recipient's funded wallet and deployment credentials.
