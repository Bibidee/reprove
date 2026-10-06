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
    assert pool._finalized_count("s") == 1
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
    assert pool._finalized_count("s") == 4
    assert pool.get_claimable(researcher) == 10
    assert pool.get_final_record("s:negative")["reward_reserved_wei"] == 0
    assert pool.get_final_record("s:deviation")["reward_reserved_wei"] == 0
    assert pool.get_final_record("s:unknown")["reward_reserved_wei"] == 0


def test_positive_and_negative_valid_replications_receive_equal_rewards(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    pool = _setup_pool(direct_deploy, direct_alice, reward=10, maximum=2)
    researcher = _address(direct_bob)
    _as_engine(direct_vm)
    pool.study_balances["s"] = 20
    pool.register_finalized_outcome("s", "positive", researcher, "REPLICATED", "a" * 64)
    pool.register_finalized_outcome("s", "negative", researcher, "FAILED_TO_REPLICATE", "b" * 64)
    assert pool.get_claimable(researcher) == 20
    assert pool.get_study_pool("s") == {"available_wei": 0, "rewarded_attempts": 2}


def test_zero_withdrawal_and_counter_underflow_are_rejected(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    pool = _setup_pool(direct_deploy, direct_alice)
    with direct_vm.expect_revert("finalized record counter underflow"):
        pool._set_finalized_count("s", -1)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("withdraw amount must be positive"):
        pool.withdraw(0)


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


class _SettlementEngineView:
    def __init__(self, state):
        self.state = state

    def view(self):
        return self

    def get_study_settlement_state(self, _study_key):
        return self.state


def _closed_pool(direct_deploy, direct_alice, state):
    pool = _setup_pool(direct_deploy, direct_alice)
    pool._study = lambda _study_key: {
        "creator": _address(direct_alice),
        "status": "CLOSED",
        "reward_per_attempt_wei": 10,
        "max_rewarded_attempts": 2,
    }
    return pool, state


def _pool_gl(pool):
    import sys
    module_name = pool._instance.__class__.__module__
    return sys.modules[module_name].gl


def test_reclaim_readiness_blocks_active_attempts_and_unarchived_assessments(
    direct_vm, direct_deploy, direct_alice
):
    from unittest.mock import patch

    pool, state = _closed_pool(
        direct_deploy, direct_alice, {"active_attempts": 1, "assessed_attempts": 0}
    )
    gl = _pool_gl(pool)
    pool.study_balances["s"] = 10
    direct_vm.sender = direct_alice
    with patch.object(gl, "get_contract_at", lambda _address: _SettlementEngineView(state)):
        readiness = pool.get_reclaim_readiness("s")
        assert readiness["eligible"] is False
        assert "ACTIVE_ATTEMPTS_REMAIN" in readiness["reasons"]
        with direct_vm.expect_revert("active replication attempts remain"):
            pool.reclaim_closed_pool("s")

    state = {"active_attempts": 0, "assessed_attempts": 1}
    with patch.object(gl, "get_contract_at", lambda _address: _SettlementEngineView(state)):
        readiness = pool.get_reclaim_readiness("s")
        assert readiness["eligible"] is False
        assert "PENDING_FINALIZED_ARCHIVE" in readiness["reasons"]
        with direct_vm.expect_revert("assessed attempt is not finalized into the pool"):
            pool.reclaim_closed_pool("s")


def test_closed_settled_pool_reclaims_remainder_and_preserves_reward_claim(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    from unittest.mock import patch

    pool, state = _closed_pool(
        direct_deploy, direct_alice, {"active_attempts": 0, "assessed_attempts": 1}
    )
    gl = _pool_gl(pool)
    researcher = _address(direct_bob)
    pool.study_balances["s"] = 20
    _as_engine(direct_vm)
    pool.register_finalized_outcome("s", "settled", researcher, "REPLICATED", "a" * 64)
    assert pool.get_study_pool("s") == {"available_wei": 10, "rewarded_attempts": 1}
    assert pool.get_claimable(researcher) == 10

    direct_vm.sender = direct_alice
    with patch.object(gl, "get_contract_at", lambda _address: _SettlementEngineView(state)):
        readiness = pool.get_reclaim_readiness("s")
        assert readiness["eligible"] is True
        pool.reclaim_closed_pool("s")

    assert pool.get_study_pool("s") == {"available_wei": 0, "rewarded_attempts": 1}
    direct_vm.sender = direct_bob
    pool.withdraw(10)
    assert pool.get_claimable(researcher) == 0
