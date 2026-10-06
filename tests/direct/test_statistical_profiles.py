import json
import pytest


def _engine(direct_deploy):
    return direct_deploy("contracts/replication_engine.py", "0x" + "11" * 20, "")


def test_two_group_mean_difference_is_exact_and_bounded(direct_deploy):
    engine = _engine(direct_deploy)
    spec = {"profile":"TWO_GROUP_MEAN_DIFF","value_field":"value","scale":1000,"group_field":"group","group_a":"A","group_b":"B","threshold_scaled":500,"comparator":">="}
    result = engine._compute(json.dumps([{"group":"A","value":"1.0"},{"group":"A","value":"1.0"},{"group":"B","value":"2.0"},{"group":"B","value":"2.0"}]), spec, {"difference_num":1000,"difference_den":1,"threshold_met":True})
    assert result["difference_num"] == 4000
    assert result["difference_den"] == 4
    assert result["threshold_met"] is True
    assert result["reported_result_match"] is False


@pytest.mark.parametrize(
    ("comparator", "value", "expected"),
    [
        (">=", "0.10", False),
        (">=", "0.50", True),
        (">=", "0.90", True),
        (">", "0.50", False),
        (">", "0.90", True),
        ("<=", "0.10", True),
        ("<", "0.10", True),
        ("<", "0.50", False),
    ],
)
def test_one_sample_threshold_uses_same_fixed_point_units(direct_deploy, comparator, value, expected):
    engine = _engine(direct_deploy)
    spec = {"profile":"ONE_SAMPLE_THRESHOLD","value_field":"value","scale":1000,"threshold_scaled":500,"comparator":comparator}
    result = engine._compute(json.dumps([{"value": value}]), spec, {})
    assert result["mean_num"] in [100, 500, 900]
    assert result["threshold_met"] is expected


def test_one_sample_explicit_double_scaling_regression(direct_deploy):
    engine = _engine(direct_deploy)
    spec = {"profile":"ONE_SAMPLE_THRESHOLD","value_field":"value","scale":1000,"threshold_scaled":500,"comparator":">="}
    result = engine._compute('[{"value":"0.10"}]', spec, {})
    assert result["mean_num"] == 100
    assert result["threshold_met"] is False


def test_one_sample_negative_value_and_threshold(direct_deploy):
    engine = _engine(direct_deploy)
    spec = {"profile":"ONE_SAMPLE_THRESHOLD","value_field":"value","scale":1000,"threshold_scaled":-500,"comparator":">="}
    result = engine._compute('[{"value":"-0.60"}]', spec, {})
    assert result["mean_num"] == -600
    assert result["threshold_met"] is False


@pytest.mark.parametrize(
    ("comparator", "expected"),
    [(">=", True), (">", False), ("<=", True), ("<", False)],
)
def test_two_group_threshold_boundaries(direct_deploy, comparator, expected):
    engine = _engine(direct_deploy)
    spec = {"profile":"TWO_GROUP_MEAN_DIFF","value_field":"value","scale":1000,"group_field":"group","group_a":"A","group_b":"B","threshold_scaled":1000,"comparator":comparator}
    result = engine._compute(json.dumps([{"group":"A","value":"1.0"},{"group":"B","value":"2.0"}]), spec, {})
    assert result["difference_num"] == 1000
    assert result["difference_den"] == 1
    assert result["threshold_met"] is expected


def test_two_group_negative_difference_is_compared_without_rescaling(direct_deploy):
    engine = _engine(direct_deploy)
    spec = {"profile":"TWO_GROUP_MEAN_DIFF","value_field":"value","scale":1000,"group_field":"group","group_a":"A","group_b":"B","threshold_scaled":-500,"comparator":"<="}
    result = engine._compute(json.dumps([{"group":"A","value":"1.0"},{"group":"B","value":"0.5"}]), spec, {})
    assert result["difference_num"] == -500
    assert result["difference_den"] == 1
    assert result["threshold_met"] is True


def test_binary_rate_difference_uses_integer_counts(direct_deploy):
    engine = _engine(direct_deploy)
    spec = {"profile":"BINARY_RATE_DIFF","scale":1,"group_field":"group","group_a":"A","group_b":"B","success_field":"success","threshold_scaled":0,"comparator":">="}
    result = engine._compute(json.dumps([{"group":"A","success":"0"},{"group":"A","success":"0"},{"group":"B","success":"1"},{"group":"B","success":"1"}]), spec, {"difference_num":4,"difference_den":4,"threshold_met":True})
    assert result["success_a"] == 0
    assert result["success_b"] == 2
    assert result["difference_num"] == 4
    assert result["threshold_met"] is True


def test_binary_rate_difference_supports_fixed_point_thresholds(direct_deploy):
    engine = _engine(direct_deploy)
    spec = {"profile":"BINARY_RATE_DIFF","scale":1000,"group_field":"group","group_a":"A","group_b":"B","success_field":"success","threshold_scaled":500,"comparator":">="}
    result = engine._compute(json.dumps([{"group":"A","success":"0"},{"group":"B","success":"1"}]), spec, {})
    assert result["difference_num"] == 1000
    assert result["difference_den"] == 1
    assert result["threshold_met"] is True


@pytest.mark.parametrize(
    ("a", "b", "comparator", "expected"),
    [("0", "0", ">=", True), ("0", "1", ">", True), ("1", "0", "<", True), ("1", "0", "<=", True)],
)
def test_binary_rate_difference_positive_zero_negative_boundaries(direct_deploy, a, b, comparator, expected):
    engine = _engine(direct_deploy)
    spec = {"profile":"BINARY_RATE_DIFF","scale":1,"group_field":"group","group_a":"A","group_b":"B","success_field":"success","threshold_scaled":0,"comparator":comparator}
    result = engine._compute(json.dumps([{"group":"A","success":a},{"group":"B","success":b}]), spec, {})
    assert result["threshold_met"] is expected


def test_malformed_dataset_fails_closed(direct_vm, direct_deploy):
    engine = _engine(direct_deploy)
    spec = {"profile":"ONE_SAMPLE_THRESHOLD","value_field":"value","scale":1000,"threshold_scaled":0,"comparator":">="}
    with direct_vm.expect_revert("malformed number"):
        engine._compute('[{"value":"not-a-number"}]', spec, {})
