export type Verdict = "REPLICATED" | "FAILED_TO_REPLICATE" | "PROTOCOL_DEVIATION" | "INCONCLUSIVE";
export type AttemptState = "NOTEBOOK" | "CAPSULE_COMMITTED" | "ASSESSED" | "ABANDONED" | "EXPIRED";
export type AuthorityProfile = "GITHUB_COMMIT" | "ZENODO_RECORD" | "GENERIC_CONTENT_ADDRESS";

export type EvidenceLeaf = {
  kind: "DATASET"|"METHOD"|"ANALYSIS"|"RESULT_TABLE"|"PREREGISTRATION_REFERENCE"|"INDEPENDENT_OBSERVATION"|"SUPPLEMENT";
  url: string;
  origin?: string;
  note: string;
  authority_profile?: AuthorityProfile;
  artifact_id?: string;
  sha256?: string;
  provenance?: {
    repository?: string;
    commit?: string;
    path?: string;
    record_id?: string;
    filename?: string;
    [key: string]: unknown;
  };
  media_type?: string;
};

export type ReportedResult = {
  mean_num?: number;
  mean_den?: number;
  difference_num?: number;
  difference_den?: number;
  threshold_met?: boolean;
  sample_size?: string;
  observed_effect?: string;
  analysis_statement?: string;
  notes?: string;
};

export type EvidenceReceipt = {
  kind: EvidenceLeaf["kind"];
  url: string;
  origin: string;
  fetch_status: "OK"|"UNAVAILABLE";
  content_window_sha256: string;
  content_window_chars: number;
};

export type Assessment = {
  assessment_version?: number;
  verdict: Verdict;
  protocol_compliance: "SATISFIED"|"DEVIATED"|"UNCERTAIN";
  evidence_sufficiency: "SUFFICIENT"|"INSUFFICIENT"|"UNAVAILABLE"|"CONFLICTED";
  threshold_outcome?: "YES"|"NO"|"UNKNOWN";
  reported_result_match?: "YES"|"NO";
  required_evidence_present: "YES"|"NO"|"UNKNOWN";
  provenance_status?: "VERIFIED"|"FAILED"|"UNAVAILABLE";
  artifact_integrity_status?: "VERIFIED"|"FAILED"|"UNAVAILABLE";
  statistical_profile?: string;
  computed_result?: Record<string, unknown>;
  reason_codes?: string[];
  artifact_results?: Array<Record<string, unknown>>;
  summary?: string;
  outcome_satisfied?: "YES"|"NO"|"UNKNOWN";
  evidence_receipts?: EvidenceReceipt[];
  evidence_snapshot_digest?: string;
};

export type Attempt = {
  attempt_key: string;
  study_key: string;
  researcher: string;
  replication_statement: string;
  state: AttemptState;
  created_at: string;
  evaluated_at: string;
  evidence_manifest?: EvidenceLeaf[];
  reported_result?: Record<string, unknown>;
  capsule_digest?: string;
  expires_at?: string;
  assessment: Partial<Assessment>;
  assessment_digest: string;
};
