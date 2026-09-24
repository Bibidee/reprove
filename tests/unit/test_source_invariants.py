from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = (ROOT / "contracts/replication_engine.py").read_text()
POOL = (ROOT / "contracts/research_pool.py").read_text()
REGISTRY = (ROOT / "contracts/study_registry.py").read_text()
ALL = "\n".join([ENGINE, POOL, REGISTRY])


def test_engine_uses_custom_leader_validator_consensus():
    assert "gl.vm.run_nondet_unsafe(assess, validate)" in ENGINE
    assert 'gl.nondet.web.render(item["url"], mode="text")' in ENGINE


def test_validator_compares_material_fields_and_snapshot():
    for field in [
        '"verdict"',
        '"protocol_compliance"',
        '"evidence_sufficiency"',
        '"outcome_satisfied"',
        '"required_evidence_present"',
        '"evidence_snapshot_digest"',
    ]:
        assert field in ENGINE
    assert 'candidate.get("evidence_receipts") != own.get("evidence_receipts")' in ENGINE


def test_engine_emits_pool_message_only_on_parent_finalized():
    assert 'pool.emit(on="finalized").register_finalized_outcome' in ENGINE


def test_reward_policy_is_outcome_neutral_for_valid_positive_and_negative():
    assert 'eligible = verdict in ["REPLICATED", "FAILED_TO_REPLICATE"]' in POOL


def test_pool_restricts_outcome_registration_to_engine():
    assert 'if self._sender() != self.engine_address:' in POOL
    assert 'raise gl.vm.UserError("only replication engine may register outcomes")' in POOL


def test_pool_updates_claimable_before_external_transfer():
    state_line = 'self.claimable[sender] = u256(available - value)'
    transfer_line = '_Recipient(gl.message.sender_address).emit_transfer(value=u256(value))'
    assert POOL.index(state_line) < POOL.index(transfer_line)


def test_study_has_no_edit_method_after_creation():
    assert "def update_study(" not in REGISTRY
    assert "def edit_study(" not in REGISTRY
    assert "def close_study(" in REGISTRY


def test_contracts_avoid_future_annotation_schema_hazard_and_bare_raises():
    assert "from __future__ import annotations" not in ALL
    assert "raise Exception(" not in ALL


def test_origin_policy_and_ssrf_guards_are_present():
    assert 'allowed_origins' in REGISTRY
    assert 'required_origins' in REGISTRY
    assert 'non-standard evidence ports are forbidden' in ENGINE
    assert 'literal IPv6 evidence hosts are forbidden' in ENGINE
    assert 'private or non-routable evidence hosts are forbidden' in ENGINE


def test_inconclusive_path_is_explicit_and_not_reward_eligible():
    assert '"INCONCLUSIVE"' in ENGINE
    assert 'eligible = verdict in ["REPLICATED", "FAILED_TO_REPLICATE"]' in POOL
