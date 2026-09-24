"use client";
import { ADDRESSES, reader } from "@/consensus/genlayer-session";
import { toPlain } from "@/consensus/codec";
import { writeResearchTx, type ResearchTxState } from "@/consensus/write-pipeline";
import type { ArchiveRecord } from "@/research/publication/archive-model";
import {parseGen} from "@/research/money";
export async function readArchive(recordKey:string):Promise<ArchiveRecord|null>{if(!ADDRESSES.pool)return null;const raw=await (reader() as any).readContract({address:ADDRESSES.pool as `0x${string}`,functionName:"get_final_record",args:[recordKey]});const p:any=toPlain(raw);return p?.record_key?p as ArchiveRecord:null}
export async function readPool(studyKey:string){if(!ADDRESSES.pool)return{available_wei:"0",rewarded_attempts:0};const raw=await (reader() as any).readContract({address:ADDRESSES.pool as `0x${string}`,functionName:"get_study_pool",args:[studyKey]});return toPlain<any>(raw)}
export async function fundStudy(account:string,studyKey:string,gen:string,onState?:(s:ResearchTxState)=>void){const value=parseGen(gen||"0");return writeResearchTx({account,address:ADDRESSES.pool,functionName:"fund_study",args:[studyKey],value,onState})}
export async function readClaimable(address:string){if(!ADDRESSES.pool)return"0";const raw=await (reader() as any).readContract({address:ADDRESSES.pool as `0x${string}`,functionName:"get_claimable",args:[address]});return String(toPlain(raw))}
export async function withdraw(account:string,wei:string,onState?:(s:ResearchTxState)=>void){return writeResearchTx({account,address:ADDRESSES.pool,functionName:"withdraw",args:[BigInt(wei)],onState})}

export async function reclaimClosedPool(account:string,studyKey:string,onState?:(s:ResearchTxState)=>void){return writeResearchTx({account,address:ADDRESSES.pool,functionName:"reclaim_closed_pool",args:[studyKey],onState})}
