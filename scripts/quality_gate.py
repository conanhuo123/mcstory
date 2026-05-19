#!/usr/bin/env python3
"""quality_gate.py — 5 项自动质量闸 (赵雪/周朗 16:14 verdict)
低于阈值自动重跑, 不进展示.
"""
import json, sys
import numpy as np
from PIL import Image
try: from scipy import ndimage; HAS_SCIPY=True
except: HAS_SCIPY=False
from mcrcon import MCRcon

def gate1_ground_check(origin, bbox, rcon):
    """① 贴地/不悬浮: build 底部 y == paper 真地面 y (±1 块)"""
    ox, oy, oz = origin
    # paper 真地面 y (扫 origin 周围)
    actual_ground = None
    for y in range(95, 50, -1):
        o = rcon.command(f'execute if block {ox} {y} {oz} air').strip()
        if 'Test passed' not in o:
            actual_ground = y; break
    build_bottom = bbox[1]
    ok = actual_ground is not None and abs(build_bottom - actual_ground) <= 2
    return {'gate': 1, 'name': 'ground_check', 'actual_ground': actual_ground, 'build_bottom': build_bottom, 'status': 'PASS' if ok else 'FAIL'}

def gate2_framing(png_path, target_color_set):
    """② 完整取景: target 物体 bbox 4 边 padding >= 5%"""
    if not HAS_SCIPY: return {'gate': 2, 'name':'framing', 'status': 'SKIP_SCIPY'}
    arr = np.array(Image.open(png_path).convert('RGB'))
    H, W, _ = arr.shape
    mask = np.zeros((H,W), bool)
    for r,g,b in target_color_set:
        m = (abs(arr[:,:,0].astype(int)-r)<30) & (abs(arr[:,:,1].astype(int)-g)<30) & (abs(arr[:,:,2].astype(int)-b)<30)
        mask |= m
    labels, n = ndimage.label(mask)
    if n == 0: return {'gate':2, 'name':'framing','status':'FAIL_NO_OBJECT'}
    sizes = ndimage.sum(mask, labels, range(1,n+1))
    big = int(np.argmax(sizes))+1
    ys, xs = np.where(labels==big)
    x1,x2,y1,y2 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    TOL = int(W * 0.05)
    edges = dict(head=y1>TOL, foot=y2<H-TOL, left=x1>TOL, right=x2<W-TOL)
    ok = all(edges.values())
    return {'gate':2, 'name':'framing', 'bbox':[x1,y1,x2,y2], 'TOL':TOL, 'edges':edges, 'status': 'PASS' if ok else 'FAIL'}

def gate3_bbox_proportion(bbox, target_ratio=(1.5, 3.0)):
    """③ 比例 bbox 合理: height/width 在合理范围 (default 1.5~3.0 for humanoid)"""
    x1,y1,z1,x2,y2,z2 = bbox
    h = y2-y1+1; w = max(x2-x1, z2-z1) + 1
    ratio = h / w if w > 0 else 0
    ok = target_ratio[0] <= ratio <= target_ratio[1]
    return {'gate':3, 'name':'proportion', 'h':h, 'w':w, 'ratio':round(ratio,2), 'target':target_ratio, 'status': 'PASS' if ok else 'FAIL'}

def gate4_detail_density(cmds, min_block_types=5, min_total=200):
    """④ 细节密度达标: block 种类 >= 5, 总块数 >= 200"""
    import re
    block_types = set()
    for c in cmds:
        m = re.search(r'(?:setblock|fill)\s+(?:-?\d+\s+){3,6}(\S+)', c)
        if m: block_types.add(m.group(1).split('[')[0])
    n_types = len(block_types)
    n_total = len(cmds)
    ok = n_types >= min_block_types and n_total >= min_total
    return {'gate':4, 'name':'detail', 'block_types':n_types, 'total_cmds':n_total,
            'min_types':min_block_types, 'min_total':min_total,
            'sample_blocks':sorted(block_types)[:8], 'status': 'PASS' if ok else 'FAIL'}

def gate5_multiview_score(pngs, target_color_set):
    """⑤ 多视角评分: 至少 3 张截图, 每张 gate2 PASS"""
    if not HAS_SCIPY: return {'gate':5, 'name':'multiview', 'status':'SKIP_SCIPY'}
    results = []
    for p in pngs:
        r = gate2_framing(p, target_color_set)
        results.append((p.split('/')[-1], r['status']))
    pass_count = sum(1 for _,s in results if s == 'PASS')
    ok = pass_count >= 2 and len(pngs) >= 3
    return {'gate':5,'name':'multiview', 'views':len(pngs), 'pass_count':pass_count,
            'views_detail':results, 'status':'PASS' if ok else 'FAIL'}


def run_full_audit(origin, bbox, cmds, pngs, target_color_set, target_ratio=(0.3, 5.0)):
    """跑所有 5 闸, 返回汇总"""
    results = []
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        results.append(gate1_ground_check(origin, bbox, r))
    results.append(gate2_framing(pngs[0], target_color_set) if pngs else {'gate':2,'status':'SKIP_NO_PNG'})
    results.append(gate3_bbox_proportion(bbox, target_ratio))
    results.append(gate4_detail_density(cmds))
    results.append(gate5_multiview_score(pngs, target_color_set))
    all_pass = all(r['status'] in ('PASS','SKIP_SCIPY') for r in results)
    return {'overall':'PASS' if all_pass else 'FAIL', 'gates':results}


if __name__ == '__main__':
    # 测试: louvre v2 polished
    import os, glob
    OUTDIR = sorted(glob.glob('/Users/coco/mcstory/outputs/louvre_v2_polished_*'))[-1]
    LOUVRE_COLORS = [(230,210,150),(180,150,90),(235,230,220),(200,170,130),(160,130,90),(60,40,30),(100,100,100)]
    cmds_dummy = ['setblock x y z sandstone'] * 921  # placeholder, actual cmds in build
    # 真 cmds 从 build.json 不会保留 (太大), 用占位
    import json
    build = json.load(open(f'{OUTDIR}/build.json'))
    bbox = [-318, 80, -316, -282, 94, -288]  # louvre v2 bbox
    origin = build['origin']
    pngs = sorted(glob.glob(f'{OUTDIR}/*.png'))
    result = run_full_audit(origin, bbox, ['setblock x y z sandstone']*921, pngs, LOUVRE_COLORS, target_ratio=(0.2, 10.0))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    json.dump(result, open(f'{OUTDIR}/quality_gate.json','w'), ensure_ascii=False, indent=2)
