export type StudyStatus = "OPEN" | "CLOSED";

export type Protocol = {
  population: string;
  procedure: string;
  measurement: string;
  analysis: string;
  window: string;
  [key: string]: unknown;
};

export type EvidencePolicy = {
  required_kinds: string[];
  min_distinct_origins?: number;
  allowed_origins?: string[];
  required_origins?: string[];
  notes?: string;
  min_distinct_artifacts?: number;
  provenance_policy?: ProvenancePolicy;
};

export type AnalysisSpec = {
  version: number;
  profile: "ONE_SAMPLE_THRESHOLD"|"TWO_GROUP_MEAN_DIFF"|"BINARY_RATE_DIFF"|"UNSUPPORTED";
  schema_version?: number;
  value_field?: string;
  scale?: number;
  comparator?: ">="|">"|"<="|"<";
  threshold_scaled?: number;
  min_value_scaled?: number;
  max_value_scaled?: number;
  group_field?: string;
  group_a?: string;
  group_b?: string;
  success_field?: string;
};

export type ProvenancePolicy = {
  version?: number;
  immutable_required: boolean;
  allowed_profiles?: string[];
  required_profiles?: string[];
  minimum_provenance_level?: number;
  max_artifact_chars?: number;
  machine_readable_dataset?: boolean;
};

export type Study = {
  study_key: string;
  title: string;
  field: string;
  claim: string;
  protocol: Protocol;
  outcome_rule: string;
  evidence_policy: EvidencePolicy;
  analysis_spec?: AnalysisSpec;
  attempt_ttl_seconds?: number;
  study_digest?: string;
  reward_per_attempt_wei: number | string;
  max_rewarded_attempts: number;
  creator: string;
  status: StudyStatus;
  registered_at: string;
  closed_at: string;
  revision: number;
};

export type StudyDraft = {
  studyKey: string;
  title: string;
  field: string;
  claim: string;
  protocol: Protocol;
  outcomeRule: string;
  evidencePolicy: EvidencePolicy;
  rewardGen: string;
  maxRewardedAttempts: string;
  analysisSpec: AnalysisSpec;
  provenancePolicy: ProvenancePolicy;
  attemptTtlSeconds: string;
};
