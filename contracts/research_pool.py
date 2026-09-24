# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from genlayer import *


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


class ResearchPool(gl.Contract):
    """Finality-gated replication reward and public record consumer.

    ReplicationEngine emits register_finalized_outcome only on='finalized'.
    Therefore this contract does not reserve a reward or publish an archive
    record for merely accepted/provisional evaluations.
    """

    registry_address: str
    engine_address: str
    study_balances: TreeMap[str, u256]
    rewarded_count: TreeMap[str, u256]
    claimable: TreeMap[str, u256]
    final_records: str
    record_keys_json: str
    record_count: u256

    def __init__(self, registry_address: str, engine_address: str):
        registry_text = registry_address.as_hex if hasattr(registry_address, "as_hex") else str(registry_address)
        engine_text = engine_address.as_hex if hasattr(engine_address, "as_hex") else str(engine_address)
        if not registry_text.startswith("0x") or len(registry_text) != 42:
            raise gl.vm.UserError("invalid registry address")
        if not engine_text.startswith("0x") or len(engine_text) != 42:
            raise gl.vm.UserError("invalid engine address")
        self.registry_address = registry_text.lower()
        self.engine_address = engine_text.lower()
        # GenVM derives the concrete storage descriptor from the annotated
        # fields.  Constructing parameterized TreeMaps here creates a second
        # descriptor instance and fails deployment-time descriptor identity
        # checks, so use the SDK's canonical unparameterized constructor.
        self.study_balances = TreeMap()
        self.rewarded_count = TreeMap()
        self.claimable = TreeMap()
        self.final_records = "{}"
        self.record_keys_json = "[]"
        self.record_count = u256(0)

    def _sender(self) -> str:
        return gl.message.sender_address.as_hex.lower()

    def _now(self) -> str:
        return str(gl.message_raw["datetime"])

    def _study(self, study_key: str) -> dict:
        registry = gl.get_contract_at(Address(self.registry_address))
        value = registry.view().get_study(study_key)
        if not value:
            raise gl.vm.UserError("study not found")
        return value

    @gl.public.write.payable
    def fund_study(self, study_key: str) -> int:
        study = self._study(study_key)
        if study.get("status") != "OPEN":
            raise gl.vm.UserError("closed study cannot receive new funding")
        if study.get("creator", "").lower() != self._sender():
            raise gl.vm.UserError("only study creator may fund this pool")
        value = gl.message.value
        if int(value) <= 0:
            raise gl.vm.UserError("funding value must be positive")
        current = int(self.study_balances.get(study_key) or u256(0))
        self.study_balances[study_key] = u256(current + int(value))
        return int(self.study_balances[study_key])


    @gl.public.write
    def reclaim_closed_pool(self, study_key: str) -> None:
        study = self._study(study_key)
        sender = self._sender()
        if study.get("creator", "").lower() != sender:
            raise gl.vm.UserError("only study creator may reclaim")
        if study.get("status") != "CLOSED":
            raise gl.vm.UserError("study must be closed before reclaim")

        engine = gl.get_contract_at(Address(self.engine_address))
        attempts = engine.view().list_attempts_for_study(study_key)
        for attempt in attempts:
            if attempt.get("state") != "ASSESSED":
                raise gl.vm.UserError("unsettled replication attempt exists")
            record_key = study_key + ":" + str(attempt.get("attempt_key", ""))
            if record_key not in json.loads(self.final_records):
                raise gl.vm.UserError("assessed attempt is not finalized into the pool")

        balance = int(self.study_balances.get(study_key) or u256(0))
        if balance <= 0:
            raise gl.vm.UserError("no remaining study balance")
        self.study_balances[study_key] = u256(0)
        _Recipient(gl.message.sender_address).emit_transfer(value=u256(balance))

    @gl.public.write
    def register_finalized_outcome(
        self,
        study_key: str,
        attempt_key: str,
        researcher: str,
        verdict: str,
        assessment_digest: str,
    ) -> str:
        if self._sender() != self.engine_address:
            raise gl.vm.UserError("only replication engine may register outcomes")
        record_key = study_key + ":" + attempt_key
        records = json.loads(self.final_records)
        if record_key in records:
            raise gl.vm.UserError("final record already registered")
        if verdict not in ["REPLICATED", "FAILED_TO_REPLICATE", "PROTOCOL_DEVIATION", "INCONCLUSIVE"]:
            raise gl.vm.UserError("invalid verdict")
        if len(assessment_digest) != 64:
            raise gl.vm.UserError("invalid assessment digest")
        study = self._study(study_key)
        reward = int(study.get("reward_per_attempt_wei", 0))
        max_rewards = int(study.get("max_rewarded_attempts", 0))
        eligible = verdict in ["REPLICATED", "FAILED_TO_REPLICATE"]
        reserved = 0
        count = int(self.rewarded_count.get(study_key) or u256(0))
        balance = int(self.study_balances.get(study_key) or u256(0))
        if eligible and reward > 0 and count < max_rewards and balance >= reward:
            self.study_balances[study_key] = u256(balance - reward)
            self.rewarded_count[study_key] = u256(count + 1)
            wallet = researcher.lower()
            current_claimable = int(self.claimable.get(wallet) or u256(0))
            self.claimable[wallet] = u256(current_claimable + reward)
            reserved = reward

        record = {
            "record_key": record_key,
            "study_key": study_key,
            "attempt_key": attempt_key,
            "researcher": researcher.lower(),
            "verdict": verdict,
            "assessment_digest": assessment_digest,
            "recorded_at": self._now(),
            "reward_reserved_wei": reserved,
        }
        records[record_key] = record
        self.final_records = json.dumps(records, sort_keys=True, separators=(",", ":"))
        keys = json.loads(self.record_keys_json)
        keys.append(record_key)
        self.record_keys_json = json.dumps(keys, separators=(",", ":"))
        self.record_count = u256(int(self.record_count) + 1)
        return record_key

    @gl.public.write
    def withdraw(self, amount: u256) -> None:
        value = int(amount)
        if value <= 0:
            raise gl.vm.UserError("withdraw amount must be positive")
        sender = self._sender()
        available = int(self.claimable.get(sender) or u256(0))
        if value > available:
            raise gl.vm.UserError("withdraw amount exceeds claimable balance")
        self.claimable[sender] = u256(available - value)
        _Recipient(gl.message.sender_address).emit_transfer(value=u256(value))

    @gl.public.view
    def get_study_pool(self, study_key: str) -> dict:
        return {
            "available_wei": int(self.study_balances.get(study_key) or u256(0)),
            "rewarded_attempts": int(self.rewarded_count.get(study_key) or u256(0)),
        }

    @gl.public.view
    def get_claimable(self, researcher: str) -> int:
        return int(self.claimable.get(researcher.lower()) or u256(0))

    @gl.public.view
    def get_final_record(self, record_key: str) -> dict:
        return json.loads(self.final_records).get(record_key, {})

    @gl.public.view
    def list_final_records(self, offset: int, limit: int) -> dict:
        if offset < 0:
            offset = 0
        if limit < 1:
            limit = 1
        if limit > 50:
            limit = 50
        keys = json.loads(self.record_keys_json)
        selected = keys[offset : offset + limit]
        records = json.loads(self.final_records)
        return {"items": [records[k] for k in selected], "total": len(keys)}

    @gl.public.view
    def get_config(self) -> dict:
        return {
            "registry_address": self.registry_address,
            "engine_address": self.engine_address,
            "records": int(self.record_count),
        }
