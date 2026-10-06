# REPROVE V2 milestone

V2 moves a replication attempt from a mutable URL list to an immutable, typed
replication capsule. The capsule freezes the study digest, analysis digest,
artifact identities, provenance profile, and exact SHA-256 for every artifact.

## Frozen contract model

- `StudyRegistry.create_study_v2` freezes a bounded analysis profile, provenance
  policy, artifact-size limit, evidence policy, and attempt TTL.
- Supported deterministic profiles are `ONE_SAMPLE_THRESHOLD`,
  `TWO_GROUP_MEAN_DIFF`, and `BINARY_RATE_DIFF`.
- Supported provenance profiles are `GITHUB_COMMIT`, `ZENODO_RECORD`, and
  `GENERIC_CONTENT_ADDRESS`. Mutable branch/latest references are rejected.
- Artifact retrieval never truncates silently. A source larger than the frozen
  limit fails closed with `INCONCLUSIVE`.
- The model only adjudicates bounded semantic protocol compliance and evidence
  sufficiency. It cannot choose the numeric result or a reward.

## Attempt lifecycle

`NOTEBOOK -> CAPSULE_COMMITTED -> ASSESSED`

An owner may abandon a non-terminal attempt. Anyone may expire an attempt after
the frozen TTL. Both terminal paths decrement the active counter. A closed
study can be reclaimed in O(1): the pool compares engine active/assessed
counters with its finalized child-record counter and never scans historical
attempts.

## Release verification

Run the full local suite before deployment:

```text
py_compile contracts/*.py
pytest -q tests/unit tests/direct
genvm-lint check contracts/study_registry.py
genvm-lint check contracts/replication_engine.py
genvm-lint check contracts/research_pool.py
python scripts/release_check.py
cd web && npm run typecheck && npm run build
```

Deploy only to Studionet chain `61999`, update the three Vercel contract
variables from the fresh manifest, and prove the two-wallet capsule lifecycle
through finalized parent assessment, finalized ResearchPool child, equal valid
outcome rewards, withdrawal, close, and permissionless reclaim.
