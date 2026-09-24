import json


POSITIVE = json.dumps({
    "verdict": "REPLICATED",
    "protocol_compliance": "SATISFIED",
    "evidence_sufficiency": "SUFFICIENT",
    "outcome_satisfied": "YES",
    "required_evidence_present": "YES",
    "summary": "positive",
})

NEGATIVE = json.dumps({
    "verdict": "FAILED_TO_REPLICATE",
    "protocol_compliance": "SATISFIED",
    "evidence_sufficiency": "SUFFICIENT",
    "outcome_satisfied": "NO",
    "required_evidence_present": "YES",
    "summary": "negative",
})


def _address(value):
    return "0x" + bytes(value).hex()


def _setup_engine(direct_deploy, direct_bob):
    engine = direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")
    study = {
        "claim": "A preregistered claim long enough to pass the minimum validation boundary.",
        "protocol": {"population": "P", "procedure": "P", "measurement": "M", "analysis": "A", "window": "W"},
        "outcome_rule": "A registered outcome rule long enough to be considered meaningful.",
        "evidence_policy": {"required_kinds": ["DATASET", "METHOD"], "min_distinct_origins": 2},
    }
    engine._study = lambda _study_key: study
    engine.attempts["seeded-attempt"] = json.dumps({
        "attempt_key": "seeded-attempt",
        "study_key": "adversarial-study",
        "researcher": _address(direct_bob),
        "replication_statement": "A replication statement long enough for validation.",
        "state": "NOTEBOOK",
        "created_at": "2026-01-01T00:00:00Z",
        "evaluated_at": "",
        "evidence_manifest": [],
        "reported_result": {},
        "assessment": {},
        "assessment_digest": "",
    }, sort_keys=True, separators=(",", ":"))
    return engine


def _begin(direct_vm, engine, direct_bob, attempt_key):
    direct_vm.sender = direct_bob
    if attempt_key != "seeded-attempt":
        engine.attempts[attempt_key] = engine.attempts["seeded-attempt"].replace("seeded-attempt", attempt_key)


def _web_mocks(direct_vm, first_body="dataset", second_body="method"):
    direct_vm.mock_web(r"https://data\.example/.*", {"status": 200, "body": first_body})
    direct_vm.mock_web(r"https://method\.example/.*", {"status": 200, "body": second_body})


def _manifest(*, duplicate_kind=False):
    return json.dumps([
        {"kind": "DATASET", "url": "https://data.example/source", "note": "dataset"},
        {"kind": "DATASET" if duplicate_kind else "METHOD", "url": "https://method.example/source", "note": "method"},
    ])


def test_missing_required_kind_is_inconclusive_even_if_model_claims_positive(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    engine = _setup_engine(direct_deploy, direct_bob)
    _begin(direct_vm, engine, direct_bob, "missing-required")
    _web_mocks(direct_vm)
    direct_vm.mock_llm("You are independently evaluating", POSITIVE)

    direct_vm.sender = direct_bob
    assessment = engine.evaluate_attempt("missing-required", _manifest(duplicate_kind=True), "{}")

    assert assessment["verdict"] == "INCONCLUSIVE"
    assert assessment["evidence_sufficiency"] == "INSUFFICIENT"
    assert assessment["required_evidence_present"] == "NO"


def test_unavailable_source_is_inconclusive_even_if_model_claims_positive(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    engine = _setup_engine(direct_deploy, direct_bob)
    _begin(direct_vm, engine, direct_bob, "unavailable-source")
    direct_vm.mock_web(r"https://data\.example/.*", {"status": 200, "body": "dataset"})
    direct_vm.mock_llm("You are independently evaluating", POSITIVE)

    direct_vm.sender = direct_bob
    assessment = engine.evaluate_attempt("unavailable-source", _manifest(), "{}")

    assert assessment["verdict"] == "INCONCLUSIVE"
    assert assessment["evidence_sufficiency"] == "UNAVAILABLE"
    assert any(r["fetch_status"] == "UNAVAILABLE" for r in assessment["evidence_receipts"])


def test_conflicting_evidence_can_only_settle_as_inconclusive(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    engine = _setup_engine(direct_deploy, direct_bob)
    _begin(direct_vm, engine, direct_bob, "conflicting-source")
    _web_mocks(direct_vm, "version A says yes", "version B says no")
    inconclusive = json.dumps({
        "verdict": "INCONCLUSIVE",
        "protocol_compliance": "UNCERTAIN",
        "evidence_sufficiency": "CONFLICTED",
        "outcome_satisfied": "UNKNOWN",
        "required_evidence_present": "YES",
        "summary": "sources conflict",
    })
    direct_vm.mock_llm("You are independently evaluating", inconclusive)

    direct_vm.sender = direct_bob
    assessment = engine.evaluate_attempt("conflicting-source", _manifest(), "{}")

    assert assessment["verdict"] == "INCONCLUSIVE"
    assert assessment["evidence_sufficiency"] == "CONFLICTED"


def test_validator_rejects_materially_changed_assessment(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    engine = _setup_engine(direct_deploy, direct_bob)
    _begin(direct_vm, engine, direct_bob, "changed-assessment")
    _web_mocks(direct_vm)
    direct_vm.mock_llm("You are independently evaluating", POSITIVE)

    direct_vm.sender = direct_bob
    engine.evaluate_attempt("changed-assessment", _manifest(), "{}")

    direct_vm.clear_mocks()
    _web_mocks(direct_vm)
    direct_vm.mock_llm("You are independently evaluating", NEGATIVE)

    assert direct_vm.run_validator() is False
