from pathlib import Path
import json, re, sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
required=[
 "contracts/study_registry.py","contracts/replication_engine.py","contracts/research_pool.py",
 "web/app/page.tsx","web/app/lab/page.tsx","web/app/claim/[studyKey]/page.tsx",
 "web/app/attempt/[attemptKey]/page.tsx","web/app/archive/[recordKey]/page.tsx",
 "web/surfaces/atlas/AtlasSurface.tsx","web/surfaces/notebook/ReplicationNotebook.tsx",
 "deploy/deployScript.ts","MEGA_PROMPT_FOR_AGENT.md"
]
for p in required:
    if not (ROOT/p).exists(): errors.append(f"missing {p}")
# Exact public route architecture and explicit anti-convergence guard.
banned_routes=["dashboard","console","release","proof","account","protocol","settings","incidents","settlements","agreements"]
app=ROOT/"web/app"
for child in app.iterdir():
    if child.is_dir() and child.name.lower() in banned_routes:
        errors.append(f"forbidden route directory: {child.name}")
expected_routes={"/","/lab","/claim/[studyKey]","/attempt/[attemptKey]","/archive/[recordKey]"}
discovered_routes=set()
for page in app.rglob("page.tsx"):
    parent=page.parent.relative_to(app)
    route="/" if str(parent)=="." else "/"+parent.as_posix()
    discovered_routes.add(route)
if discovered_routes != expected_routes:
    errors.append(f"route set mismatch: expected {sorted(expected_routes)}, found {sorted(discovered_routes)}")
banned_component_names={"Header.tsx","Footer.tsx","WalletButton.tsx","TxNotice.tsx","Sidebar.tsx","Dashboard.tsx"}
for p in (ROOT/"web").rglob("*.tsx"):
    if p.name in banned_component_names: errors.append(f"forbidden generic component name: {p.relative_to(ROOT)}")
# Do not accidentally converge on PATHCLOCK's warm palette.
css="\n".join(p.read_text(errors="ignore") for p in (ROOT/"web").rglob("*.css"))
for old in ["#f4f1e8","#201d19","#8b4b30","#b87b26","#2d6b55"]:
    if old.lower() in css.lower(): errors.append(f"PATHCLOCK palette token found: {old}")
# Studionet constants.
text="\n".join(p.read_text(errors="ignore") for p in ROOT.rglob("*.ts") if "node_modules" not in p.parts)
if "61999" not in text: errors.append("Studionet chain ID missing from TS sources")
manifest=json.loads((ROOT/"deployments/studionet.json").read_text())
if manifest.get("chainId")!=61999: errors.append("deployment manifest chainId is not 61999")
if errors:
    print("RELEASE CHECK FAILED")
    for e in errors: print(" -",e)
    sys.exit(1)
print("RELEASE CHECK OK")
print("Routes: /, /lab, /claim/[studyKey], /attempt/[attemptKey], /archive/[recordKey]")
print("Clean-room route/component/palette guards passed.")
