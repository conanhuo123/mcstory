#!/usr/bin/env python3
"""mcstory cli — 一条命令把一句话变成 MC 短剧脚本+timeline+bot.js
Usage: python3 cli.py "苦力怕跟村民道歉"
"""
import sys, os, json, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(f"❌ {' '.join(map(str,cmd))[:80]}: {r.stderr[-200:]}"); sys.exit(1)
    return r.stdout

def main(prompt):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / "outputs" / f"job_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    script_p = out_dir / "script.json"
    timeline_p = out_dir / "timeline.json"
    
    print(f"=== mcstory job {stamp} ===")
    print(f"prompt: {prompt}")
    
    # 1. parse
    print("[1/3] parse → 剧本 JSON...")
    out = run(["python3", str(ROOT/"scripts/parse.py"), prompt])
    # parse.py 输出 JSON 到 stdout
    script_p.write_text(out)
    s = json.loads(out)
    print(f"  ✓ scene={s['scene']} chars={len(s['characters'])} shots={len(s['shots'])}")
    
    # 2. translate
    print("[2/3] translate → timeline...")
    run(["python3", str(ROOT/"scripts/translate.py"), str(script_p), str(timeline_p)])
    tl = json.loads(timeline_p.read_text())
    print(f"  ✓ events={len(tl['timeline'])}")
    
    # 3. record (生成 server cmds + bot.js)
    print("[3/3] record → MC commands + bot.js...")
    run(["python3", str(ROOT/"scripts/record.py"), str(timeline_p)])
    
    print(f"\n✓ 全部落盘到 {out_dir}/")
    for f in sorted(out_dir.iterdir()):
        print(f"  - {f.name}")
    print(f"\n下一步 (人工/自动): 启 Paper 服 → 跑 bot.js → ReplayMod 录像 → postprod.py")
    return out_dir

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
