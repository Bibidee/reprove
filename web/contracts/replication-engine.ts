"use client";
import { ADDRESSES, reader } from "@/consensus/genlayer-session";
import { toPlain } from "@/consensus/codec";
import { writeResearchTx, type ResearchTxState } from "@/consensus/write-pipeline";
import type { Attempt, EvidenceLeaf } from "@/research/replication/attempt-model";

export async function readAttempt(key:string):Promise<Attempt|null>{if(!ADDRESSES.engine)return null;const raw=await (reader() as any).readContract({address:ADDRESSES.engine as `0x${string}`,functionName:"get_attempt",args:[key]});const p:any=toPlain(raw);return p?.attempt_key?p as Attempt:null}
export async function readStudyAttempts(studyKey:string):Promise<Attempt[]>{if(!ADDRESSES.engine)return[];const raw=await (reader() as any).readContract({address:ADDRESSES.engine as `0x${string}`,functionName:"list_attempts_for_study",args:[studyKey]});return toPlain(raw) as Attempt[]}
export async function beginAttempt(account:string,studyKey:string,attemptKey:string,statement:string,onState?:(s:ResearchTxState)=>void){return writeResearchTx({account,address:ADDRESSES.engine,functionName:"begin_attempt",args:[studyKey,attemptKey,statement],onState})}
export async function evaluateAttempt(account:string,attemptKey:string,evidence:EvidenceLeaf[],reported:Record<string,unknown>,onState?:(s:ResearchTxState)=>void){return writeResearchTx({account,address:ADDRESSES.engine,functionName:"evaluate_attempt",args:[attemptKey,JSON.stringify(evidence),JSON.stringify(reported)],onState})}
