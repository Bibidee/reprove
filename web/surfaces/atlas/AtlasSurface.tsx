"use client";
import Link from "next/link";
import {useEffect,useMemo,useState} from "react";
import {readStudies} from "@/contracts/study-registry";
import type {Study} from "@/research/study/study-model";
import {ResearcherStamp} from "@/identity/ResearcherStamp";
import {RegisterStudy} from "@/surfaces/registration/RegisterStudy";
import {configured} from "@/consensus/genlayer-session";

export function AtlasSurface(){
 const[studies,setStudies]=useState<Study[]>([]),[busy,setBusy]=useState(true),[q,setQ]=useState(""),[register,setRegister]=useState(false),[err,setErr]=useState("");
 const load=async()=>{setBusy(true);setErr("");try{const r=await readStudies();setStudies(r.items)}catch(e:any){setErr(e?.message||"Could not read the study registry")}finally{setBusy(false)}};
 useEffect(()=>{load()},[]);
 const shown=useMemo(()=>studies.filter(s=>`${s.title} ${s.claim} ${s.field} ${s.study_key}`.toLowerCase().includes(q.toLowerCase())),[studies,q]);
 if(register)return <div className="shell"><div className="research-ribbon"><Link className="mark" href="/"><span className="mark-orbit"/>REPROVE</Link><ResearcherStamp/></div><RegisterStudy onExit={()=>setRegister(false)} onCreated={()=>{setRegister(false);load()}}/></div>;
 return <main className="shell"><div className="research-ribbon"><Link className="mark" href="/"><span className="mark-orbit"/>REPROVE</Link><div className="ribbon-right"><span className="chain-label">Studionet · 61999</span><ResearcherStamp/></div></div><section className="atlas"><div className="atlas-intro"><div><div className="journal-kicker">replication atlas</div><h1>Registered studies</h1><p>Claims are frozen before replication results are known. Each study keeps its protocol, evidence standard, attempts and archive record together.</p></div><div className="atlas-tools"><input className="atlas-search" value={q} onChange={e=>setQ(e.target.value)} placeholder="search claim, field, key…"/><button className="ink-action" onClick={()=>setRegister(true)}>register a claim +</button></div></div>{!configured()&&<div className="config-leaf"><b>Deployment addresses are not configured.</b> The interface is complete, but live registry reads and writes begin after the three Studionet addresses are placed in the Vercel environment.</div>}{err&&<div className="error-leaf">{err}</div>}<div className="atlas-table"><div className="atlas-row header"><span>field</span><span>claim</span><span>state</span><span>revision</span></div>{busy?<div className="empty-leaf">Reading the registered study index…</div>:shown.length===0?<div className="empty-leaf">No registered studies match this view.</div>:shown.map(s=><Link key={s.study_key} href={`/claim/${encodeURIComponent(s.study_key)}`} className="atlas-row"><span className="field-label">{s.field}</span><span className="atlas-title">{s.title}<small>{s.claim}</small></span><span className={`state-glyph ${s.status.toLowerCase()}`}>{s.status}</span><span className="micro">v{s.revision}</span></Link>)}</div></section></main>
}
