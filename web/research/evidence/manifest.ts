import type { EvidenceLeaf } from "@/research/replication/attempt-model";

export const EVIDENCE_KINDS: EvidenceLeaf["kind"][] = [
  "DATASET","METHOD","ANALYSIS","RESULT_TABLE","PREREGISTRATION_REFERENCE","INDEPENDENT_OBSERVATION","SUPPLEMENT"
];

export function normaliseEvidence(leaves: EvidenceLeaf[]): EvidenceLeaf[] {
  const seen = new Set<string>();
  return leaves.map(x => ({...x, url:x.url.trim(), note:x.note.trim()})).filter(x => {
    if (!x.url.startsWith("https://") || seen.has(x.url)) return false;
    seen.add(x.url);
    return true;
  });
}
