"use client";
import { ADDRESSES, reader } from "@/consensus/genlayer-session";
import { toPlain } from "@/consensus/codec";
import { writeResearchTx, type ResearchTxState } from "@/consensus/write-pipeline";
import type { Study, StudyDraft } from "@/research/study/study-model";
import {parseGen} from "@/research/money";

export async function readStudies(offset=0,limit=50):Promise<{items:Study[];total:number}>{
  if(!ADDRESSES.registry) return {items:[],total:0};
  const raw=await (reader() as any).readContract({address:ADDRESSES.registry as `0x${string}`,functionName:"list_studies",args:[offset,limit]});
  const p:any=toPlain(raw); return {items:(p.items||[]) as Study[],total:Number(p.total||0)};
}
export async function readStudy(key:string):Promise<Study|null>{
  if(!ADDRESSES.registry) return null;
  const raw=await (reader() as any).readContract({address:ADDRESSES.registry as `0x${string}`,functionName:"get_study",args:[key]});
  const p:any=toPlain(raw); return p?.study_key?p as Study:null;
}
export async function createStudy(account:string,d:StudyDraft,onState?:(s:ResearchTxState)=>void){
  const rewardWei=parseGen(d.rewardGen||"0");
  return writeResearchTx({account,address:ADDRESSES.registry,functionName:"create_study",args:[d.studyKey,d.title,d.field,d.claim,JSON.stringify(d.protocol),d.outcomeRule,JSON.stringify(d.evidencePolicy),rewardWei,BigInt(d.maxRewardedAttempts||"0")],onState});
}
export async function closeStudy(account:string,key:string,onState?:(s:ResearchTxState)=>void){return writeResearchTx({account,address:ADDRESSES.registry,functionName:"close_study",args:[key],onState})}
