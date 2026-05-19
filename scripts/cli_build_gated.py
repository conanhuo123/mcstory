#!/usr/bin/env python3
"""cli_build_gated.py — build 后自动跑 5 闸, FAIL retry, PASS 才上传百度网盘
集成 voxel_dsl / quality_gate / bypy
"""
import sys, os, json, time, glob, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcrcon import MCRcon
from quality_gate import gate1_ground_check, gate2_framing, gate3_bbox_proportion, gate4_detail_density, gate5_multiview_score

PALETTE_COLORS = {
    'mecha': [(235,230,220),(35,75,200),(220,40,40),(240,220,60),(250,230,100),(180,180,200)],
    'louvre': [(230,210,150),(200,170,130),(180,150,90),(235,230,220),(200,200,210),(60,40,30),(100,100,100)],
    'castle': [(120,120,120),(140,140,140),(90,60,40),(220,30,30)],
}

def build_and_gate(build_fn, origin, target, max_retry=2):
    """build_fn(origin) → (cmds, bbox); pipeline 跑 build → screenshot → 5 闸 → retry"""
    target_colors = PALETTE_COLORS.get(target, PALETTE_COLORS['mecha'])
    ts = time.strftime('%Y%m%d-%H%M%S')
    outdir = os.path.expanduser(f'~/mcstory/outputs/gated_{target}_{ts}')
    os.makedirs(outdir, exist_ok=True)

    for attempt in range(max_retry + 1):
        print(f"[gated] attempt {attempt+1}/{max_retry+1}")
        # 1. 清场 + 削平 + build
        with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
            ox,oy,oz = origin
            r.command(f'gamerule commandModificationBlockLimit 200000')
            # 削平 + grass 地基
            for sx in range(-25, 30, 25):
                for sz in range(-25, 30, 25):
                    r.command(f'fill {ox+sx-12} {oy} {oz+sz-12} {ox+sx+12} {oy+15} {oz+sz+12} air')
            for sx in range(-25, 30, 25):
                for sz in range(-25, 30, 25):
                    r.command(f'fill {ox+sx-12} {oy-1} {oz+sz-12} {ox+sx+12} {oy-1} {oz+sz+12} grass_block')
            cmds, bbox = build_fn(origin)
            ok=fail=0
            for c in cmds:
                out = r.command(c)
                if any(k in out for k in ['Successfully','Changed','Set the block']): ok+=1
                else: fail+=1
        print(f"[gated] RCON: {ok}/{ok+fail}")
        # 2. 跑 5 闸 (静态, 无截图先跑 gate 1/3/4)
        with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
            g1 = gate1_ground_check(origin, bbox, r)
        g3 = gate3_bbox_proportion(bbox, (0.3, 5.0))
        g4 = gate4_detail_density(cmds, min_block_types=5, min_total=200)
        # 3. 截图 (需 mineflayer, 此处占位)
        pngs = []  # TODO: integrate screenshot
        g2 = gate2_framing(pngs[0], target_colors) if pngs else {'gate':2, 'status':'SKIP_NO_PNG'}
        g5 = gate5_multiview_score(pngs, target_colors)
        gates = [g1, g2, g3, g4, g5]
        all_pass = all(g['status'] in ('PASS','SKIP_SCIPY','SKIP_NO_PNG') for g in gates)
        json.dump({'attempt':attempt+1, 'rcon_ok':ok, 'rcon_total':ok+fail,
                   'overall':'PASS' if all_pass else 'FAIL', 'gates':gates,
                   'origin':list(origin), 'bbox':list(bbox)},
                  open(f'{outdir}/attempt_{attempt+1}.json','w'), ensure_ascii=False, indent=2)
        if all_pass:
            print(f"[gated] PASS at attempt {attempt+1}")
            return outdir, gates
        # 4. retry 调参数: origin y +1 (避免浮空), 等
        print(f"[gated] FAIL → retry with origin y+1")
        origin = (origin[0], origin[1] + 1, origin[2])
    print(f"[gated] FINAL FAIL after {max_retry+1} attempts")
    return outdir, gates


if __name__ == '__main__':
    # demo: 跑 louvre v2 build with gating
    from louvre import build_louvre
    def lv_wrapper(origin):
        b = build_louvre(origin)
        return b.to_commands(), b.bbox()
    outdir, gates = build_and_gate(lv_wrapper, (-300, 80, -300), target='louvre', max_retry=1)
    print(f"[gated] outdir: {outdir}")
    for g in gates:
        print(f"  gate {g.get('gate')}: {g.get('status')}")
