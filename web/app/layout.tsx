import type {Metadata,Viewport} from "next";
import "@/visual-language/foundations.css";
import "@/visual-language/document-grid.css";
import "@/visual-language/typography.css";
import "./globals.css";
import {Providers} from "./providers";
export const metadata:Metadata={title:{default:"REPROVE",template:"%s · REPROVE"},description:"A GenLayer-native registry for preregistered scientific replication and finalized evidence records."};
export const viewport:Viewport={themeColor:"#edf5fb"};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body className="research-grid"><Providers>{children}</Providers></body></html>}
