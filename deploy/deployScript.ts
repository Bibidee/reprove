import fs from "fs";
import path from "path";
import { transactionsStatusNumberToName, type GenLayerClient } from "genlayer-js/types";

const ROOT = process.cwd();
const sleep = (ms:number)=>new Promise(r=>setTimeout(r,ms));

async function waitFinal(client:any, txId:`0x${string}`, label:string){
  for(let i=0;i<240;i++){
    const tx:any=await client.getTransaction({hash:txId});
    const raw=tx?.statusName??tx?.status??"";
    const name=String((transactionsStatusNumberToName as Record<string,string>)[String(raw)]||raw).toUpperCase();
    process.stdout.write(`\r${label}: ${name||"PENDING"}        `);
    if(name.includes("FINALIZED")){process.stdout.write("\n");return tx}
    if(name.includes("UNDETERMINED")) throw new Error(`${label} became UNDETERMINED`);
    if(name.includes("REVERT")||name.includes("CANCEL")||name.includes("FAIL")) throw new Error(`${label} failed with ${name}`);
    if(name.includes("READY_TO_FINALIZE")){
      try{await client.finalizeTransaction({txId})}catch{}
    }
    await sleep(5000);
  }
  throw new Error(`${label} did not finalize within the deployment window`);
}

async function deployOne(client:any,file:string,args:any[],label:string){
  const code=new Uint8Array(fs.readFileSync(path.join(ROOT,"contracts",file)));
  const txId=await client.deployContract({code,args}) as `0x${string}`;
  await waitFinal(client,txId,label);
  const tx:any=await client.getTransaction({hash:txId});
  const address=tx?.txDataDecoded?.contractAddress||tx?.data?.contract_address||tx?.contractAddress;
  if(!address) throw new Error(`${label}: finalized but contract address could not be decoded`);
  return {txId,address:String(address)};
}

async function finalizedWrite(client:any,address:string,functionName:string,args:any[],label:string){
  const draft={address:address as `0x${string}`,functionName,args,value:0n};
  let fees:any;
  try{const estimate=await client.estimateTransactionFeesForWrite(draft);fees=estimate?.distribution&&estimate?.feeValue!==undefined?{distribution:estimate.distribution,feeValue:estimate.feeValue}:undefined}catch{}
  const txId=await client.writeContract({...draft,...(fees?{fees}:{})}) as `0x${string}`;
  await waitFinal(client,txId,label);
  return txId;
}

export default async function main(client: GenLayerClient<any>){
  const chainId=Number((client as any)?.chain?.id);
  if(chainId!==61999) throw new Error(`REPROVE deploy aborted: expected Studionet 61999, connected chain is ${chainId||"unknown"}`);
  await (client as any).initializeConsensusSmartContract();
  console.log("REPROVE deployment target: GenLayer Studionet 61999");
  const registry=await deployOne(client,"study_registry.py",[],"StudyRegistry");
  const engine=await deployOne(client,"replication_engine.py",[registry.address,""],"ReplicationEngine");
  const pool=await deployOne(client,"research_pool.py",[registry.address,engine.address],"ResearchPool");
  const configureTx=await finalizedWrite(client,engine.address,"set_pool_once",[pool.address],"Configure Engine → Pool");
  const manifest={
    project:"REPROVE",
    network:"GenLayer Studionet",
    chainId:61999,
    rpc:"https://studio.genlayer.com/api",
    explorer:"https://explorer-studio.genlayer.com",
    deployedAt:new Date().toISOString(),
    contracts:{
      studyRegistry:{address:registry.address,deployTx:registry.txId},
      replicationEngine:{address:engine.address,deployTx:engine.txId,configurePoolTx:configureTx},
      researchPool:{address:pool.address,deployTx:pool.txId}
    }
  };
  fs.mkdirSync(path.join(ROOT,"deployments"),{recursive:true});
  fs.writeFileSync(path.join(ROOT,"deployments","studionet.json"),JSON.stringify(manifest,null,2)+"\n");
  console.log("\nCanonical Studionet deployment:\n"+JSON.stringify(manifest,null,2));
  console.log("\nSet these Vercel variables:");
  console.log(`NEXT_PUBLIC_STUDY_REGISTRY_ADDRESS=${registry.address}`);
  console.log(`NEXT_PUBLIC_REPLICATION_ENGINE_ADDRESS=${engine.address}`);
  console.log(`NEXT_PUBLIC_RESEARCH_POOL_ADDRESS=${pool.address}`);
}
