import json
from urllib.parse import urlparse

VERDICTS = {"REPLICATED", "FAILED_TO_REPLICATE", "PROTOCOL_DEVIATION", "INCONCLUSIVE"}
ALLOWED_KINDS = {
    "DATASET",
    "METHOD",
    "ANALYSIS",
    "RESULT_TABLE",
    "PREREGISTRATION_REFERENCE",
    "INDEPENDENT_OBSERVATION",
    "SUPPLEMENT",
}


def coherent(result):
    if result["verdict"] not in VERDICTS:
        return False
    if result["protocol_compliance"] not in {"SATISFIED", "DEVIATED", "UNCERTAIN"}:
        return False
    if result["evidence_sufficiency"] not in {"SUFFICIENT", "INSUFFICIENT", "UNAVAILABLE", "CONFLICTED"}:
        return False
    if result["outcome_satisfied"] not in {"YES", "NO", "UNKNOWN"}:
        return False
    if result["required_evidence_present"] not in {"YES", "NO", "UNKNOWN"}:
        return False
    if result["verdict"] == "REPLICATED":
        return (
            result["protocol_compliance"] == "SATISFIED"
            and result["evidence_sufficiency"] == "SUFFICIENT"
            and result["outcome_satisfied"] == "YES"
            and result["required_evidence_present"] == "YES"
        )
    if result["verdict"] == "FAILED_TO_REPLICATE":
        return (
            result["protocol_compliance"] == "SATISFIED"
            and result["evidence_sufficiency"] == "SUFFICIENT"
            and result["outcome_satisfied"] == "NO"
            and result["required_evidence_present"] == "YES"
        )
    if result["verdict"] == "PROTOCOL_DEVIATION":
        return result["protocol_compliance"] == "DEVIATED"
    return True


def reward_for(verdict, reward, count, maximum, balance):
    if verdict not in {"REPLICATED", "FAILED_TO_REPLICATE"}:
        return 0
    if reward <= 0 or count >= maximum or balance < reward:
        return 0
    return reward


def validate_manifest(items):
    if not 2 <= len(items) <= 8:
        return False
    urls = set()
    for item in items:
        if item.get("kind") not in ALLOWED_KINDS:
            return False
        url = item.get("url", "")
        if url in urls:
            return False
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            return False
        if parsed.username or parsed.password:
            return False
        urls.add(url)
    return True


BASE = {
    "protocol_compliance": "SATISFIED",
    "evidence_sufficiency": "SUFFICIENT",
    "outcome_satisfied": "YES",
    "required_evidence_present": "YES",
}


def test_replicated_requires_full_support():
    r = dict(BASE, verdict="REPLICATED")
    assert coherent(r)


def test_replicated_cannot_have_unknown_outcome():
    r = dict(BASE, verdict="REPLICATED", outcome_satisfied="UNKNOWN")
    assert not coherent(r)


def test_failed_to_replicate_is_valid_negative_result():
    r = dict(BASE, verdict="FAILED_TO_REPLICATE", outcome_satisfied="NO")
    assert coherent(r)


def test_failed_to_replicate_cannot_be_used_for_protocol_failure():
    r = dict(BASE, verdict="FAILED_TO_REPLICATE", outcome_satisfied="NO", protocol_compliance="DEVIATED")
    assert not coherent(r)


def test_protocol_deviation_is_distinct_terminal_result():
    r = dict(BASE, verdict="PROTOCOL_DEVIATION", protocol_compliance="DEVIATED", outcome_satisfied="UNKNOWN")
    assert coherent(r)


def test_inconclusive_is_first_class():
    r = dict(
        verdict="INCONCLUSIVE",
        protocol_compliance="UNCERTAIN",
        evidence_sufficiency="UNAVAILABLE",
        outcome_satisfied="UNKNOWN",
        required_evidence_present="UNKNOWN",
    )
    assert coherent(r)


def test_positive_and_negative_replications_receive_equal_fixed_reward():
    assert reward_for("REPLICATED", 30, 0, 3, 100) == 30
    assert reward_for("FAILED_TO_REPLICATE", 30, 0, 3, 100) == 30


def test_protocol_deviation_never_receives_reward():
    assert reward_for("PROTOCOL_DEVIATION", 30, 0, 3, 100) == 0


def test_inconclusive_never_receives_reward():
    assert reward_for("INCONCLUSIVE", 30, 0, 3, 100) == 0


def test_reward_cap_prevents_overpayment():
    assert reward_for("REPLICATED", 30, 3, 3, 100) == 0


def test_insufficient_pool_prevents_overpayment():
    assert reward_for("REPLICATED", 30, 0, 3, 29) == 0


def test_manifest_accepts_multiple_semantic_evidence_types():
    items = [
        {"kind": "DATASET", "url": "https://example.org/data.csv"},
        {"kind": "METHOD", "url": "https://methods.example/method"},
    ]
    assert validate_manifest(items)


def test_manifest_rejects_duplicate_url():
    items = [
        {"kind": "DATASET", "url": "https://example.org/data"},
        {"kind": "METHOD", "url": "https://example.org/data"},
    ]
    assert not validate_manifest(items)


def test_manifest_rejects_non_https():
    items = [
        {"kind": "DATASET", "url": "http://example.org/data"},
        {"kind": "METHOD", "url": "https://example.org/method"},
    ]
    assert not validate_manifest(items)


def test_manifest_rejects_unknown_kind():
    items = [
        {"kind": "RANDOM_FILE", "url": "https://example.org/data"},
        {"kind": "METHOD", "url": "https://example.org/method"},
    ]
    assert not validate_manifest(items)


def test_manifest_size_is_bounded():
    two = [{"kind": "DATASET", "url": "https://a.example/x"}, {"kind": "METHOD", "url": "https://b.example/x"}]
    assert validate_manifest(two)
    assert not validate_manifest(two * 5)


def test_canonical_json_is_stable_for_same_record():
    a = {"b": 2, "a": 1}
    b = {"a": 1, "b": 2}
    assert json.dumps(a, sort_keys=True, separators=(",", ":")) == json.dumps(b, sort_keys=True, separators=(",", ":"))


def can_reclaim(status, attempts, final_record_keys):
    if status != "CLOSED":
        return False
    for a in attempts:
        if a["state"] != "ASSESSED":
            return False
        if f'{a["study_key"]}:{a["attempt_key"]}' not in final_record_keys:
            return False
    return True


def test_open_study_pool_cannot_be_reclaimed():
    assert not can_reclaim("OPEN", [], set())


def test_closed_pool_with_open_notebook_cannot_be_reclaimed():
    attempts = [{"study_key":"s","attempt_key":"a","state":"NOTEBOOK"}]
    assert not can_reclaim("CLOSED", attempts, set())


def test_assessed_but_not_finalized_attempt_blocks_reclaim():
    attempts = [{"study_key":"s","attempt_key":"a","state":"ASSESSED"}]
    assert not can_reclaim("CLOSED", attempts, set())


def test_closed_and_fully_settled_pool_can_be_reclaimed():
    attempts = [{"study_key":"s","attempt_key":"a","state":"ASSESSED"}]
    assert can_reclaim("CLOSED", attempts, {"s:a"})


def test_two_studies_do_not_share_reward_balance_in_model():
    pools = {"a": 50, "b": 70}
    pools["a"] -= reward_for("REPLICATED", 20, 0, 2, pools["a"])
    assert pools == {"a": 30, "b": 70}


def test_assessment_snapshot_digest_changes_when_evidence_window_changes():
    import hashlib
    def digest(window):
        receipt = [{"kind":"DATASET","url":"https://data.example/x","origin":"https://data.example","fetch_status":"OK","content_window_sha256":hashlib.sha256(window.encode()).hexdigest(),"content_window_chars":len(window)}]
        return hashlib.sha256(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest("version one") != digest("version two")


def test_assessment_snapshot_digest_is_stable_for_same_receipts():
    import hashlib
    receipt = [{"kind":"METHOD","url":"https://method.example/x","origin":"https://method.example","fetch_status":"OK","content_window_sha256":"a"*64,"content_window_chars":42}]
    a = hashlib.sha256(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    b = hashlib.sha256(json.dumps(list(receipt), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert a == b


def evidence_policy_ok(required_kinds, present_kinds, origins, minimum, allowed=None, required_origins=None):
    allowed = allowed or []
    required_origins = required_origins or []
    return (
        all(kind in present_kinds for kind in required_kinds)
        and len(set(origins)) >= minimum
        and (not allowed or all(origin in allowed for origin in set(origins)))
        and all(origin in set(origins) for origin in required_origins)
    )


def test_frozen_origin_allowlist_rejects_unregistered_source_origin():
    assert not evidence_policy_ok(
        ["DATASET", "METHOD"], ["DATASET", "METHOD"],
        ["https://zenodo.org", "https://unregistered.example"], 2,
        allowed=["https://zenodo.org", "https://osf.io"],
    )


def test_frozen_required_origin_must_appear():
    assert not evidence_policy_ok(
        ["DATASET", "METHOD"], ["DATASET", "METHOD"],
        ["https://zenodo.org", "https://github.com"], 2,
        required_origins=["https://osf.io"],
    )


def test_frozen_origin_policy_accepts_registered_diversity():
    assert evidence_policy_ok(
        ["DATASET", "METHOD"], ["DATASET", "METHOD", "ANALYSIS"],
        ["https://zenodo.org", "https://osf.io"], 2,
        allowed=["https://zenodo.org", "https://osf.io"],
        required_origins=["https://zenodo.org"],
    )
