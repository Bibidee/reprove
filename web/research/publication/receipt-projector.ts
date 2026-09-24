import type { ArchiveRecord } from "./archive-model";
import { formatGen } from "@/research/money";
export function archiveTitle(v:ArchiveRecord["verdict"]){return v==="REPLICATED"?"Replicated under protocol":v==="FAILED_TO_REPLICATE"?"Failed to replicate under protocol":v==="PROTOCOL_DEVIATION"?"Protocol deviation": "Inconclusive"}
export function rewardGen(wei:number|string){return formatGen(wei,4)}
