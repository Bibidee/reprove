import {ArchiveLeaf} from "@/surfaces/archive-record/ArchiveLeaf";
export default async function Page({params}:{params:Promise<{recordKey:string}>}){const {recordKey}=await params;return <ArchiveLeaf recordKey={decodeURIComponent(recordKey)}/>}
