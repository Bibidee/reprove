import json


def test_create_freezes_study(direct_vm, direct_deploy, direct_alice):
    registry = direct_deploy("contracts/study_registry.py")
    direct_vm.sender = direct_alice
    registry.create_study(
        "sleep-01",
        "Sleep duration and recall",
        "Behavioural science",
        "Participants sleeping at least eight hours score at least 10% higher on the registered recall measure.",
        json.dumps({
            "population": "Adults 18-45",
            "procedure": "Randomised sleep schedule",
            "measurement": "Registered recall battery",
            "analysis": "Difference in registered mean score",
            "window": "Seven nights",
        }),
        "REPLICATED when the protocol is satisfied and the registered mean-score improvement is at least 10%.",
        json.dumps({"required_kinds": ["DATASET", "METHOD", "ANALYSIS", "RESULT_TABLE"]}),
        30 * 10**18,
        3,
    )
    study = registry.get_study("sleep-01")
    assert study["status"] == "OPEN"
    assert study["revision"] == 1
    assert study["claim"].startswith("Participants sleeping")


def test_duplicate_study_key_reverts(direct_vm, direct_deploy, direct_alice):
    registry = direct_deploy("contracts/study_registry.py")
    direct_vm.sender = direct_alice
    args = (
        "s-001",
        "A sufficiently long title",
        "Biology",
        "A preregistered claim long enough to pass the minimum validation boundary.",
        json.dumps({"population":"P","procedure":"P","measurement":"M","analysis":"A","window":"W"}),
        "A registered outcome rule long enough to be considered meaningful.",
        json.dumps({"required_kinds":["DATASET","METHOD"]}),
        0,
        0,
    )
    registry.create_study(*args)
    with direct_vm.expect_revert("study_key already exists"):
        registry.create_study(*args)


def test_only_creator_can_close(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry = direct_deploy("contracts/study_registry.py")
    direct_vm.sender = direct_alice
    registry.create_study(
        "s-002", "Another registered study", "Biology",
        "A preregistered claim long enough to pass the minimum validation boundary.",
        json.dumps({"population":"P","procedure":"P","measurement":"M","analysis":"A","window":"W"}),
        "A registered outcome rule long enough to be considered meaningful.",
        json.dumps({"required_kinds":["DATASET","METHOD"]}), 0, 0,
    )
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only study creator may close"):
        registry.close_study("s-002")


def test_required_origin_must_be_in_allowlist(direct_vm, direct_deploy, direct_alice):
    registry = direct_deploy("contracts/study_registry.py")
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("required_origins must be included in allowed_origins when allowlist is used"):
        registry.create_study(
            "s-origin", "Origin policy study", "Software engineering",
            "A preregistered claim long enough to pass the minimum validation boundary.",
            json.dumps({"population":"P","procedure":"P","measurement":"M","analysis":"A","window":"W"}),
            "A registered outcome rule long enough to be considered meaningful.",
            json.dumps({"required_kinds":["DATASET","METHOD"],"allowed_origins":["https://zenodo.org"],"required_origins":["https://osf.io"]}),
            0, 0,
        )


def test_origin_policy_is_frozen_and_normalized(direct_vm, direct_deploy, direct_alice):
    registry = direct_deploy("contracts/study_registry.py")
    direct_vm.sender = direct_alice
    registry.create_study(
        "s-origin-2", "Normalized origin policy", "Software engineering",
        "A preregistered claim long enough to pass the minimum validation boundary.",
        json.dumps({"population":"P","procedure":"P","measurement":"M","analysis":"A","window":"W"}),
        "A registered outcome rule long enough to be considered meaningful.",
        json.dumps({"required_kinds":["DATASET","METHOD"],"allowed_origins":["https://ZENODO.ORG/"],"required_origins":["https://zenodo.org"]}),
        0, 0,
    )
    study = registry.get_study("s-origin-2")
    assert study["evidence_policy"]["allowed_origins"] == ["https://zenodo.org"]
    assert study["evidence_policy"]["required_origins"] == ["https://zenodo.org"]
