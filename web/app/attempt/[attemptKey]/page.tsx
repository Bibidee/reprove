import {ReplicationNotebook} from "@/surfaces/notebook/ReplicationNotebook";
export default async function Page({params}:{params:Promise<{attemptKey:string}>}){const {attemptKey}=await params;return <ReplicationNotebook attemptKey={decodeURIComponent(attemptKey)}/>}
