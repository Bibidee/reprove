"use client";
import { reader, signer } from "./genlayer-session";
import { transactionsStatusNumberToName } from "genlayer-js/types";

export type ResearchTxPhase =
  |"AWAITING_SIGNATURE"|"SUBMITTED"|"CONSENSUS_RUNNING"|"PROVISIONAL"|"UNDETERMINED"|"READY_TO_FINALIZE"|"FINALIZED"|"FAILED";

export type ResearchTxState = { phase:ResearchTxPhase; txId?:string; statusName?:string; message:string; receipt?:any };

function feesFromEstimate(e:any){
  if(!e) return undefined;
  if(e.distribution && e.feeValue !== undefined) return {distribution:e.distribution, feeValue:e.feeValue};
  return undefined;
}

function statusNameOf(...values:any[]):string{
  for(const value of values){
    if(value===undefined||value===null||value==="") continue;
    const raw=String(value);
    const mapped=(transactionsStatusNumberToName as Record<string,string>)[raw];
    return String(mapped||raw).toUpperCase();
  }
  return "";
}

export async function writeResearchTx(opts:{account:string,address:string,functionName:string,args:any[],value?:bigint,onState?:(s:ResearchTxState)=>void}){
  const {account,address,functionName,args,value=0n,onState}=opts;
  if(!/^0x[a-fA-F0-9]{40}$/.test(address)) throw new Error("Canonical Studionet contract address is not configured for this action.");
  if(!/^0x[a-fA-F0-9]{40}$/.test(account)) throw new Error("Connected researcher address is invalid.");
  const client:any = signer(account);
  onState?.({phase:"AWAITING_SIGNATURE",message:"Review the transaction in your wallet."});
  const draft={address:address as `0x${string}`,functionName,args,value};
  let estimate:any;
  try{ estimate=await client.estimateTransactionFeesForWrite({...draft,account:account as `0x${string}`}); }catch{}
  const fees=feesFromEstimate(estimate);
  const txId=await client.writeContract({...draft,...(fees?{fees}:{})});
  onState?.({phase:"SUBMITTED",txId,message:"Transaction submitted to GenLayer."});
  onState?.({phase:"CONSENSUS_RUNNING",txId,message:"Validators are evaluating this transaction."});
  const decided=await client.waitForTransactionReceipt({hash:txId,waitUntil:"decided",retries:180,interval:4000,fullTransaction:true});
  const tx=await client.getTransaction({hash:txId});
  const name=statusNameOf((tx as any)?.statusName,(tx as any)?.status_name,(tx as any)?.status,(decided as any)?.statusName,(decided as any)?.status_name,(decided as any)?.status);
  if(name.includes("FINALIZED")){
    const state={phase:"FINALIZED" as const,txId,statusName:name,message:"Transaction is finalized. Contract state has crossed the finality boundary.",receipt:decided};
    onState?.(state); return state;
  }
  if(name.includes("READY_TO_FINALIZE")){
    const state={phase:"READY_TO_FINALIZE" as const,txId,statusName:name,message:"Appeal window has closed; transaction is ready to finalize.",receipt:decided};
    onState?.(state); return state;
  }
  if(name.includes("UNDETERMINED")){
    const state={phase:"UNDETERMINED" as const,txId,statusName:name,message:"Consensus is undetermined. No final record or reward has been issued.",receipt:decided};
    onState?.(state); return state;
  }
  if(name.includes("TIMEOUT") || name.includes("REVERT") || name.includes("CANCEL") || name.includes("FAIL")){
    const state={phase:"FAILED" as const,txId,statusName:name,message:"Transaction did not complete successfully. No final consequence has been issued.",receipt:decided};
    onState?.(state); return state;
  }
  const provisional={phase:"PROVISIONAL" as const,txId,statusName:name,message:"A provisional consensus result exists. It is not final.",receipt:decided};
  onState?.(provisional);
  return provisional;
}

export async function inspectTransaction(account:string|undefined,txId:string):Promise<ResearchTxState>{
  const client:any=account?signer(account):reader();
  const tx:any=await client.getTransaction({hash:txId as `0x${string}`});
  const name=statusNameOf(tx?.statusName,tx?.status_name,tx?.status);
  if(name.includes("FINALIZED")) return {phase:"FINALIZED",txId,statusName:name,message:"Finalized. Permanent consequences may now be relied on.",receipt:tx};
  if(name.includes("READY_TO_FINALIZE")) return {phase:"READY_TO_FINALIZE",txId,statusName:name,message:"Appeal window has closed; transaction is ready to finalize.",receipt:tx};
  if(name.includes("UNDETERMINED")) return {phase:"UNDETERMINED",txId,statusName:name,message:"Consensus is undetermined.",receipt:tx};
  if(name.includes("TIMEOUT")||name.includes("CANCEL")||name.includes("FAIL")||name.includes("REVERT")) return {phase:"FAILED",txId,statusName:name,message:"Transaction did not complete successfully.",receipt:tx};
  if(name.includes("ACCEPTED")) return {phase:"PROVISIONAL",txId,statusName:name,message:"Accepted provisionally; not finalized.",receipt:tx};
  return {phase:"CONSENSUS_RUNNING",txId,statusName:name,message:"Consensus lifecycle is still running.",receipt:tx};
}

export async function finalizeResearchTx(account:string,txId:string){
  const client:any=signer(account);
  return client.finalizeTransaction({account:account as `0x${string}`,txId:txId as `0x${string}`});
}

export async function appealResearchTx(account:string,txId:string){
  const client:any=signer(account);
  const can=await client.canAppeal({txId:txId as `0x${string}`});
  if(!can) throw new Error("This transaction is not currently appealable.");
  const bond=await client.getMinAppealBond({txId:txId as `0x${string}`});
  return client.appealTransaction({account:account as `0x${string}`,txId:txId as `0x${string}`,value:bond});
}
