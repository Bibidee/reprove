"use client";

import Link from "next/link";
import {useEffect,useMemo,useState} from "react";
import {readAttempt,readCapsule,commitCapsule,evaluateAttempt} from "@/contracts/replication-engine";
import {readStudy} from "@/contracts/study-registry";
import {readArchive} from "@/contracts/research-pool";
import type {Attempt,Assessment,EvidenceLeaf,ReportedResult,AuthorityProfile} from "@/research/replication/attempt-model";
import type {Study} from "@/research/study/study-model";
import {EVIDENCE_KINDS,normaliseEvidence} from "@/research/evidence/manifest";
import {ResearcherStamp} from "@/identity/ResearcherStamp";
import {useResearcher} from "@/identity/researcher-session";
import {appealResearchTx,finalizeResearchTx,inspectTransaction,type ResearchTxState} from "@/consensus/write-pipeline";
import {ADDRESSES} from "@/consensus/genlayer-session";

const emptyLeaf:EvidenceLeaf={kind:"DATASET",url:"",note:"",authority_profile:"GENERIC_CONTENT_ADDRESS",sha256:"",artifact_id:"",provenance:{}};
const evaluationStorageKey=(attemptKey:string)=>`reprove:evaluate:${ADDRESSES.engine.toLowerCase()}:${attemptKey}`;
const HEX64=/^[0-9a-fA-F]{64}$/;
const COMMIT=/^[0-9a-fA-F]{40}$/;
const REPOSITORY=/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const GITHUB_PATH=/^[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+)*$/;
const ZENODO_FILENAME=/^[A-Za-z0-9][A-Za-z0-9._-]{0,219}$/;

function stableJson(value:unknown):string {
  if(Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if(value&&typeof value==="object") return `{${Object.keys(value as Record<string,unknown>).sort().map(k=>`${JSON.stringify(k)}:${stableJson((value as Record<string,unknown>)[k])}`).join(",")}}`;
  return JSON.stringify(value);
}

async function sha256(text:string){
  const bytes=new TextEncoder().encode(text);
  const digest=await crypto.subtle.digest("SHA-256",bytes);
  return Array.from(new Uint8Array(digest)).map(x=>x.toString(16).padStart(2,"0")).join("");
}

function integerField(value:string,label:string):number {
  if(!/^-?\d+$/.test(value.trim())) throw new Error(`${label} must be an integer.`);
  const parsed=Number(value);
  if(!Number.isSafeInteger(parsed)) throw new Error(`${label} is outside the supported integer range.`);
  return parsed;
}

function buildProvenance(leaf:EvidenceLeaf):{artifact_id:string;provenance:Record<string,unknown>} {
  const sha=String(leaf.sha256||"").trim().toLowerCase();
  if(!HEX64.test(sha)) throw new Error(`Every ${leaf.kind} artifact needs its exact SHA-256 digest.`);
  const profile=(leaf.authority_profile||"GENERIC_CONTENT_ADDRESS") as AuthorityProfile;
  const provenance=leaf.provenance||{};
  if(profile==="GENERIC_CONTENT_ADDRESS") return {artifact_id:`sha256:${sha}`,provenance:{}};
  if(profile==="GITHUB_COMMIT"){
    const repository=String(provenance.repository||"").trim().toLowerCase();
    const commit=String(provenance.commit||"").trim().toLowerCase();
    const path=String(provenance.path||"").trim();
    if(!REPOSITORY.test(repository)||!COMMIT.test(commit)||!GITHUB_PATH.test(path)) throw new Error("GitHub provenance needs an owner/repository, full 40-character commit SHA, and artifact path.");
    const url=`https://raw.githubusercontent.com/${repository}/${commit}/${path}`;
    if(leaf.url.trim()!==url) throw new Error("GitHub URL must exactly match the canonical immutable raw URL for the declared artifact.");
    return {artifact_id:`github:${repository}@${commit}:${path}`,provenance:{repository,commit,path}};
  }
  const recordId=String(provenance.record_id||"").trim();
  const filename=String(provenance.filename||"").trim();
  if(!/^\d+$/.test(recordId)||!ZENODO_FILENAME.test(filename)) throw new Error("Zenodo provenance needs a numeric record ID and a safe filename.");
  const url=`https://zenodo.org/records/${recordId}/files/${filename}`;
  if(leaf.url.trim()!==url) throw new Error("Zenodo URL must exactly match https://zenodo.org/records/{id}/files/{filename}.");
  return {artifact_id:`zenodo:${recordId}:${filename}`,provenance:{record_id:recordId,filename}};
}

type ReportedDraft={
  mean_num:string; mean_den:string; difference_num:string; difference_den:string; threshold_met:""|"true"|"false";
  sample_size:string; observed_effect:string; analysis_statement:string; notes:string;
};

const emptyResult:ReportedDraft={mean_num:"",mean_den:"",difference_num:"",difference_den:"",threshold_met:"",sample_size:"",observed_effect:"",analysis_statement:"",notes:""};

function resultFromCapsule(value:Record<string,unknown>):ReportedDraft {
  return {
    mean_num:value.mean_num==null?"":String(value.mean_num), mean_den:value.mean_den==null?"":String(value.mean_den),
    difference_num:value.difference_num==null?"":String(value.difference_num), difference_den:value.difference_den==null?"":String(value.difference_den),
    threshold_met:value.threshold_met===true?"true":value.threshold_met===false?"false":"",
    sample_size:value.sample_size==null?"":String(value.sample_size), observed_effect:value.observed_effect==null?"":String(value.observed_effect),
    analysis_statement:value.analysis_statement==null?"":String(value.analysis_statement), notes:value.notes==null?"":String(value.notes),
  };
}

function buildReportedResult(profile:string,draft:ReportedDraft):ReportedResult {
  if(draft.threshold_met!=="true"&&draft.threshold_met!=="false") throw new Error("Select whether the frozen threshold was met.");
  const commentary={sample_size:draft.sample_size.trim(),observed_effect:draft.observed_effect.trim(),analysis_statement:draft.analysis_statement.trim(),notes:draft.notes.trim()};
  const threshold_met=draft.threshold_met==="true";
  if(profile==="ONE_SAMPLE_THRESHOLD") return {...commentary,mean_num:integerField(draft.mean_num,"mean numerator"),mean_den:integerField(draft.mean_den,"mean denominator"),threshold_met};
  if(profile==="TWO_GROUP_MEAN_DIFF"||profile==="BINARY_RATE_DIFF") return {...commentary,difference_num:integerField(draft.difference_num,"difference numerator"),difference_den:integerField(draft.difference_den,"difference denominator"),threshold_met};
  throw new Error("The registered analysis profile is unsupported.");
}

export function ReplicationNotebook({attemptKey}:{attemptKey:string}){
  const w=useResearcher();
  const [attempt,setAttempt]=useState<Attempt|null>(null),[study,setStudy]=useState<Study|null>(null),[busy,setBusy]=useState(true),[err,setErr]=useState(""),[leaves,setLeaves]=useState<EvidenceLeaf[]>([{...emptyLeaf},{...emptyLeaf,kind:"METHOD"}]),[result,setResult]=useState<ReportedDraft>(emptyResult),[tx,setTx]=useState<ResearchTxState|null>(null),[archive,setArchive]=useState<any>(null);
  const recordKey=attempt?`${attempt.study_key}:${attempt.attempt_key}`:"";
  const load=async()=>{setBusy(true);setErr("");try{const a=await readAttempt(attemptKey);setAttempt(a);if(a){const[s,r,c]=await Promise.all([readStudy(a.study_key),readArchive(`${a.study_key}:${a.attempt_key}`),readCapsule(a.attempt_key)]);setStudy(s);setArchive(r);if(a.evidence_manifest?.length)setLeaves(a.evidence_manifest);if(c?.artifacts&&Array.isArray(c.artifacts))setLeaves(c.artifacts as EvidenceLeaf[]);if(c?.reported_result)setResult(resultFromCapsule(c.reported_result as Record<string,unknown>));}}catch(e:any){setErr(e?.message||"Could not open notebook")}finally{setBusy(false)}};
  useEffect(()=>{load();if(typeof window!=="undefined"){const saved=localStorage.getItem(evaluationStorageKey(attemptKey));if(saved)inspectTransaction(undefined,saved).then(setTx).catch(()=>{})}},[attemptKey]);
  const compliance=useMemo(()=>study?[['Population',study.protocol.population],['Procedure',study.protocol.procedure],['Measurement',study.protocol.measurement],['Analysis',study.protocol.analysis],['Window',study.protocol.window]]:[],[study]);
  const profile=study?.analysis_spec?.profile||"UNSUPPORTED";
  const addLeaf=()=>setLeaves(x=>x.length>=8?x:[...x,{...emptyLeaf,kind:"SUPPLEMENT",provenance:{}}]);
  const patchLeaf=(i:number,p:Partial<EvidenceLeaf>)=>setLeaves(x=>x.map((v,n)=>n===i?{...v,...p}:v));
  const patchProvenance=(i:number,key:string,value:string)=>setLeaves(x=>x.map((v,n)=>n===i?{...v,provenance:{...(v.provenance||{}),[key]:value},artifact_id:""}:v));
  const removeLeaf=(i:number)=>setLeaves(x=>x.filter((_,n)=>n!==i));
  const submit=async()=>{
    setErr("");
    if(!attempt||!study||!w.address)return setErr("Connect the researcher wallet that owns this attempt.");
    if(attempt.researcher.toLowerCase()!==w.address.toLowerCase())return setErr("Only the registered attempt researcher may submit this notebook.");
    if(!w.chainOk)return setErr("Switch to Studionet 61999.");
    try{
      if(attempt.state==="CAPSULE_COMMITTED"){const r=await evaluateAttempt(w.address,attemptKey,setTx);if(r.txId)localStorage.setItem(evaluationStorageKey(attemptKey),r.txId);await load();return;}
      const clean=normaliseEvidence(leaves);
      if(clean.length<2)return setErr("Provide at least two unique HTTPS evidence sources.");
      const enriched=clean.map(x=>{const built=buildProvenance(x);return {...x,authority_profile:x.authority_profile||"GENERIC_CONTENT_ADDRESS",...built,sha256:String(x.sha256).trim().toLowerCase(),media_type:x.media_type||"text/plain"};});
      const reported_result=buildReportedResult(profile,result);
      const capsule={capsule_version:2,study_key:attempt.study_key,attempt_key:attempt.attempt_key,study_digest:study.study_digest,analysis_spec_digest:await sha256(stableJson(study.analysis_spec||{})),reported_result,artifacts:enriched};
      const capsuleTx=await commitCapsule(w.address,attemptKey,capsule,setTx);
      if(capsuleTx.phase!=="FINALIZED"){setErr("Capsule submitted. Finalize the capsule transaction, then press evaluate again.");return;}
      const r=await evaluateAttempt(w.address,attemptKey,setTx);if(r.txId)localStorage.setItem(evaluationStorageKey(attemptKey),r.txId);await load();
    }catch(e:any){setErr(e?.message||"Capsule validation or evaluation failed")}
  };
  const check=async()=>{const id=tx?.txId||(typeof window!=="undefined"?localStorage.getItem(evaluationStorageKey(attemptKey)):null);if(!id)return setErr("No cached evaluation transaction id is available.");try{const s=await inspectTransaction(w.address||undefined,id);setTx(s);await load()}catch(e:any){setErr(e?.message||"Could not inspect transaction")}};
  const finalize=async()=>{if(!w.address||!tx?.txId)return;try{await finalizeResearchTx(w.address,tx.txId);setTimeout(check,1200)}catch(e:any){setErr(e?.message||"Finalization failed")}};
  const appeal=async()=>{if(!w.address||!tx?.txId)return;try{await appealResearchTx(w.address,tx.txId);setTimeout(check,1200)}catch(e:any){setErr(e?.message||"Appeal failed")}};
  if(busy)return <div className="shell"><div className="loading-leaf">Opening replication notebook…</div></div>;
  if(!attempt||!study)return <div className="shell"><div className="error-leaf">{err||"Attempt not found."}</div></div>;
  const assessed=attempt.state==="ASSESSED"&&attempt.assessment?.verdict;const assessment=attempt.assessment as Partial<Assessment>;
  return <main className="shell notebook"><div className="notebook-nav"><Link className="paper-back" href={`/claim/${encodeURIComponent(attempt.study_key)}`}>← registered study</Link><ResearcherStamp/></div><div className="notebook-title"><div><div className="journal-kicker">replication notebook · {attempt.attempt_key}</div><h1>{study.title}</h1></div><div className="attempt-meta">researcher {attempt.researcher.slice(0,8)}…{attempt.researcher.slice(-4)}<br/>opened {attempt.created_at}<br/>expires {attempt.expires_at||"study policy"}</div></div><div className="notebook-tabs"><span className="done">protocol</span><span className={assessed?"done":"active"}>capsule</span><span className={assessed?"done":"active"}>evidence</span><span className={assessed?"active":""}>result</span></div><div className="notebook-spread"><section className="notebook-left"><div className="section-number">REGISTERED METHOD</div><h2>Protocol compliance desk</h2>{compliance.map(([k,v])=><div className="compliance-item" key={k}><i>§</i><div><b>{k}</b><div>{String(v)}</div></div></div>)}<div className="outcome-law"><div className="section-number">OUTCOME RULE</div><p>{study.outcome_rule}</p></div><div className="outcome-law"><div className="section-number">RESEARCHER STATEMENT</div><p>{attempt.replication_statement}</p></div><div className="outcome-law"><div className="section-number">FROZEN ANALYSIS</div><p>{profile} · threshold {study.analysis_spec?.threshold_scaled??"—"} · immutable artifacts required</p></div></section><section className="notebook-right"><div className="section-number">IMMUTABLE EVIDENCE CAPSULE</div><h2>Evidence leaves</h2>{leaves.map((leaf,i)=><div className="evidence-leaf" key={i}><div className="kind">{leaf.kind}</div><div>{assessed?<><a href={leaf.url||undefined} target="_blank" rel="noreferrer">{leaf.url||"source not entered"}</a><p>{leaf.note||"No evidence note."}</p><code>{leaf.artifact_id||leaf.sha256||"no capsule identity"}</code></>:<><div className="two-fields"><div className="field-block"><label>kind</label><select value={leaf.kind} onChange={e=>patchLeaf(i,{kind:e.target.value as EvidenceLeaf["kind"]})}>{EVIDENCE_KINDS.map(k=><option key={k}>{k}</option>)}</select></div><div className="field-block"><label>public HTTPS source</label><input value={leaf.url} onChange={e=>patchLeaf(i,{url:e.target.value})} placeholder="https://…"/></div></div><div className="two-fields"><div className="field-block"><label>authority profile</label><select value={leaf.authority_profile||"GENERIC_CONTENT_ADDRESS"} onChange={e=>patchLeaf(i,{authority_profile:e.target.value as AuthorityProfile,artifact_id:"",provenance:{}})}><option>GENERIC_CONTENT_ADDRESS</option><option>GITHUB_COMMIT</option><option>ZENODO_RECORD</option></select></div><div className="field-block"><label>exact artifact SHA-256</label><input value={leaf.sha256||""} onChange={e=>patchLeaf(i,{sha256:e.target.value})} placeholder="64 hexadecimal characters"/></div></div>{leaf.authority_profile==="GITHUB_COMMIT"&&<div className="three-fields"><div className="field-block"><label>repository</label><input value={String(leaf.provenance?.repository||"")} onChange={e=>patchProvenance(i,"repository",e.target.value)} placeholder="owner/repository"/></div><div className="field-block"><label>full commit SHA</label><input value={String(leaf.provenance?.commit||"")} onChange={e=>patchProvenance(i,"commit",e.target.value)} placeholder="40 hex characters"/></div><div className="field-block"><label>artifact path</label><input value={String(leaf.provenance?.path||"")} onChange={e=>patchProvenance(i,"path",e.target.value)} placeholder="data.json"/></div></div>}{leaf.authority_profile==="ZENODO_RECORD"&&<div className="two-fields"><div className="field-block"><label>record ID</label><input value={String(leaf.provenance?.record_id||"")} onChange={e=>patchProvenance(i,"record_id",e.target.value)} placeholder="12345"/></div><div className="field-block"><label>filename</label><input value={String(leaf.provenance?.filename||"")} onChange={e=>patchProvenance(i,"filename",e.target.value)} placeholder="data.json"/></div></div>}<div className="field-block"><label>what this source proves</label><textarea value={leaf.note} onChange={e=>patchLeaf(i,{note:e.target.value})} placeholder="Describe the role of this evidence in the replication."/></div></>}</div>{!assessed&&<button className="leaf-remove" onClick={()=>removeLeaf(i)}>remove</button>}</div>)}{!assessed&&<div className="evidence-compose"><button className="outline-action" onClick={addLeaf} disabled={leaves.length>=8}>add evidence leaf</button></div>}{!assessed&&<div className="result-compose"><div className="section-number">REPLICATION RESULT</div><h2>Report the recomputed result</h2><p className="micro">The canonical verdict is recomputed from the dataset. These deterministic fields are compared with your report for transparency; they never choose the verdict.</p>{profile==="ONE_SAMPLE_THRESHOLD"?<div className="two-fields"><div className="field-block"><label>mean numerator</label><input value={result.mean_num} onChange={e=>setResult(x=>({...x,mean_num:e.target.value}))} placeholder="8792"/></div><div className="field-block"><label>mean denominator</label><input value={result.mean_den} onChange={e=>setResult(x=>({...x,mean_den:e.target.value}))} placeholder="10"/></div></div>:<div className="two-fields"><div className="field-block"><label>difference numerator</label><input value={result.difference_num} onChange={e=>setResult(x=>({...x,difference_num:e.target.value}))} placeholder="4000"/></div><div className="field-block"><label>difference denominator</label><input value={result.difference_den} onChange={e=>setResult(x=>({...x,difference_den:e.target.value}))} placeholder="4"/></div></div>}<div className="two-fields"><div className="field-block"><label>threshold met</label><select value={result.threshold_met} onChange={e=>setResult(x=>({...x,threshold_met:e.target.value as ReportedDraft["threshold_met"]}))}><option value="">choose one</option><option value="true">yes</option><option value="false">no</option></select></div><div className="field-block"><label>sample size · optional commentary</label><input value={result.sample_size} onChange={e=>setResult(x=>({...x,sample_size:e.target.value}))} placeholder="10"/></div></div><div className="field-block"><label>observed effect · optional commentary</label><input value={result.observed_effect} onChange={e=>setResult(x=>({...x,observed_effect:e.target.value}))} placeholder="0.8792"/></div><div className="field-block"><label>analysis statement · optional commentary</label><textarea value={result.analysis_statement} onChange={e=>setResult(x=>({...x,analysis_statement:e.target.value}))} placeholder="State what the registered analysis produced."/></div><div className="field-block"><label>notes · optional commentary</label><textarea value={result.notes} onChange={e=>setResult(x=>({...x,notes:e.target.value}))} placeholder="Optional context, deviations or limitations."/></div><button className="ink-action" onClick={submit}>commit capsule + evaluate</button></div>}</section></div>{assessed&&<section className="assessment-leaf"><div className="provisional-label">{archive?"FINALITY-GATED ARCHIVE RECORD":"CONSENSUS ASSESSMENT · CHECK FINALITY"}</div><h2>{assessment.verdict?.replaceAll("_"," ")}</h2><p>{assessment.summary||"Bounded reason codes and deterministic results are the authoritative assessment record."}</p><div className="assessment-grid"><div><span>protocol</span><b>{assessment.protocol_compliance}</b></div><div><span>evidence</span><b>{assessment.evidence_sufficiency}</b></div><div><span>threshold</span><b>{assessment.threshold_outcome}</b></div><div><span>provenance</span><b>{assessment.provenance_status}</b></div><div><span>integrity</span><b>{assessment.artifact_integrity_status}</b></div><div><span>recomputed profile</span><b>{assessment.statistical_profile}</b></div></div>{assessment.reason_codes&&<div className="micro">reason codes: {assessment.reason_codes.join(" · ")}</div>}{archive?<div className="finality-actions"><Link className="ink-action" href={`/archive/${encodeURIComponent(recordKey)}`}>open archive record</Link></div>:<><p className="micro">The archive record is shown only after parent finality and finalized-only ResearchPool child registration.</p>{tx&&<Tx state={tx}/>}<div className="finality-actions"><button className="outline-action" onClick={check}>check finality + archive</button>{tx?.phase==="READY_TO_FINALIZE"&&<button className="ink-action" onClick={finalize}>finalize transaction</button>}{tx?.phase==="PROVISIONAL"&&<button className="outline-action" onClick={appeal}>appeal assessment</button>}</div></>}</section>}{tx&&!assessed&&<Tx state={tx}/>} {err&&<div className="error-leaf">{err}</div>}</main>;
}

function Tx({state}:{state:ResearchTxState}){return <div className="tx-trace"><strong>{state.phase.replaceAll("_"," ")}</strong><p>{state.message}</p>{state.txId&&<code>{state.txId}</code>}</div>}
