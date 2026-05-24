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

# 双维路由: 场景/材质关键词→风格, 功能关键词→建筑类型 → minecolonies 真精模名
def route(p):
    # 风格 (默认 birch 明亮木)
    style = 'birch'
    for kws, s in [
        (('沙漠','desert','沙','埃及','金字塔','黄沙'), 'sandstone'),
        (('暗','黑','哥特','深色','darkoak','幽暗'), 'darkoak'),
        (('石','城堡','stone','灰','现代'), 'stone'),
        (('雪','松','北欧','taiga','寒','冬'), 'taiga'),
    ]:
        if any(k in p for k in kws): style = s; break
    # 类型 (默认 townhall 大厅)
    typ = 'townhall'
    for kws, t in [
        (('民居','房','家','住宅','小屋','citizen','house'), 'citizen'),
        (('农','farm','田','庄园'), 'farmer'),
        (('塔','哨','瞭望','guard','tower','灯塔'), 'guardtower'),
        (('兵营','营房','barrack','军'), 'barracks'),
        (('仓库','warehouse','货','库'), 'warehouse'),
        (('市政','镇','府','大厅','townhall','hall','村','宫'), 'townhall'),
    ]:
        if any(k in p for k in kws): typ = t; break
    # stone 风格只有 citizen/farmer; 回退 birch
    name = f"{style}_{typ}_{typ}5"
    valid = {  # 已验证存在的组合
        'birch','darkoak','sandstone','taiga'  # 这些风格全类型齐
    }
    if style == 'stone' and typ not in ('citizen','farmer'):
        style = 'birch'; name = f"{style}_{typ}_{typ}5"
    return name

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
# 按类型估算精模尺寸 → 自适应居中放置 + 后面 orbit 半径
SIZE = {'citizen':14, 'farmer':32, 'guardtower':12, 'barracks':28, 'warehouse':28, 'townhall':40}
btype = name.split('_')[1]
bsz = SIZE.get(btype, 34)
off = bsz // 2
px, pz = cx - off, cz - off
rp = subprocess.run([VENV, 'scripts/nbt_importer.py', 'place', name, str(px), str(FLOOR_Y+1), str(pz)],
                    capture_output=True, text=True, timeout=120)
print(rp.stdout[-200:], flush=True)
if 'Loaded' not in rp.stdout and 'placed' not in rp.stdout.lower():
    print("PLACE FAILED:", rp.stderr[-200:], flush=True); sys.exit(1)
time.sleep(2)

# 2) 环绕运镜
ccx, ccy, ccz = cx, FLOOR_Y + max(8, int(bsz*0.35)), cz
radius = max(int(bsz*0.95) + 12, 20)  # 半径随精模尺寸自适应
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
