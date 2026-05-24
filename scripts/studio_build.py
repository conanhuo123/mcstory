#!/usr/bin/env python3
# studio_build.py — 清出平整 studio 地台(无树无坡) → 在台上 build, 保证截图无遮挡
# 用法: python3 studio_build.py "<prompt>" <cx> <cz>   (地台中心 x z, 地面固定 y=100)
import sys, subprocess, os, time
from mcrcon import MCRcon

prompt, cx, cz = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
FLOOR_Y = 100
HALF = 50  # 100x100 地台

x0, x1 = cx - HALF, cx + HALF
z0, z1 = cz - HALF, cz + HALF

def fill(r, a, b, c, d, e, f, block, mode=''):
    out = r.command(f'fill {a} {b} {c} {d} {e} {f} minecraft:{block} {mode}'.strip())
    return out

t0 = time.time()
with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
    print('range forceload...', flush=True)
    r.command(f'forceload add {x0} {z0} {x1} {z1}')
    time.sleep(3)  # 等区块真加载完再 fill, 否则远坐标 fill 落空→无平台→建筑下沉→gate1 FAIL
    # 1) 清空上方 (y101..152), 分层 chunk (<32768/fill: 100x100x3=30000)
    print('clearing air above...', flush=True)
    y = FLOOR_Y + 1
    while y <= 152:
        fill(r, x0, y, z0, x1, min(y + 2, 152), z1, 'air')
        y += 3
    # 2) 实心基底 (y96..99 石) + 地面 (y100 草)
    print('laying floor...', flush=True)
    fill(r, x0, 96, z0, x1, 98, z1, 'stone')
    fill(r, x0, 99, z0, x1, 99, z1, 'dirt')
    fill(r, x0, FLOOR_Y, z0, x1, FLOOR_Y, z1, 'grass_block')
    print(f'studio ready @ center {cx},{FLOOR_Y},{cz} ({time.time()-t0:.0f}s)', flush=True)

# 3) 在地台中心建 (probe 会找到 y100 平地)
print('building...', flush=True)
env = dict(os.environ)
r = subprocess.run(
    ['.venv/bin/python', 'scripts/nlp_to_building.py', prompt, str(cx), str(FLOOR_Y + 1), str(cz)],
    env=env, capture_output=True, text=True, timeout=240)
print(r.stdout[-600:], flush=True)
if r.returncode != 0:
    print('BUILD STDERR:', r.stderr[-400:], flush=True)
print('STUDIO_BUILD_DONE', flush=True)
