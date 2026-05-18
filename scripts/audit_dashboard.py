#!/usr/bin/env python3
"""audit_dashboard.py — 跑全部 mp4 audit_v2 输出 markdown 报表"""
import subprocess, json, glob, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
mp4s = sorted(glob.glob("/Users/coco/mcstory/outputs/*_2026*/final.mp4"))
print(f"# audit dashboard — {len(mp4s)} mp4\n")
print("| sample | size MB | motion | luma | pass |")
print("|---|---|---|---|---|")
ok = 0
for m in mp4s:
    r = subprocess.run(["python3", str(ROOT/"scripts/self_audit_v2.py"), m],
                       capture_output=True, text=True, timeout=120)
    try:
        d = json.loads(r.stdout)
        sid = Path(m).parent.name.split("_2026")[0]
        sz = os.path.getsize(m)/1024/1024
        flag = "✅" if d["pass"] else "❌"
        if d["pass"]: ok += 1
        print(f"| {sid} | {sz:.1f} | {d.get('motion_signal',0):.2f} | {d.get('luma_diversity',0):.2f} | {flag} |")
    except: pass
print(f"\n**Total: {ok}/{len(mp4s)} PASS ({100*ok/max(1,len(mp4s)):.0f}%)**")
