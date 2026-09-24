import {StudyPaper} from "@/surfaces/study-paper/StudyPaper";
export default async function Page({params}:{params:Promise<{studyKey:string}>}){const {studyKey}=await params;return <StudyPaper studyKey={decodeURIComponent(studyKey)}/>}
