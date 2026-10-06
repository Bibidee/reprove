# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
import re
from genlayer import *


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


class ResearchPool(gl.Contract):
    """Finality-gated V2 certificate and reward settlement.

    Reclaim readiness is constant-time with respect to historical attempts:
    the pool compares engine active/assessed counters with its own finalized
    child-record counter instead of scanning every notebook.
    """

    registry_address: str
    engine_address: str
    study_balances: TreeMap[str, u256]
    rewarded_count: TreeMap[str, u256]
    finalized_record_counts_json: str
    claimable: TreeMap[str, u256]
    claimable_json: str
    withdrawn_json: str
    final_records: str
    record_keys_json: str
    record_count: u256

    def __init__(self, registry_address: str, engine_address: str):
        registry_text = registry_address.as_hex if hasattr(registry_address, "as_hex") else str(registry_address)
        engine_text = engine_address.as_hex if hasattr(engine_address, "as_hex") else str(engine_address)
        if registry_text.startswith("address:"): registry_text = registry_text[8:]
        if registry_text.startswith("addr#"): registry_text = registry_text[5:]
        if engine_text.startswith("address:"): engine_text = engine_text[8:]
        if engine_text.startswith("addr#"): engine_text = engine_text[5:]
        if not registry_text.startswith("0x") or len(registry_text) != 42: raise gl.vm.UserError("invalid registry address")
        if not engine_text.startswith("0x") or len(engine_text) != 42: raise gl.vm.UserError("invalid engine address")
        self.registry_address = registry_text.lower(); self.engine_address = engine_text.lower()
        self.study_balances = TreeMap(); self.rewarded_count = TreeMap(); self.finalized_record_counts_json = "{}"; self.claimable = TreeMap()
        self.claimable_json = "{}"; self.withdrawn_json = "{}"; self.final_records = "{}"; self.record_keys_json = "[]"; self.record_count = u256(0)

    def _sender(self) -> str:
        return gl.message.sender_address.as_hex.lower()

    def _now(self) -> str:
        return str(gl.message_raw["datetime"])

    def _finalized_count(self, study_key: str) -> int:
        return int(json.loads(self.finalized_record_counts_json).get(study_key, 0))

    def _set_finalized_count(self, study_key: str, value: int) -> None:
        if int(value) < 0: raise gl.vm.UserError("finalized record counter underflow")
        counts = json.loads(self.finalized_record_counts_json); counts[study_key] = int(value)
        self.finalized_record_counts_json = json.dumps(counts, sort_keys=True, separators=(",", ":"))

    def _study(self, study_key: str) -> dict:
        registry = gl.get_contract_at(Address(self.registry_address)); value = registry.view().get_study(study_key)
        if not value: raise gl.vm.UserError("study not found")
        return value

    def _computed_claimable(self, wallet: str) -> int:
        reserved = int(json.loads(self.claimable_json).get(wallet, 0)); withdrawn = int(json.loads(self.withdrawn_json).get(wallet, 0)); return max(reserved - withdrawn, 0)

    def _wallet_key(self, wallet) -> str:
        return wallet.as_hex.lower() if hasattr(wallet, "as_hex") else str(wallet).lower()

    @gl.public.write.payable
    def fund_study(self, study_key: str) -> int:
        study = self._study(study_key)
        if study.get("status") != "OPEN": raise gl.vm.UserError("closed study cannot receive new funding")
        if study.get("creator", "").lower() != self._sender(): raise gl.vm.UserError("only study creator may fund this pool")
        value = int(gl.message.value)
        if value <= 0: raise gl.vm.UserError("funding value must be positive")
        current = int(self.study_balances.get(study_key) or 0); self.study_balances[study_key] = u256(current + value); return current + value

    @gl.public.write
    def reclaim_closed_pool(self, study_key: str) -> None:
        study = self._study(study_key); sender = self._sender()
        if study.get("creator", "").lower() != sender: raise gl.vm.UserError("only study creator may reclaim")
        if study.get("status") != "CLOSED": raise gl.vm.UserError("study must be closed before reclaim")
        engine = gl.get_contract_at(Address(self.engine_address)); state = engine.view().get_study_settlement_state(study_key)
        active = int(state.get("active_attempts", 0)); assessed = int(state.get("assessed_attempts", 0)); finalized = self._finalized_count(study_key)
        if active > 0: raise gl.vm.UserError("active replication attempts remain")
        if assessed != finalized: raise gl.vm.UserError("assessed attempt is not finalized into the pool")
        balance = int(self.study_balances.get(study_key) or 0)
        if balance <= 0: raise gl.vm.UserError("no remaining study balance")
        self.study_balances[study_key] = u256(0); _Recipient(gl.message.sender_address).emit_transfer(value=u256(balance))

    @gl.public.write
    def register_finalized_outcome(self, study_key: str, attempt_key: str, researcher: str, verdict: str, assessment_digest: str) -> str:
        if self._sender() != self.engine_address: raise gl.vm.UserError("only replication engine may register outcomes")
        record_key = study_key + ":" + attempt_key; records = json.loads(self.final_records)
        if record_key in records: raise gl.vm.UserError("final record already registered")
        if verdict not in ["REPLICATED", "FAILED_TO_REPLICATE", "PROTOCOL_DEVIATION", "INCONCLUSIVE"]: raise gl.vm.UserError("invalid verdict")
        if re.fullmatch(r"[0-9a-fA-F]{64}", str(assessment_digest)) is None: raise gl.vm.UserError("invalid assessment digest")
        study = self._study(study_key); reward = int(study.get("reward_per_attempt_wei", 0)); maximum = int(study.get("max_rewarded_attempts", 0)); eligible = verdict in ["REPLICATED", "FAILED_TO_REPLICATE"]
        reserved = 0; count = int(self.rewarded_count.get(study_key) or 0); balance = int(self.study_balances.get(study_key) or 0)
        if eligible and reward > 0 and count < maximum and balance >= reward:
            self.study_balances[study_key] = u256(balance - reward); self.rewarded_count[study_key] = u256(count + 1); wallet = researcher.lower(); claimables = json.loads(self.claimable_json); claimables[wallet] = int(claimables.get(wallet, 0)) + reward; self.claimable_json = json.dumps(claimables, sort_keys=True, separators=(",", ":")); self.claimable[wallet] = u256(int(claimables[wallet])); reserved = reward
        records[record_key] = {"record_key": record_key, "study_key": study_key, "attempt_key": attempt_key, "researcher": researcher.lower(), "verdict": verdict, "assessment_digest": assessment_digest, "recorded_at": self._now(), "reward_reserved_wei": reserved, "certificate_version": 2}
        self.final_records = json.dumps(records, sort_keys=True, separators=(",", ":")); keys = json.loads(self.record_keys_json); keys.append(record_key); self.record_keys_json = json.dumps(keys, separators=(",", ":")); self.record_count = u256(int(self.record_count) + 1)
        self._set_finalized_count(study_key, self._finalized_count(study_key) + 1)
        return record_key

    @gl.public.write
    def withdraw(self, amount: u256) -> None:
        value = int(amount)
        if value <= 0: raise gl.vm.UserError("withdraw amount must be positive")
        sender = self._sender(); available = self._computed_claimable(sender)
        if value > available: raise gl.vm.UserError("withdraw amount exceeds claimable balance")
        withdrawn = json.loads(self.withdrawn_json); withdrawn[sender] = int(withdrawn.get(sender, 0)) + value; self.withdrawn_json = json.dumps(withdrawn, sort_keys=True, separators=(",", ":")); self.claimable[sender] = u256(available - value); _Recipient(gl.message.sender_address).emit_transfer(value=u256(value))

    @gl.public.view
    def get_study_pool(self, study_key: str) -> dict:
        return {"available_wei": int(self.study_balances.get(study_key) or 0), "rewarded_attempts": int(self.rewarded_count.get(study_key) or 0)}

    @gl.public.view
    def get_claimable(self, researcher: str) -> int:
        return self._computed_claimable(self._wallet_key(researcher))

    @gl.public.view
    def get_reclaim_readiness(self, study_key: str) -> dict:
        engine = gl.get_contract_at(Address(self.engine_address)); state = engine.view().get_study_settlement_state(study_key); active = int(state.get("active_attempts", 0)); assessed = int(state.get("assessed_attempts", 0)); finalized = self._finalized_count(study_key); balance = int(self.study_balances.get(study_key) or 0); study = self._study(study_key)
        reasons = []
        if study.get("status") != "CLOSED": reasons.append("STUDY_NOT_CLOSED")
        if active > 0: reasons.append("ACTIVE_ATTEMPTS_REMAIN")
        if assessed != finalized: reasons.append("PENDING_FINALIZED_ARCHIVE")
        if balance <= 0: reasons.append("NO_REMAINING_BALANCE")
        return {"study_status": study.get("status", "UNKNOWN"), "remaining_pool_wei": balance, "active_attempts": active, "assessed_attempts": assessed, "finalized_records": finalized, "eligible": len(reasons) == 0, "reasons": reasons}

    @gl.public.view
    def get_final_record(self, record_key: str) -> dict:
        return json.loads(self.final_records).get(record_key, {})

    @gl.public.view
    def list_final_records(self, offset: int, limit: int) -> dict:
        if offset < 0: offset = 0
        if limit < 1: limit = 1
        if limit > 50: limit = 50
        keys = json.loads(self.record_keys_json); selected = keys[offset : offset + limit]; records = json.loads(self.final_records); return {"items": [records[k] for k in selected], "total": len(keys)}

    @gl.public.view
    def get_config(self) -> dict:
        return {"registry_address": self.registry_address, "engine_address": self.engine_address, "records": int(self.record_count), "schema_version": 2}
