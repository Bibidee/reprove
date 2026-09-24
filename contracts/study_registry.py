# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
import re
from genlayer import *


class StudyRegistry(gl.Contract):
    """Immutable preregistration registry for REPROVE studies.

    A study is frozen at creation. The creator may close it to new attempts,
    but cannot rewrite the claim, protocol, outcome rule, evidence policy,
    or reward policy after registration.
    """

    studies: TreeMap[str, str]
    creator_index: TreeMap[str, str]
    study_keys_json: str
    study_count: u256

    def __init__(self):
        self.studies = TreeMap()
        self.creator_index = TreeMap()
        self.study_keys_json = "[]"
        self.study_count = u256(0)

    def _sender(self) -> str:
        return gl.message.sender_address.as_hex.lower()

    def _now(self) -> str:
        return str(gl.message_raw["datetime"])

    def _must_text(self, value: str, label: str, minimum: int, maximum: int) -> str:
        clean = value.strip()
        if len(clean) < minimum or len(clean) > maximum:
            raise gl.vm.UserError(f"{label} length out of range")
        return clean

    def _parse_object(self, raw: str, label: str) -> dict:
        if len(raw) > 24000:
            raise gl.vm.UserError(f"{label} too large")
        try:
            value = json.loads(raw)
        except Exception:
            raise gl.vm.UserError(f"{label} must be valid JSON")
        if not isinstance(value, dict):
            raise gl.vm.UserError(f"{label} must be a JSON object")
        return value

    def _policy_origins(self, value, label: str) -> list:
        if value is None:
            return []
        if not isinstance(value, list) or len(value) > 12:
            raise gl.vm.UserError(f"{label} must be a list of at most 12 origins")
        out = []
        for item in value:
            origin = str(item).strip().lower().rstrip("/")
            if len(origin) < 12 or len(origin) > 260:
                raise gl.vm.UserError(f"{label} contains invalid origin")
            if re.fullmatch(r"https://[a-z0-9.-]+", origin) is None:
                raise gl.vm.UserError(f"{label} origins must be exact https origins without paths")
            if origin not in out:
                out.append(origin)
        return out

    @gl.public.write
    def create_study(
        self,
        study_key: str,
        title: str,
        field: str,
        claim: str,
        protocol_json: str,
        outcome_rule: str,
        evidence_policy_json: str,
        reward_per_attempt_wei: u256,
        max_rewarded_attempts: u256,
    ) -> str:
        key = self._must_text(study_key, "study_key", 3, 64)
        if re.fullmatch(r"[A-Za-z0-9_-]+", key) is None:
            raise gl.vm.UserError("study_key may contain only letters, numbers, _ and -")
        if key in self.studies:
            raise gl.vm.UserError("study_key already exists")

        title = self._must_text(title, "title", 6, 180)
        field = self._must_text(field, "field", 2, 80)
        claim = self._must_text(claim, "claim", 20, 3000)
        outcome_rule = self._must_text(outcome_rule, "outcome_rule", 20, 4000)
        protocol = self._parse_object(protocol_json, "protocol_json")
        evidence_policy = self._parse_object(evidence_policy_json, "evidence_policy_json")

        required_protocol = ["population", "procedure", "measurement", "analysis", "window"]
        for name in required_protocol:
            if name not in protocol or not str(protocol[name]).strip():
                raise gl.vm.UserError(f"protocol missing {name}")

        required_evidence = evidence_policy.get("required_kinds", [])
        allowed_evidence = ["DATASET", "METHOD", "ANALYSIS", "RESULT_TABLE", "PREREGISTRATION_REFERENCE", "INDEPENDENT_OBSERVATION", "SUPPLEMENT"]
        if not isinstance(required_evidence, list) or len(required_evidence) < 2:
            raise gl.vm.UserError("evidence policy requires at least two evidence kinds")
        normalized_required = []
        for kind in required_evidence:
            name = str(kind).upper()
            if name not in allowed_evidence:
                raise gl.vm.UserError("evidence policy contains unsupported kind")
            if name not in normalized_required:
                normalized_required.append(name)
        if len(normalized_required) < 2:
            raise gl.vm.UserError("evidence policy requires two distinct evidence kinds")
        evidence_policy["required_kinds"] = normalized_required
        min_origins = int(evidence_policy.get("min_distinct_origins", 1))
        if min_origins < 1 or min_origins > 8:
            raise gl.vm.UserError("min_distinct_origins out of range")
        evidence_policy["min_distinct_origins"] = min_origins
        allowed_origins = self._policy_origins(evidence_policy.get("allowed_origins", []), "allowed_origins")
        required_origins = self._policy_origins(evidence_policy.get("required_origins", []), "required_origins")
        if allowed_origins:
            for origin in required_origins:
                if origin not in allowed_origins:
                    raise gl.vm.UserError("required_origins must be included in allowed_origins when allowlist is used")
        evidence_policy["allowed_origins"] = allowed_origins
        evidence_policy["required_origins"] = required_origins

        max_rewards = int(max_rewarded_attempts)
        reward = int(reward_per_attempt_wei)
        if max_rewards < 0 or max_rewards > 100:
            raise gl.vm.UserError("max_rewarded_attempts out of range")
        if reward < 0:
            raise gl.vm.UserError("reward cannot be negative")
        if reward > 0 and max_rewards == 0:
            raise gl.vm.UserError("rewarded study needs max_rewarded_attempts > 0")

        creator = self._sender()
        record = {
            "study_key": key,
            "title": title,
            "field": field,
            "claim": claim,
            "protocol": protocol,
            "outcome_rule": outcome_rule,
            "evidence_policy": evidence_policy,
            "reward_per_attempt_wei": reward,
            "max_rewarded_attempts": max_rewards,
            "creator": creator,
            "status": "OPEN",
            "registered_at": self._now(),
            "closed_at": "",
            "revision": 1,
        }
        self.studies[key] = json.dumps(record, sort_keys=True, separators=(",", ":"))

        keys = json.loads(self.study_keys_json)
        keys.append(key)
        self.study_keys_json = json.dumps(keys, separators=(",", ":"))

        mine = json.loads(self.creator_index.get(creator) or "[]")
        mine.append(key)
        self.creator_index[creator] = json.dumps(mine, separators=(",", ":"))
        self.study_count = u256(int(self.study_count) + 1)
        return key

    @gl.public.write
    def close_study(self, study_key: str) -> None:
        if study_key not in self.studies:
            raise gl.vm.UserError("study not found")
        record = json.loads(self.studies[study_key])
        if record["creator"] != self._sender():
            raise gl.vm.UserError("only study creator may close")
        if record["status"] == "CLOSED":
            raise gl.vm.UserError("study already closed")
        record["status"] = "CLOSED"
        record["closed_at"] = self._now()
        self.studies[study_key] = json.dumps(record, sort_keys=True, separators=(",", ":"))

    @gl.public.view
    def get_study(self, study_key: str) -> dict:
        raw = self.studies.get(study_key)
        return json.loads(raw) if raw else {}

    @gl.public.view
    def has_study(self, study_key: str) -> bool:
        return bool(self.studies.get(study_key))

    @gl.public.view
    def list_studies(self, offset: int, limit: int) -> dict:
        if offset < 0:
            offset = 0
        if limit < 1:
            limit = 1
        if limit > 50:
            limit = 50
        keys = json.loads(self.study_keys_json)
        selected = keys[offset : offset + limit]
        items = [json.loads(self.studies[k]) for k in selected]
        return {"items": items, "total": len(keys), "offset": offset, "limit": limit}

    @gl.public.view
    def list_creator_studies(self, creator: str) -> list:
        keys = json.loads(self.creator_index.get(creator.lower()) or "[]")
        return [json.loads(self.studies[k]) for k in keys]

    @gl.public.view
    def get_stats(self) -> dict:
        keys = json.loads(self.study_keys_json)
        open_count = 0
        for key in keys:
            if json.loads(self.studies[key])["status"] == "OPEN":
                open_count += 1
        return {"studies": len(keys), "open": open_count, "closed": len(keys) - open_count}
