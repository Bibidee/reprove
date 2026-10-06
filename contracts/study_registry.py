# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import hashlib
import json
import re
from genlayer import *


class StudyRegistry(gl.Contract):
    """Immutable preregistration registry for REPROVE V2 studies.

    V2 keeps the original registry boundary but freezes typed analysis,
    provenance, artifact-size and attempt-lifetime policy at registration.
    The legacy create_study entry point remains available for compatibility;
    V2 clients use create_study_v2 with explicit policies.
    """

    studies: TreeMap[str, str]
    creator_index: TreeMap[str, str]
    study_keys_json: str
    study_count: u256

    ALLOWED_KINDS = [
        "DATASET", "METHOD", "ANALYSIS", "RESULT_TABLE",
        "PREREGISTRATION_REFERENCE", "INDEPENDENT_OBSERVATION", "SUPPLEMENT",
    ]
    ANALYSIS_PROFILES = ["ONE_SAMPLE_THRESHOLD", "TWO_GROUP_MEAN_DIFF", "BINARY_RATE_DIFF", "UNSUPPORTED"]
    AUTHORITY_PROFILES = ["GITHUB_COMMIT", "ZENODO_RECORD", "GENERIC_CONTENT_ADDRESS"]

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
        clean = str(value).strip()
        if len(clean) < minimum or len(clean) > maximum:
            raise gl.vm.UserError(f"{label} length out of range")
        return clean

    def _parse_object(self, raw: str, label: str) -> dict:
        if isinstance(raw, dict):
            return raw
        if len(raw) > 24000:
            raise gl.vm.UserError(f"{label} too large")
        try:
            value = json.loads(raw)
        except Exception:
            raise gl.vm.UserError(f"{label} must be valid JSON")
        if not isinstance(value, dict):
            raise gl.vm.UserError(f"{label} must be a JSON object")
        return value

    def _bounded_int(self, value, label: str, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except Exception:
            raise gl.vm.UserError(f"{label} must be an integer")
        if parsed < minimum or parsed > maximum:
            raise gl.vm.UserError(f"{label} out of range")
        return parsed

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

    def _profile_list(self, value, label: str) -> list:
        if value is None:
            return []
        if not isinstance(value, list) or len(value) > 3:
            raise gl.vm.UserError(f"{label} must contain at most three profiles")
        out = []
        for item in value:
            profile = str(item).strip().upper()
            if profile not in self.AUTHORITY_PROFILES:
                raise gl.vm.UserError(f"{label} contains unsupported authority profile")
            if profile not in out:
                out.append(profile)
        return out

    def _normalize_analysis(self, raw: dict) -> dict:
        profile = str(raw.get("profile", "UNSUPPORTED")).strip().upper()
        if profile not in self.ANALYSIS_PROFILES:
            raise gl.vm.UserError("unsupported analysis profile")
        version = self._bounded_int(raw.get("version", 1), "analysis_spec.version", 1, 2)
        if profile == "UNSUPPORTED":
            return {"version": version, "profile": profile}
        comparator = str(raw.get("comparator", ">=")).strip()
        if comparator not in [">=", ">", "<=", "<"]:
            raise gl.vm.UserError("analysis comparator is unsupported")
        scale = self._bounded_int(raw.get("scale", 1000), "analysis_spec.scale", 1, 1000000)
        if scale not in [1, 10, 100, 1000, 10000, 100000, 1000000]:
            raise gl.vm.UserError("analysis_spec.scale must be a power of ten")
        value_field = self._must_text(raw.get("value_field", "value"), "analysis_spec.value_field", 1, 64)
        minimum = self._bounded_int(raw.get("min_value_scaled", -1000000000000000), "analysis_spec.min_value_scaled", -1000000000000000, 1000000000000000)
        maximum = self._bounded_int(raw.get("max_value_scaled", 1000000000000000), "analysis_spec.max_value_scaled", -1000000000000000, 1000000000000000)
        if minimum > maximum:
            raise gl.vm.UserError("analysis value range is invalid")
        result = {
            "version": version,
            "profile": profile,
            "schema_version": self._bounded_int(raw.get("schema_version", 1), "analysis_spec.schema_version", 1, 4),
            "value_field": value_field,
            "scale": scale,
            "comparator": comparator,
            "threshold_scaled": self._bounded_int(raw.get("threshold_scaled", 0), "analysis_spec.threshold_scaled", -1000000000000000, 1000000000000000),
            "min_value_scaled": minimum,
            "max_value_scaled": maximum,
        }
        if profile in ["TWO_GROUP_MEAN_DIFF", "BINARY_RATE_DIFF"]:
            result["group_field"] = self._must_text(raw.get("group_field", "group"), "analysis_spec.group_field", 1, 64)
            result["group_a"] = self._must_text(raw.get("group_a", "A"), "analysis_spec.group_a", 1, 64)
            result["group_b"] = self._must_text(raw.get("group_b", "B"), "analysis_spec.group_b", 1, 64)
            if result["group_a"] == result["group_b"]:
                raise gl.vm.UserError("analysis groups must differ")
        if profile == "BINARY_RATE_DIFF":
            result["success_field"] = self._must_text(raw.get("success_field", "success"), "analysis_spec.success_field", 1, 64)
            if scale != 1:
                raise gl.vm.UserError("binary rate analysis scale must be 1")
        return result

    def _normalize_provenance(self, raw: dict) -> dict:
        if not isinstance(raw, dict):
            raw = {}
        allowed_profiles = self._profile_list(raw.get("allowed_profiles", []), "allowed_profiles")
        required_profiles = self._profile_list(raw.get("required_profiles", []), "required_profiles")
        for profile in required_profiles:
            if allowed_profiles and profile not in allowed_profiles:
                raise gl.vm.UserError("required_profiles must be included in allowed_profiles")
        immutable_required = bool(raw.get("immutable_required", bool(raw)))
        max_chars = self._bounded_int(raw.get("max_artifact_chars", 48000), "max_artifact_chars", 1024, 50000)
        min_level = self._bounded_int(raw.get("minimum_provenance_level", 0), "minimum_provenance_level", 0, 3)
        return {
            "version": self._bounded_int(raw.get("version", 1), "provenance_policy.version", 1, 2),
            "immutable_required": immutable_required,
            "allowed_profiles": allowed_profiles,
            "required_profiles": required_profiles,
            "minimum_provenance_level": min_level,
            "max_artifact_chars": max_chars,
            "machine_readable_dataset": bool(raw.get("machine_readable_dataset", False)),
        }

    def _normalize_evidence_policy(self, raw: dict, provenance: dict) -> dict:
        required_evidence = raw.get("required_kinds", [])
        if not isinstance(required_evidence, list) or len(required_evidence) < 2 or len(required_evidence) > 8:
            raise gl.vm.UserError("evidence policy requires 2 to 8 evidence kinds")
        normalized_required = []
        for kind in required_evidence:
            name = str(kind).upper()
            if name not in self.ALLOWED_KINDS:
                raise gl.vm.UserError("evidence policy contains unsupported kind")
            if name not in normalized_required:
                normalized_required.append(name)
        if len(normalized_required) < 2:
            raise gl.vm.UserError("evidence policy requires two distinct evidence kinds")
        min_origins = self._bounded_int(raw.get("min_distinct_origins", 1), "min_distinct_origins", 1, 8)
        allowed_origins = self._policy_origins(raw.get("allowed_origins", []), "allowed_origins")
        required_origins = self._policy_origins(raw.get("required_origins", []), "required_origins")
        if allowed_origins:
            for origin in required_origins:
                if origin not in allowed_origins:
                    raise gl.vm.UserError("required_origins must be included in allowed_origins when allowlist is used")
        min_artifacts = self._bounded_int(raw.get("min_distinct_artifacts", len(normalized_required)), "min_distinct_artifacts", len(normalized_required), 8)
        return {
            "required_kinds": normalized_required,
            "min_distinct_origins": min_origins,
            "min_distinct_artifacts": min_artifacts,
            "allowed_origins": allowed_origins,
            "required_origins": required_origins,
            "provenance_policy": provenance,
        }

    def _digest(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _create_study(
        self, study_key: str, title: str, field: str, claim: str, protocol_json: str,
        outcome_rule: str, evidence_policy_json: str, analysis_spec_json: str,
        provenance_policy_json: str, attempt_ttl_seconds: int,
        reward_per_attempt_wei: u256, max_rewarded_attempts: u256, revision: int = 2,
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
        evidence_policy_raw = self._parse_object(evidence_policy_json, "evidence_policy_json")
        for name in ["population", "procedure", "measurement", "analysis", "window"]:
            if name not in protocol or not str(protocol[name]).strip():
                raise gl.vm.UserError(f"protocol missing {name}")
        analysis_raw = self._parse_object(analysis_spec_json, "analysis_spec_json") if analysis_spec_json else protocol.get("analysis_spec", evidence_policy_raw.get("analysis_spec", {}))
        analysis_spec = self._normalize_analysis(analysis_raw if isinstance(analysis_raw, dict) else {})
        provenance_raw = self._parse_object(provenance_policy_json, "provenance_policy_json") if provenance_policy_json else evidence_policy_raw.get("provenance_policy", {})
        provenance = self._normalize_provenance(provenance_raw if isinstance(provenance_raw, dict) else {})
        evidence_policy = self._normalize_evidence_policy(evidence_policy_raw, provenance)
        ttl = self._bounded_int(attempt_ttl_seconds or evidence_policy_raw.get("attempt_ttl_seconds", 604800), "attempt_ttl_seconds", 60, 31536000)
        max_rewards = self._bounded_int(max_rewarded_attempts, "max_rewarded_attempts", 0, 100)
        reward = self._bounded_int(reward_per_attempt_wei, "reward_per_attempt_wei", 0, 10**30)
        if reward > 0 and max_rewards == 0:
            raise gl.vm.UserError("rewarded study needs max_rewarded_attempts > 0")

        immutable_definition = {
            "study_key": key, "title": title, "field": field, "claim": claim,
            "protocol": protocol, "outcome_rule": outcome_rule,
            "evidence_policy": evidence_policy, "analysis_spec": analysis_spec,
            "attempt_ttl_seconds": ttl, "reward_per_attempt_wei": reward,
            "max_rewarded_attempts": max_rewards,
        }
        record = dict(immutable_definition)
        record.update({
            "creator": self._sender(), "status": "OPEN", "registered_at": self._now(),
            "closed_at": "", "revision": revision,
            "study_digest": self._digest(json.dumps(immutable_definition, sort_keys=True, separators=(",", ":"))),
        })
        self.studies[key] = json.dumps(record, sort_keys=True, separators=(",", ":"))
        keys = json.loads(self.study_keys_json)
        keys.append(key)
        self.study_keys_json = json.dumps(keys, separators=(",", ":"))
        creator = self._sender()
        mine = json.loads(self.creator_index.get(creator) or "[]")
        mine.append(key)
        self.creator_index[creator] = json.dumps(mine, separators=(",", ":"))
        self.study_count = u256(int(self.study_count) + 1)
        return key

    @gl.public.write
    def create_study(
        self, study_key: str, title: str, field: str, claim: str, protocol_json: str,
        outcome_rule: str, evidence_policy_json: str, reward_per_attempt_wei: u256,
        max_rewarded_attempts: u256,
    ) -> str:
        return self._create_study(study_key, title, field, claim, protocol_json, outcome_rule, evidence_policy_json, "", "", 0, reward_per_attempt_wei, max_rewarded_attempts, 1)

    @gl.public.write
    def create_study_v2(
        self, study_key: str, title: str, field: str, claim: str, protocol_json: str,
        outcome_rule: str, evidence_policy_json: str, analysis_spec_json: str,
        provenance_policy_json: str, attempt_ttl_seconds: u256,
        reward_per_attempt_wei: u256, max_rewarded_attempts: u256,
    ) -> str:
        return self._create_study(study_key, title, field, claim, protocol_json, outcome_rule, evidence_policy_json, analysis_spec_json, provenance_policy_json, int(attempt_ttl_seconds), reward_per_attempt_wei, max_rewarded_attempts)

    @gl.public.write
    def create_study_v2_structured(
        self, study_key: str, title: str, field: str, claim: str, protocol: dict,
        outcome_rule: str, evidence_policy: dict, analysis_spec: dict,
        provenance_policy: dict, attempt_ttl_seconds: u256,
        reward_per_attempt_wei: u256, max_rewarded_attempts: u256,
    ) -> str:
        return self._create_study(
            study_key, title, field, claim, protocol, outcome_rule,
            evidence_policy, analysis_spec, provenance_policy,
            int(attempt_ttl_seconds), reward_per_attempt_wei,
            max_rewarded_attempts,
        )

    @gl.public.write
    def create_study_v2_bytes(
        self, study_key: str, title: str, field: str, claim: str, protocol_bytes: bytes,
        outcome_rule: str, evidence_policy_bytes: bytes, analysis_spec_bytes: bytes,
        provenance_policy_bytes: bytes, attempt_ttl_seconds: u256,
        reward_per_attempt_wei: u256, max_rewarded_attempts: u256,
    ) -> str:
        def decode_payload(value) -> str:
            if isinstance(value, bytes):
                return value.decode("utf-8")
            text = str(value)
            if text.startswith("bytes:b#"):
                return bytes.fromhex(text[8:]).decode("utf-8")
            return text
        protocol = decode_payload(protocol_bytes)
        evidence_policy = decode_payload(evidence_policy_bytes)
        analysis_spec = decode_payload(analysis_spec_bytes)
        provenance_policy = decode_payload(provenance_policy_bytes)
        return self._create_study(
            study_key, title, field, claim, protocol, outcome_rule,
            evidence_policy, analysis_spec, provenance_policy,
            int(attempt_ttl_seconds), reward_per_attempt_wei,
            max_rewarded_attempts,
        )

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
        return {"items": [json.loads(self.studies[k]) for k in selected], "total": len(keys), "offset": offset, "limit": limit}

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
