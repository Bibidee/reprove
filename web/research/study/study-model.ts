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
};

export type Study = {
  study_key: string;
  title: string;
  field: string;
  claim: string;
  protocol: Protocol;
  outcome_rule: string;
  evidence_policy: EvidencePolicy;
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
};
