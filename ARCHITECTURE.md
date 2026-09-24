# REPROVE Architecture

## Product thesis

Scientific replication has adversarial incentives: original authors, replicators, funders and observers can prefer different outcomes. REPROVE does not ask one operator to decide whether a replication "counts". The study protocol is frozen first; evidence is published; GenLayer validators independently reconstruct whether the attempt followed the registered protocol and what the registered evidence supports.

## Contract boundaries

### StudyRegistry

Owns immutable preregistration facts. Creation freezes the claim, protocol, outcome rule, evidence policy, fixed reward amount and reward count cap. The creator can close a study but cannot rewrite it.

### ReplicationEngine

Owns attempt creation and semantic assessment. It retrieves 2–8 typed HTTPS evidence sources inside the nondeterministic block. The leader produces a bounded structured finding. Validators independently rerun the evidence retrieval and assessment and compare the material fields:

- verdict
- protocol compliance
- evidence sufficiency
- outcome criterion
- required evidence presence

This is deliberately not schema-only validation. For each source, the leader and validators also commit to an exact bounded text window digest (`content_window_sha256`) plus fetch status and size. Validators require the evidence-receipt set and aggregate snapshot digest to match, so a mutable source that changes materially between nodes causes disagreement instead of silently producing a record.

A coherent result must obey the decision law. For example `REPLICATED` is invalid unless protocol compliance is `SATISFIED`, evidence is `SUFFICIENT`, required evidence is present, and the registered outcome criterion is `YES`.

After consensus, storage is updated deterministically. If a ResearchPool is configured, a message is emitted with `on="finalized"`.

### ResearchPool

Owns creator-funded study pools, archive records, reward reservation, safe closed-pool reclaim and pull withdrawals. Only the configured ReplicationEngine may register outcomes. The child message is not created until the parent ReplicationEngine evaluation finalizes. The ResearchPool child transaction is deterministic but still has its own consensus/finality lifecycle, so production evidence must verify that child transaction also reaches `FINALIZED` before calling the archive/reward fully settled.

Only the study creator may fund its pool. After a study is closed, remaining GEN can be reclaimed only when every registered attempt is assessed and has a pool final record, preventing a close/refund race against pending replications.

A valid positive replication (`REPLICATED`) and valid negative replication (`FAILED_TO_REPLICATE`) receive the same fixed frozen reward, subject to remaining pool balance and the reward-count cap. `PROTOCOL_DEVIATION` and `INCONCLUSIVE` reserve no reward.

## Evidence and safety model

- Only HTTPS evidence URLs.
- Credentials in URLs are rejected.
- Loopback and common private IPv4 ranges are rejected.
- Duplicate exact evidence URLs are rejected.
- Evidence kinds are bounded and semantic.
- A study may freeze exact allowed and required HTTPS evidence origins before replication; the engine enforces those origin constraints deterministically before semantic evaluation.
- Fetched content is truncated before prompt construction.
- Evidence is explicitly treated as hostile data; prompt instructions contained inside evidence are not followed.
- Missing or unavailable sources must be capable of producing `INCONCLUSIVE` rather than a forced answer.

## Frontend information architecture

`/lab` is a Replication Atlas, not a dashboard. `/claim/[studyKey]` is a registered protocol paper. `/attempt/[attemptKey]` is a replication notebook. `/archive/[recordKey]` is a public archive research record.

The UI never calculates the semantic verdict. It projects contract state into research language.

## Transaction lifecycle

Writes are presented as:

`AWAITING_SIGNATURE → SUBMITTED → CONSENSUS_RUNNING → PROVISIONAL / UNDETERMINED → READY_TO_FINALIZE → FINALIZED`

A provisional assessment may be displayed, but the UI must state that no archive record or reward exists before parent finality. The archive page is sourced from ResearchPool, never from the assessment alone. For release evidence, the deterministic ResearchPool child transaction must also be verified `FINALIZED` before the record is described as fully settled.
