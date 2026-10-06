import json


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


def test_binary_rate_difference_uses_integer_counts(direct_deploy):
    engine = _engine(direct_deploy)
    spec = {"profile":"BINARY_RATE_DIFF","scale":1,"group_field":"group","group_a":"A","group_b":"B","success_field":"success","threshold_scaled":0,"comparator":">="}
    result = engine._compute(json.dumps([{"group":"A","success":"0"},{"group":"A","success":"0"},{"group":"B","success":"1"},{"group":"B","success":"1"}]), spec, {"difference_num":4,"difference_den":4,"threshold_met":True})
    assert result["success_a"] == 0
    assert result["success_b"] == 2
    assert result["difference_num"] == 4
    assert result["threshold_met"] is True


def test_malformed_dataset_fails_closed(direct_vm, direct_deploy):
    engine = _engine(direct_deploy)
    spec = {"profile":"ONE_SAMPLE_THRESHOLD","value_field":"value","scale":1000,"threshold_scaled":0,"comparator":">="}
    with direct_vm.expect_revert("malformed number"):
        engine._compute('[{"value":"not-a-number"}]', spec, {})
