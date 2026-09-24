# REPROVE handoff inventory

This package is a near-complete REPROVE release candidate targeting **GenLayer Studionet 61999**.

Included:

- Three Intelligent Contracts: `StudyRegistry`, `ReplicationEngine`, `ResearchPool`.
- Five-route clean-room frontend: `/`, `/lab`, `/claim/[studyKey]`, `/attempt/[attemptKey]`, `/archive/[recordKey]`.
- Injected-wallet Studionet integration and transaction/finality handling.
- Evidence-bound semantic evaluation with four distinct outcomes.
- Fixed reward pool and pull-withdrawal logic.
- Direct/unit tests, CI workflow and clean-room release guard.
- Synthetic public demo evidence.
- Studionet deployment script and canonical deployment manifest template.
- Vercel environment template.
- Architecture, deployment, review, validation and submission documents.
- `MEGA_PROMPT_FOR_AGENT.md` for the recipient's finishing agent.

Local handoff checks completed:

- Python contract/script syntax: passed.
- Unit tests: 37 passed.
- Clean-room route/component/palette guard: passed.
- Direct-mode files: syntax checked; current GenLayer runtime must be installed by finishing agent.
- Live Studionet deployment and Vercel hosting are intentionally left for the recipient's funded wallet/agent.
