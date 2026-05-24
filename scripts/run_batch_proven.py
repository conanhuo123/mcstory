#!/usr/bin/env python3
# run_batch_proven.py — 用验证过的单张 gate1_screenshot.js 循环跑 manifest, 自动取景
# 用法: python3 run_batch_proven.py <manifest.json> <outDir>
import json, sys, os, subprocess, time

manifest, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
builds = json.load(open(manifest))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def frame(o, b):
    # 建筑正面斜角, 中等高度(看到立面+屋顶, 不高俯视), 较近
    ox, oy, oz = o; w, h, d = b
    cx, cz = ox + w/2, oz + d/2
    md = max(w, d)
    dist = max(md, h) * 0.95 + 10
    cam = (cx + dist*0.45, oy + h*0.60, cz + dist*0.92)  # 偏正前+略斜, y≈建筑中上部
    look = (cx, oy + h*0.45, cz)
    return cam, look

results = []
for i, bd in enumerate(builds):
    cam, look = frame(bd["origin"], bd["bbox"])
    out = os.path.join(outdir, f"{bd['name']}.png")
    args = ["node", "scripts/gate1_screenshot.js",
            f"{cam[0]:.0f}", f"{cam[1]:.0f}", f"{cam[2]:.0f}",
            f"{look[0]:.0f}", f"{look[1]:.0f}", f"{look[2]:.0f}", out]
    print(f"[{i+1}/{len(builds)}] {bd['name']} cam={tuple(round(c) for c in cam)} -> {out}", flush=True)
    env = dict(os.environ, CHROME_PATH=CHROME)
    t0 = time.time()
    try:
        r = subprocess.run(args, env=env, capture_output=True, text=True, timeout=120)
        ok = os.path.exists(out)
        print(f"    exit={r.returncode} saved={ok} {time.time()-t0:.0f}s", flush=True)
        if not ok:
            print("    STDERR tail:", r.stderr.strip().splitlines()[-3:] if r.stderr.strip() else "(none)", flush=True)
        results.append({"name": bd["name"], "out": out, "saved": ok})
    except subprocess.TimeoutExpired:
        print(f"    TIMEOUT 120s", flush=True)
        results.append({"name": bd["name"], "out": out, "saved": False, "timeout": True})

json.dump(results, open(os.path.join(outdir, "_shots.json"), "w"), indent=2)
n_ok = sum(1 for r in results if r.get("saved"))
print(f"BATCH_DONE {n_ok}/{len(builds)} saved -> {outdir}", flush=True)
