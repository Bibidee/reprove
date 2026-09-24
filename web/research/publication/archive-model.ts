import type { Verdict } from "@/research/replication/attempt-model";
export type ArchiveRecord = {
  record_key: string;
  study_key: string;
  attempt_key: string;
  researcher: string;
  verdict: Verdict;
  assessment_digest: string;
  recorded_at: string;
  reward_reserved_wei: number | string;
};
