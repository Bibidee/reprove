"use client";
import React,{createContext,useContext,useEffect,useMemo,useState} from "react";
import { CHAIN_ID, RPC, EXPLORER } from "@/consensus/genlayer-session";

type Provider={request:(x:{method:string;params?:any[]})=>Promise<any>;on?:(e:string,h:(...x:any[])=>void)=>void;removeListener?:(e:string,h:(...x:any[])=>void)=>void};
declare global{interface Window{ethereum?:Provider}}

type Context={address:string|null;chainOk:boolean;busy:boolean;connect:()=>Promise<void>;disconnect:()=>Promise<void>;switchNetwork:()=>Promise<void>};
const C=createContext<Context|null>(null);
const HEX=`0x${CHAIN_ID.toString(16)}`;

export function ResearcherSession({children}:{children:React.ReactNode}){
 const [address,setAddress]=useState<string|null>(null),[chainOk,setChainOk]=useState(false),[busy,setBusy]=useState(false);
 const refresh=async()=>{const p=window.ethereum;if(!p){setAddress(null);setChainOk(false);return} const a=await p.request({method:"eth_accounts"}); const c=await p.request({method:"eth_chainId"}); setAddress(a?.[0]||null);setChainOk(parseInt(c,16)===CHAIN_ID)};
 useEffect(()=>{refresh();const p=window.ethereum;if(!p?.on)return;const h=()=>refresh();p.on("accountsChanged",h);p.on("chainChanged",h);return()=>{p.removeListener?.("accountsChanged",h);p.removeListener?.("chainChanged",h)}},[]);
 const switchNetwork=async()=>{const p=window.ethereum;if(!p)throw new Error("No injected wallet found");try{await p.request({method:"wallet_switchEthereumChain",params:[{chainId:HEX}]})}catch(e:any){if(e?.code!==4902)throw e;await p.request({method:"wallet_addEthereumChain",params:[{chainId:HEX,chainName:"GenLayer Studionet",nativeCurrency:{name:"GEN",symbol:"GEN",decimals:18},rpcUrls:[RPC],blockExplorerUrls:[EXPLORER]}]})}await refresh()};
 const connect=async()=>{const p=window.ethereum;if(!p)throw new Error("Install an injected EIP-1193 wallet");setBusy(true);try{const a=await p.request({method:"eth_requestAccounts"});setAddress(a?.[0]||null);await switchNetwork()}finally{setBusy(false)}};
 const disconnect=async()=>{const p=window.ethereum;setBusy(true);try{await p?.request({method:"wallet_revokePermissions",params:[{eth_accounts:{}}]})}catch{}finally{setAddress(null);setChainOk(false);setBusy(false)}};
 const value=useMemo(()=>({address,chainOk,busy,connect,disconnect,switchNetwork}),[address,chainOk,busy]);return <C.Provider value={value}>{children}</C.Provider>
}
export function useResearcher(){const v=useContext(C);if(!v)throw new Error("ResearcherSession missing");return v}
