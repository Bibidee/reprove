"use client";
import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";

export const CHAIN_ID = 61999;
export const RPC = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || "https://studio.genlayer.com/api";
export const EXPLORER = process.env.NEXT_PUBLIC_GENLAYER_EXPLORER || "https://explorer-studio.genlayer.com";
export const ADDRESSES = {
  registry: process.env.NEXT_PUBLIC_STUDY_REGISTRY_ADDRESS || "",
  engine: process.env.NEXT_PUBLIC_REPLICATION_ENGINE_ADDRESS || "",
  pool: process.env.NEXT_PUBLIC_RESEARCH_POOL_ADDRESS || "",
};

export function configured(){return Object.values(ADDRESSES).every(Boolean)}

export function reader(){return createClient({chain:studionet, endpoint:RPC} as any)}
export function signer(account:string){return createClient({chain:studionet, endpoint:RPC, account:account as `0x${string}`} as any)}
