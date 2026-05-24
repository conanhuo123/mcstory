#!/usr/bin/env python3
# one_line_l1_to_mp4.py — 真产品MVP: 一句话 → 路由L1真精模(minecolonies) → 清台放置 → 环绕 → mp4
# 一句话出"好看"视频(L1玩家精模质量), 区别于 one_line_to_mp4(L2程序化).
# 用法: python3 one_line_l1_to_mp4.py "<中文一句话>" [cx cz]
import sys, os, subprocess, time, glob
from mcrcon import MCRcon

prompt = sys.argv[1]
cx = int(sys.argv[2]) if len(sys.argv) > 2 else -1400
cz = int(sys.argv[3]) if len(sys.argv) > 3 else -1400
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
VENV = os.path.join(ROOT, '.venv/bin/python')
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FLOOR_Y = 100
ts = time.strftime('%H%M%S')

# 简易路由: 关键词 → minecolonies 精模名 (默认大气宅邸 townhall5)
def route(p):
    table = [
        (('塔','哨塔','瞭望','tower'), 'birch_guardtower_guardtower5'),
        (('兵营','营房','barrack'), 'birch_barracktower_barrackstower5'),
        (('市政','镇','宅','府','大厅','townhall','hall','村'), 'birch_townhall_townhall5'),
    ]
    for kws, name in table:
        if any(k in p for k in kws):
            return name
    return 'birch_townhall_townhall5'

name = route(prompt)
print(f"[route] '{prompt}' → L1精模 {name}", flush=True)

# 1) 清平整 studio 地台 (120x120) + 放置精模
HALF = 60
print(f"[1/3] clear studio @ {cx},{cz} + place {name}", flush=True)
with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
    r.command(f'forceload add {cx-HALF} {cz-HALF} {cx+HALF} {cz+HALF}')
    y = FLOOR_Y + 1
    while y <= 150:
        r.command(f'fill {cx-HALF} {y} {cz-HALF} {cx+HALF} {y} {cz+HALF} air'); y += 1
    r.command(f'fill {cx-HALF} 96 {cz-HALF} {cx+HALF} 99 {cz+HALF} stone')
    r.command(f'fill {cx-HALF} {FLOOR_Y} {cz-HALF} {cx+HALF} {FLOOR_Y} {cz+HALF} grass_block')
# 放置: 精模约40大, 放在 (cx-20,cz-20) 使其中心≈(cx,cz)
px, pz = cx - 20, cz - 20
rp = subprocess.run([VENV, 'scripts/nbt_importer.py', 'place', name, str(px), str(FLOOR_Y+1), str(pz)],
                    capture_output=True, text=True, timeout=120)
print(rp.stdout[-200:], flush=True)
if 'Loaded' not in rp.stdout and 'placed' not in rp.stdout.lower():
    print("PLACE FAILED:", rp.stderr[-200:], flush=True); sys.exit(1)
time.sleep(2)

# 2) 环绕运镜
ccx, ccy, ccz = cx, FLOOR_Y + 10, cz
radius = 42
outdir = f"outputs/l1auto_{name}_{ts}"
print(f"[2/3] orbit center({ccx},{ccy},{ccz}) r={radius}", flush=True)
r2 = subprocess.run(['node', 'scripts/orbit_video.js', str(ccx), str(ccy), str(ccz), str(radius), "36", outdir],
                    capture_output=True, text=True, env=dict(os.environ, CHROME_PATH=CHROME), timeout=400)
print(r2.stdout[-200:], flush=True)
if 'FRAMES_DONE' not in r2.stdout:
    print("ORBIT FAILED:", r2.stderr[-200:], flush=True); sys.exit(1)

# 3) ffmpeg → mp4
print("[3/3] ffmpeg → mp4", flush=True)
mp4 = f"{outdir}/video.mp4"
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','12','-i',f"{outdir}/frame_%03d.png",
                '-c:v','libx264','-pix_fmt','yuv420p','-vf','scale=1280:720', mp4], check=True)
print(f"PIPELINE_DONE mp4={mp4} size={os.path.getsize(mp4)//1024}KB", flush=True)
