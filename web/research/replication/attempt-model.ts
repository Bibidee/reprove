export type Verdict = "REPLICATED" | "FAILED_TO_REPLICATE" | "PROTOCOL_DEVIATION" | "INCONCLUSIVE";
export type AttemptState = "NOTEBOOK" | "ASSESSED";

export type EvidenceLeaf = {
  kind: "DATASET"|"METHOD"|"ANALYSIS"|"RESULT_TABLE"|"PREREGISTRATION_REFERENCE"|"INDEPENDENT_OBSERVATION"|"SUPPLEMENT";
  url: string;
  origin?: string;
  note: string;
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
  verdict: Verdict;
  protocol_compliance: "SATISFIED"|"DEVIATED"|"UNCERTAIN";
  evidence_sufficiency: "SUFFICIENT"|"INSUFFICIENT"|"UNAVAILABLE"|"CONFLICTED";
  outcome_satisfied: "YES"|"NO"|"UNKNOWN";
  required_evidence_present: "YES"|"NO"|"UNKNOWN";
  summary: string;
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
  evidence_manifest: EvidenceLeaf[];
  reported_result: Record<string, unknown>;
  assessment: Partial<Assessment>;
  assessment_digest: string;
};
