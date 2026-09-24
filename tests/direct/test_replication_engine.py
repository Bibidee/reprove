import json


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
