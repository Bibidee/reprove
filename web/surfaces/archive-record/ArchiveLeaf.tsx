"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {readArchive} from "@/contracts/research-pool";
import {readStudy} from "@/contracts/study-registry";
import {readAttempt} from "@/contracts/replication-engine";
import type {ArchiveRecord} from "@/research/publication/archive-model";
import type {Study} from "@/research/study/study-model";
import type {Attempt} from "@/research/replication/attempt-model";
import {archiveTitle,rewardGen} from "@/research/publication/receipt-projector";
import {ADDRESSES,EXPLORER} from "@/consensus/genlayer-session";

export function ArchiveLeaf({recordKey}:{recordKey:string}){
 const[record,setRecord]=useState<ArchiveRecord|null>(null),[study,setStudy]=useState<Study|null>(null),[attempt,setAttempt]=useState<Attempt|null>(null),[busy,setBusy]=useState(true),[err,setErr]=useState("");
 useEffect(()=>{(async()=>{try{const r=await readArchive(recordKey);setRecord(r);if(r){const[s,a]=await Promise.all([readStudy(r.study_key),readAttempt(r.attempt_key)]);setStudy(s);setAttempt(a)}}catch(e:any){setErr(e?.message||"Could not open archive record")}finally{setBusy(false)}})()},[recordKey]);
 if(busy)return <main className="shell archive"><div className="loading-leaf">Opening finality-gated research record…</div></main>;
 if(!record||!study||!attempt)return <main className="shell archive"><div className="error-leaf">{err||"Archive record not found. A provisional parent assessment is not an archive record."}</div></main>;
 return <main className="shell archive"><div className="archive-head"><Link className="archive-word" href="/">REPROVE ARCHIVE</Link><span className="chain-label">FINALITY-GATED · GENLAYER 61999</span></div><article className="archive-sheet"><div className="archive-accession">{record.record_key}</div><h1>{study.title}</h1><div className="micro">REGISTERED STUDY {study.study_key} · ATTEMPT {attempt.attempt_key}</div><div className="archive-verdict">{archiveTitle(record.verdict)}</div><div className="archive-facts"><Fact label="registered field" value={study.field}/><Fact label="protocol revision" value={`v${study.revision} · frozen before attempt`}/><Fact label="researcher" value={record.researcher}/><Fact label="protocol compliance" value={String(attempt.assessment?.protocol_compliance||"—")}/><Fact label="evidence sufficiency" value={String(attempt.assessment?.evidence_sufficiency||"—")}/><Fact label="outcome criterion" value={String(attempt.assessment?.outcome_satisfied||"—")}/><Fact label="evidence snapshot" value={String(attempt.assessment?.evidence_snapshot_digest||"—")}/><Fact label="assessment digest" value={record.assessment_digest}/><Fact label="recorded after parent finality" value={record.recorded_at}/><Fact label="reward reserved" value={`${rewardGen(record.reward_reserved_wei)} GEN`}/></div><div className="archive-note"><b>Interpretation boundary.</b><br/>This record was created by REPROVE's finalized-parent outcome pipeline and evaluates this replication against the preregistered protocol and registered outcome rule. It does not establish universal scientific truth and it does not merge disagreement across different protocols into one claim.</div><Link className="technical-link" href={`/claim/${encodeURIComponent(study.study_key)}`}>open registered study ↗</Link>{ADDRESSES.pool&&<a className="technical-link" style={{marginLeft:18}} target="_blank" href={`${EXPLORER}/address/${ADDRESSES.pool}`}>verify archive contract ↗</a>}</article></main>
}
function Fact({label,value}:{label:string;value:string}){return <div className="archive-fact"><span>{label}</span><code>{value}</code></div>}
