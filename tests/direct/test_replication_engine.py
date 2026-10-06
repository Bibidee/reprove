import json
import sys

from test_adversarial_evidence import _capsule, _mocks, _study


def _set_direct_time(timestamp):
    sys.modules["genlayer.gl"].message_raw["datetime"] = timestamp


def test_manifest_validation_rejects_duplicate_urls(direct_vm, direct_deploy, direct_alice):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    direct_vm.sender = direct_alice
    raw = json.dumps([
        {"kind":"DATASET","url":"https://example.org/evidence","note":"dataset"},
        {"kind":"METHOD","url":"https://example.org/evidence","note":"method"},
    ])
    with direct_vm.expect_revert("duplicate evidence URL"):
        engine.validate_evidence_manifest(raw)


def test_manifest_reports_distinct_origins(direct_vm, direct_deploy, direct_alice):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    direct_vm.sender = direct_alice
    raw = json.dumps([
        {"kind":"DATASET","url":"https://data.example/a","note":"dataset"},
        {"kind":"METHOD","url":"https://method.example/b","note":"method"},
    ])
    result = engine.validate_evidence_manifest(raw)
    assert result["items"] == 2
    assert len(result["distinct_origins"]) == 2


def test_private_host_is_rejected(direct_vm, direct_deploy, direct_alice):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    direct_vm.sender = direct_alice
    raw = json.dumps([
        {"kind":"DATASET","url":"https://127.0.0.1/data","note":"dataset"},
        {"kind":"METHOD","url":"https://method.example/b","note":"method"},
    ])
    with direct_vm.expect_revert("private evidence hosts are forbidden"):
        engine.validate_evidence_manifest(raw)


def test_pool_can_only_be_configured_once(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    engine.set_pool_once("0x" + "22" * 20)
    with direct_vm.expect_revert("pool already configured"):
        engine.set_pool_once("0x" + "33" * 20)


def test_non_owner_cannot_configure_pool(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only owner may set pool"):
        engine.set_pool_once("0x" + "22" * 20)


def test_non_standard_https_port_is_rejected(direct_vm, direct_deploy, direct_alice):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    direct_vm.sender = direct_alice
    raw = json.dumps([
        {"kind":"DATASET","url":"https://data.example:8443/a","note":"dataset"},
        {"kind":"METHOD","url":"https://method.example/b","note":"method"},
    ])
    with direct_vm.expect_revert("non-standard evidence ports are forbidden"):
        engine.validate_evidence_manifest(raw)


def test_ipv6_literal_is_rejected(direct_vm, direct_deploy, direct_alice):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    direct_vm.sender = direct_alice
    raw = json.dumps([
        {"kind":"DATASET","url":"https://[::1]/a","note":"dataset"},
        {"kind":"METHOD","url":"https://method.example/b","note":"method"},
    ])
    with direct_vm.expect_revert("literal IPv6 evidence hosts are forbidden"):
        engine.validate_evidence_manifest(raw)


def test_link_local_ipv4_is_rejected(direct_vm, direct_deploy, direct_alice):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    direct_vm.sender = direct_alice
    raw = json.dumps([
        {"kind":"DATASET","url":"https://169.254.169.254/latest/meta-data","note":"dataset"},
        {"kind":"METHOD","url":"https://method.example/b","note":"method"},
    ])
    with direct_vm.expect_revert("private or non-routable evidence hosts are forbidden"):
        engine.validate_evidence_manifest(raw)


def test_active_counter_decrements_once_on_abandon(direct_vm, direct_deploy, direct_bob):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    engine._study = lambda _study_key: {
        "status": "OPEN", "attempt_ttl_seconds": 604800,
    }
    direct_vm.sender = direct_bob
    engine.begin_attempt("study", "abandon-once", "A replication statement long enough for validation.")
    assert engine.get_study_settlement_state("study")["active_attempts"] == 1
    engine.abandon_attempt("abandon-once")
    assert engine.get_study_settlement_state("study")["active_attempts"] == 0
    with direct_vm.expect_revert("attempt is terminal"):
        engine.abandon_attempt("abandon-once")


def test_notebook_expiry_decrements_active_counter_once(direct_vm, direct_deploy, direct_bob):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    engine._study = lambda _study_key: {
        "status": "OPEN", "attempt_ttl_seconds": 60,
    }
    direct_vm.warp("2026-01-01T00:00:00Z")
    _set_direct_time("2026-01-01T00:00:00Z")
    direct_vm.sender = direct_bob
    engine.begin_attempt("study", "expired-notebook", "A replication statement long enough for validation.")
    assert engine.get_study_settlement_state("study") == {"active_attempts": 1, "assessed_attempts": 0}
    direct_vm.warp("2026-01-01T00:01:00Z")
    _set_direct_time("2026-01-01T00:01:00Z")
    engine.expire_attempt("expired-notebook")
    assert engine.get_attempt("expired-notebook")["state"] == "EXPIRED"
    assert engine.get_study_settlement_state("study") == {"active_attempts": 0, "assessed_attempts": 0}
    with direct_vm.expect_revert("attempt is terminal"):
        engine.expire_attempt("expired-notebook")


def test_committed_capsule_expiry_decrements_active_counter_once(
    direct_vm, direct_deploy, direct_bob
):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    study = _study()
    study["attempt_ttl_seconds"] = 60
    engine._study = lambda _study_key: study
    direct_vm.warp("2026-01-01T00:00:00Z")
    _set_direct_time("2026-01-01T00:00:00Z")
    direct_vm.sender = direct_bob
    engine.begin_attempt("v2-study", "expired-capsule", "A replication statement long enough for validation.")
    engine.commit_capsule("expired-capsule", _capsule(study, "expired-capsule"))
    assert engine.get_attempt("expired-capsule")["state"] == "CAPSULE_COMMITTED"
    direct_vm.warp("2026-01-01T00:01:00Z")
    _set_direct_time("2026-01-01T00:01:00Z")
    engine.expire_attempt("expired-capsule")
    assert engine.get_attempt("expired-capsule")["state"] == "EXPIRED"
    assert engine.get_study_settlement_state("v2-study") == {"active_attempts": 0, "assessed_attempts": 0}


def test_assessment_moves_counter_and_cannot_finalize_twice(
    direct_vm, direct_deploy, direct_bob
):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    study = _study()
    engine._study = lambda _study_key: study
    direct_vm.sender = direct_bob
    engine.begin_attempt("v2-study", "assessed-once", "A replication statement long enough for validation.")
    engine.commit_capsule("assessed-once", _capsule(study, "assessed-once"))
    assert engine.get_study_settlement_state("v2-study") == {"active_attempts": 1, "assessed_attempts": 0}
    _mocks(direct_vm)
    assessment = engine.evaluate_attempt("assessed-once")
    assert assessment["verdict"] == "REPLICATED"
    assert engine.get_study_settlement_state("v2-study") == {"active_attempts": 0, "assessed_attempts": 1}
    with direct_vm.expect_revert("capsule must be committed before evaluation"):
        engine.evaluate_attempt("assessed-once")
    assert engine.get_study_settlement_state("v2-study") == {"active_attempts": 0, "assessed_attempts": 1}


def test_settlement_counter_underflow_is_rejected(direct_vm, direct_deploy, direct_alice):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("settlement counter underflow"):
        engine._set_counter("study", "active", -1)
