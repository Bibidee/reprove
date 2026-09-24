ENGINE = bytes.fromhex("22" * 20)


def _address(value):
    return "0x" + bytes(value).hex()


def _setup_pool(direct_deploy, direct_alice, reward=10, maximum=1):
    pool = direct_deploy(
        "contracts/research_pool.py",
        "0x" + "11" * 20,
        "0x" + ENGINE.hex(),
    )
    study = {
        "creator": _address(direct_alice),
        "status": "OPEN",
        "reward_per_attempt_wei": reward,
        "max_rewarded_attempts": maximum,
    }
    pool._study = lambda _study_key: study
    return pool


def _as_engine(direct_vm):
    direct_vm.sender = ENGINE


def test_only_engine_can_register_and_duplicate_records_are_rejected(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    pool = _setup_pool(direct_deploy, direct_alice)
    researcher = _address(direct_bob)

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only replication engine may register outcomes"):
        pool.register_finalized_outcome("s", "a", researcher, "REPLICATED", "a" * 64)

    _as_engine(direct_vm)
    pool.register_finalized_outcome("s", "a", researcher, "REPLICATED", "a" * 64)
    with direct_vm.expect_revert("final record already registered"):
        pool.register_finalized_outcome("s", "a", researcher, "REPLICATED", "a" * 64)


def test_reward_cap_and_ineligible_verdicts_never_overpay(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    pool = _setup_pool(direct_deploy, direct_alice, reward=10, maximum=1)
    researcher = _address(direct_bob)
    _as_engine(direct_vm)

    pool.study_balances["s"] = 25
    pool.register_finalized_outcome("s", "positive", researcher, "REPLICATED", "a" * 64)
    pool.register_finalized_outcome("s", "negative", researcher, "FAILED_TO_REPLICATE", "b" * 64)
    pool.register_finalized_outcome("s", "deviation", researcher, "PROTOCOL_DEVIATION", "c" * 64)
    pool.register_finalized_outcome("s", "unknown", researcher, "INCONCLUSIVE", "d" * 64)

    assert pool.get_study_pool("s") == {"available_wei": 15, "rewarded_attempts": 1}
    assert pool.get_claimable(researcher) == 10
    assert pool.get_final_record("s:negative")["reward_reserved_wei"] == 0
    assert pool.get_final_record("s:deviation")["reward_reserved_wei"] == 0
    assert pool.get_final_record("s:unknown")["reward_reserved_wei"] == 0


def test_insufficient_pool_does_not_reserve_a_reward(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    pool = _setup_pool(direct_deploy, direct_alice, reward=20, maximum=2)
    researcher = _address(direct_bob)
    _as_engine(direct_vm)
    pool.study_balances["s"] = 19

    pool.register_finalized_outcome("s", "underfunded", researcher, "REPLICATED", "a" * 64)

    assert pool.get_study_pool("s") == {"available_wei": 19, "rewarded_attempts": 0}
    assert pool.get_claimable(researcher) == 0
    assert pool.get_final_record("s:underfunded")["reward_reserved_wei"] == 0


def test_withdrawal_cannot_be_replayed_or_exceed_claimable(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    pool = _setup_pool(direct_deploy, direct_alice, reward=10, maximum=1)
    researcher = _address(direct_bob)
    _as_engine(direct_vm)
    pool.study_balances["s"] = 10
    pool.register_finalized_outcome("s", "a", researcher, "REPLICATED", "a" * 64)

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("withdraw amount exceeds claimable balance"):
        pool.withdraw(11)
    pool.withdraw(10)
    assert pool.get_claimable(researcher) == 0
    with direct_vm.expect_revert("withdraw amount exceeds claimable balance"):
        pool.withdraw(1)


def test_reclaim_requires_closed_study_and_creator(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    pool = _setup_pool(direct_deploy, direct_alice)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only study creator may reclaim"):
        pool.reclaim_closed_pool("s")

    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("study must be closed before reclaim"):
        pool.reclaim_closed_pool("s")
