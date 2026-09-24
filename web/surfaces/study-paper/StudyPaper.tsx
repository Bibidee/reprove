"use client";

import Link from "next/link";

import {useEffect,useState} from "react";

import {useRouter} from "next/navigation";

import {readStudy,closeStudy} from "@/contracts/study-registry";

import {readStudyAttempts,beginAttempt} from "@/contracts/replication-engine";

import {readPool,readClaimable,fundStudy,withdraw,reclaimClosedPool} from "@/contracts/research-pool";

import type {Study} from "@/research/study/study-model";

import type {Attempt} from "@/research/replication/attempt-model";

import {ResearcherStamp} from "@/identity/ResearcherStamp";

import {useResearcher} from "@/identity/researcher-session";

import type {ResearchTxState} from "@/consensus/write-pipeline";

import {inspectTransaction,finalizeResearchTx} from "@/consensus/write-pipeline";

import {rewardGen} from "@/research/publication/receipt-projector";

import {parseGen} from "@/research/money";


export function StudyPaper({studyKey}:{studyKey:string}){
 const router=useRouter(),w=useResearcher();
const[study,setStudy]=useState<Study|null>(null),[attempts,setAttempts]=useState<Attempt[]>([]),[pool,setPool]=useState<any>(null),[claimable,setClaimable]=useState("0"),[busy,setBusy]=useState(true),[err,setErr]=useState("");
const[showBegin,setShowBegin]=useState(false),[attemptKey,setAttemptKey]=useState(""),[statement,setStatement]=useState(""),[tx,setTx]=useState<ResearchTxState|null>(null),[fund,setFund]=useState(""),[fundTx,setFundTx]=useState<ResearchTxState|null>(null),[withdrawAmount,setWithdrawAmount]=useState(""),[withdrawTx,setWithdrawTx]=useState<ResearchTxState|null>(null),[closeTx,setCloseTx]=useState<ResearchTxState|null>(null),[reclaimTx,setReclaimTx]=useState<ResearchTxState|null>(null);

 const load=async()=>{setBusy(true);
try{const[s,a,p,c]=await Promise.all([readStudy(studyKey),readStudyAttempts(studyKey),readPool(studyKey),w.address?readClaimable(w.address):Promise.resolve("0")]);
setStudy(s);
setAttempts(a);
setPool(p);
setClaimable(c)}catch(e:any){setErr(e?.message||"Could not load study")}finally{setBusy(false)}};
useEffect(()=>{load()},[studyKey,w.address]);

 const start=async()=>{setErr("");
if(!w.address)return setErr("Connect a researcher identity first.");
if(!w.chainOk)return setErr("Switch to Studionet 61999.");
try{const r=await beginAttempt(w.address,studyKey,attemptKey,statement,setTx);
if(r.txId)localStorage.setItem(`reprove:begin:${attemptKey}`,r.txId);
if(r.phase!=="FAILED"&&r.phase!=="UNDETERMINED")setTx(r)}catch(e:any){setErr(e?.message||"Could not begin replication")}};

 const check=async()=>{if(!tx?.txId)return;
const s=await inspectTransaction(w.address||undefined,tx.txId);
setTx(s);
if(s.phase==="FINALIZED"){await load();
router.push(`/attempt/${encodeURIComponent(attemptKey)}`)}};

 const finalize=async()=>{if(!w.address||!tx?.txId)return;
await finalizeResearchTx(w.address,tx.txId);
setTimeout(check,1200)};

 const doFund=async()=>{if(!w.address)return setErr("Connect a researcher identity first.");
if(Number(fund)<=0)return setErr("Enter a positive GEN amount.");
try{await fundStudy(w.address,studyKey,fund,setFundTx)}catch(e:any){setErr(e?.message||"Funding failed")}};

 const checkFund=async()=>{if(!fundTx?.txId)return;
try{const s=await inspectTransaction(w.address||undefined,fundTx.txId);
setFundTx(s);
if(s.phase==="FINALIZED")await load()}catch(e:any){setErr(e?.message||"Could not inspect funding finality")}};

 const finalizeFund=async()=>{if(!w.address||!fundTx?.txId)return;
try{await finalizeResearchTx(w.address,fundTx.txId);
setTimeout(checkFund,1200)}catch(e:any){setErr(e?.message||"Funding finalization failed")}};

 const doWithdraw=async()=>{if(!w.address)return setErr("Connect the researcher wallet first.");
try{const amount=parseGen(withdrawAmount);
if(amount<=0n)return setErr("Enter a positive GEN amount.");
await withdraw(w.address,amount.toString(),setWithdrawTx)}catch(e:any){setErr(e?.message||"Withdrawal failed")}};

 const checkWithdraw=async()=>{if(!withdrawTx?.txId)return;
try{const s=await inspectTransaction(w.address||undefined,withdrawTx.txId);
setWithdrawTx(s);
if(s.phase==="FINALIZED")await load()}catch(e:any){setErr(e?.message||"Could not inspect withdrawal finality")}};

 const doClose=async()=>{if(!w.address||w.address.toLowerCase()!==study?.creator.toLowerCase())return setErr("Only the study creator may close this study.");
try{await closeStudy(w.address,studyKey,setCloseTx)}catch(e:any){setErr(e?.message||"Close transaction failed")}};

 const checkClose=async()=>{if(!closeTx?.txId)return;
const s=await inspectTransaction(w.address||undefined,closeTx.txId);
setCloseTx(s);
if(s.phase==="FINALIZED")await load()};

 const doReclaim=async()=>{if(!w.address)return;
try{await reclaimClosedPool(w.address,studyKey,setReclaimTx)}catch(e:any){setErr(e?.message||"Pool reclaim failed")}};

 const checkReclaim=async()=>{if(!reclaimTx?.txId)return;
const s=await inspectTransaction(w.address||undefined,reclaimTx.txId);
setReclaimTx(s);
if(s.phase==="FINALIZED")await load()};

 if(busy)return <div className="shell">
<div className="loading-leaf">Opening registered protocol…</div>
</div>;
if(!study)return <div className="shell">
<div className="error-leaf">{err||"Study not found."}</div>
</div>;

 const protocolEntries=Object.entries(study.protocol).filter(([k])=>["population","procedure","measurement","analysis","window"].includes(k));

 return <main className="shell paper">
<div className="paper-nav">
<Link className="paper-back" href="/lab">← replication atlas</Link>
<ResearcherStamp/>
</div>
<section className="study-banner">
<div className="accession">REGISTERED STUDY · {study.study_key}</div>
<h1>{study.title}</h1>
<div className="study-meta">
<span>{study.field}</span>
<span>protocol v{study.revision}</span>
<span>{study.status}</span>
<span>{study.registered_at}</span>
</div>
</section>
<div className="paper-body">
<article>
<div className="section-number">01 / CLAIM</div>
<p className="claim-block">{study.claim}</p>
<div className="section-number">02 / REGISTERED PROTOCOL</div>
<div className="protocol-sheet">{protocolEntries.map(([k,v])=>
<div className="protocol-cell" key={k}>
<span>{k}</span>
<p>{String(v)}</p>
</div>)}</div>
<div className="outcome-law">
<div className="section-number">03 / OUTCOME LAW</div>
<h2>What counts as a replication result?</h2>
<p>{study.outcome_rule}</p>
</div>
<section className="matrix">
<div className="section-number">04 / REPLICATION MATRIX</div>
<h2>Attempts against the same frozen protocol</h2>{attempts.length===0?<div className="empty-leaf">No replication attempts have been registered yet.</div>:<table>
<thead>
<tr>
<th>attempt</th>
<th>researcher</th>
<th>state</th>
<th>protocol</th>
<th>outcome</th>
<th>finding</th>
</tr>
</thead>
<tbody>{attempts.map(a=>
<tr key={a.attempt_key}>
<td>
<Link href={`/attempt/${encodeURIComponent(a.attempt_key)}`}>{a.attempt_key}</Link>
</td>
<td>{a.researcher.slice(0,8)}…</td>
<td>{a.state}</td>
<td>{a.assessment?.protocol_compliance||"—"}</td>
<td>{a.assessment?.outcome_satisfied||"—"}</td>
<td>{a.assessment?.verdict||"—"}</td>
</tr>)}</tbody>
</table>}</section>
</article>
<aside className="paper-side">
<div className="frozen-stamp">
<div className="section-number">PREREGISTRATION</div>
<b>FROZEN · v{study.revision}</b>
<p>The claim, protocol, evidence policy and outcome rule are immutable after registration.</p>
</div>
<div className="outcome-law">
<div className="section-number">EVIDENCE STANDARD</div>
<p>
<b>Required kinds</b>
<br/>{study.evidence_policy.required_kinds.join(" · ")}</p>
<p>
<b>Minimum origins</b>
<br/>{study.evidence_policy.min_distinct_origins||1}</p>{(study.evidence_policy.allowed_origins||[]).length>0&&<p>
<b>Allowed origins</b>
<br/>{study.evidence_policy.allowed_origins?.join(" · ")}</p>}{(study.evidence_policy.required_origins||[]).length>0&&<p>
<b>Required origins</b>
<br/>{study.evidence_policy.required_origins?.join(" · ")}</p>}</div>
<div className="attempt-index">
<h2>Replication record</h2>{attempts.map(a=>
<Link key={a.attempt_key} className="attempt-line" href={`/attempt/${encodeURIComponent(a.attempt_key)}`}>
<span>
<b>{a.attempt_key}</b>
<small>{a.created_at}</small>
</span>
<span className={`attempt-verdict ${a.assessment?.verdict||""}`}>{a.assessment?.verdict||a.state}</span>
</Link>)}</div>
<div style={{marginTop:28}}>
<button className="ink-action" disabled={study.status!=="OPEN"} onClick={()=>setShowBegin(v=>!v)}>begin replication</button>
</div>{showBegin&&<div className="evidence-compose">
<div className="field-block">
<label>attempt key</label>
<input value={attemptKey} onChange={e=>setAttemptKey(e.target.value.replace(/[^A-Za-z0-9_-]/g,""))} placeholder="rep-03"/>
</div>
<div className="field-block">
<label>replication statement</label>
<textarea value={statement} onChange={e=>setStatement(e.target.value)} placeholder="Describe what this replication is attempting and who conducted it."/>
</div>
<button className="outline-action" disabled={attemptKey.length<3||statement.length<10} onClick={start}>register notebook</button>{tx&&<>
<Tx state={tx}/>
<div className="finality-actions">
<button className="outline-action" onClick={check}>check finality</button>{tx.phase==="READY_TO_FINALIZE"&&<button className="ink-action" onClick={finalize}>finalize</button>}{tx.phase==="FINALIZED"&&<Link className="ink-action" href={`/attempt/${encodeURIComponent(attemptKey)}`}>open notebook</Link>}</div>
</>}</div>}<div className="outcome-law">
<div className="section-number">REPLICATION FUND</div>
<h2>{rewardGen(pool?.available_wei||0)} GEN available</h2>
<p>Fixed reward: {rewardGen(study.reward_per_attempt_wei)} GEN for a valid REPLICATED or FAILED TO REPLICATE record. {pool?.rewarded_attempts||0}/{study.max_rewarded_attempts} reward slots used.</p>
<div className="field-block">
<label>add GEN</label>
<input type="number" min="0" value={fund} onChange={e=>setFund(e.target.value)} placeholder="30"/>
</div>{w.address?.toLowerCase()===study.creator.toLowerCase()?<>
<button className="outline-action" onClick={doFund} disabled={study.status!=="OPEN"}>fund study</button>{fundTx&&<>
<Tx state={fundTx}/>
<div className="finality-actions">
<button className="outline-action" onClick={checkFund}>check funding finality</button>{fundTx.phase==="READY_TO_FINALIZE"&&<button className="ink-action" onClick={finalizeFund}>finalize funding</button>}</div>
</>}</>:<p className="micro">The replication fund is creator-funded so unused accounting cannot be redirected by an unrelated sponsor.</p>}</div>
<div className="outcome-law">
<div className="section-number">RESEARCHER SETTLEMENT</div>
<h2>{rewardGen(claimable)} GEN claimable</h2>
<p>Finalized valid outcomes reserve the frozen reward for the recorded researcher. Withdrawals are pull-based and require the researcher wallet.</p><>
<div className="field-block">
<label>withdraw GEN</label>
<input type="number" min="0" step="0.0001" value={withdrawAmount} onChange={e=>setWithdrawAmount(e.target.value)} placeholder={rewardGen(claimable)}/>
</div>
<button className="outline-action" onClick={doWithdraw}>withdraw reward</button>
</>{withdrawTx&&<>
<Tx state={withdrawTx}/>
<div className="finality-actions">
<button className="outline-action" onClick={checkWithdraw}>check withdrawal finality</button>{withdrawTx.phase==="READY_TO_FINALIZE"&&<button className="ink-action" onClick={async()=>{if(w.address&&withdrawTx.txId){await finalizeResearchTx(w.address,withdrawTx.txId);
setTimeout(checkWithdraw,1200)}}}>finalize withdrawal</button>}</div>
</>}</div>{w.address?.toLowerCase()===study.creator.toLowerCase()&&<div className="outcome-law">
<div className="section-number">STUDY LIFECYCLE</div>{study.status==="OPEN"?<>
<p>Closing prevents new attempts. The frozen study content remains permanent.</p>
<button className="outline-action" onClick={doClose}>close study</button>{closeTx&&<>
<Tx state={closeTx}/>
<div className="finality-actions">
<button className="outline-action" onClick={checkClose}>check close finality</button>{closeTx.phase==="READY_TO_FINALIZE"&&<button className="ink-action" onClick={async()=>{if(w.address&&closeTx.txId){await finalizeResearchTx(w.address,closeTx.txId);
setTimeout(checkClose,1200)}}}>finalize close</button>}</div>
</>}</>:<>
<p>Remaining pool GEN can be reclaimed only after every registered attempt is assessed and has a ResearchPool record. Production release evidence must separately verify those deterministic pool transactions finalized.</p>
<button className="outline-action" onClick={doReclaim}>reclaim settled remainder</button>{reclaimTx&&<>
<Tx state={reclaimTx}/>
<div className="finality-actions">
<button className="outline-action" onClick={checkReclaim}>check reclaim finality</button>{reclaimTx.phase==="READY_TO_FINALIZE"&&<button className="ink-action" onClick={async()=>{if(w.address&&reclaimTx.txId){await finalizeResearchTx(w.address,reclaimTx.txId);
setTimeout(checkReclaim,1200)}}}>finalize reclaim</button>}</div>
</>}</>}</div>}{err&&<div className="error-leaf">{err}</div>}</aside>
</div>
</main>
}
function Tx({state}:{state:ResearchTxState}){return <div className="tx-trace">
<strong>{state.phase.replaceAll("_"," ")}</strong>
<p>{state.message}</p>{state.txId&&<code>{state.txId}</code>}</div>}
