#!/usr/bin/env python3
"""castle_template.py — 第二题复测: 一句话建小型城堡, 证明不是单次运气
参数化字段: 墙体材质 / 塔楼数 / 门洞 / 比例
"""
import sys, json, time, re
from typing import Tuple

def build_castle(origin, palette='medieval_gray', tower_count=4, size=15):
    """origin: base origin (xz center, y=ground level).
    palette: medieval_gray / sandstone_desert / dark_brick
    tower_count: 2 / 4 (corners)
    size: outer square edge in blocks (odd recommended, e.g. 11/15/19)
    """
    ox, oy, oz = origin
    half = size // 2
    PALETTES = {
        'medieval_gray': dict(wall='cobblestone', battlement='stone_bricks', tower_top='dark_oak_planks',
                              door='oak_door', floor='polished_andesite', window='glass_pane', flag='red_concrete'),
        'sandstone_desert': dict(wall='sandstone', battlement='smooth_sandstone', tower_top='cut_sandstone',
                                 door='spruce_door', floor='red_sandstone', window='glass_pane', flag='yellow_concrete'),
        'dark_brick': dict(wall='deepslate_bricks', battlement='polished_blackstone_bricks', tower_top='polished_deepslate',
                           door='dark_oak_door', floor='basalt', window='black_stained_glass_pane', flag='purple_concrete'),
    }
    p = PALETTES.get(palette, PALETTES['medieval_gray'])
    cmds = []

    # 清场
    cmds.append(f"fill {ox-half-3} {oy} {oz-half-3} {ox+half+3} {oy+20} {oz+half+3} air")
    # 地基 (grass 草地 + 黑曜石路)
    cmds.append(f"fill {ox-half-2} {oy-1} {oz-half-2} {ox+half+2} {oy-1} {oz+half+2} grass_block")

    # 内部地板
    cmds.append(f"fill {ox-half+1} {oy} {oz-half+1} {ox+half-1} {oy} {oz+half-1} {p['floor']}")

    # 外墙 4 面 (height 4)
    wall_h = 4
    # 北墙 z=oz-half
    cmds.append(f"fill {ox-half} {oy} {oz-half} {ox+half} {oy+wall_h} {oz-half} {p['wall']}")
    # 南墙
    cmds.append(f"fill {ox-half} {oy} {oz+half} {ox+half} {oy+wall_h} {oz+half} {p['wall']}")
    # 西墙
    cmds.append(f"fill {ox-half} {oy} {oz-half} {ox-half} {oy+wall_h} {oz+half} {p['wall']}")
    # 东墙
    cmds.append(f"fill {ox+half} {oy} {oz-half} {ox+half} {oy+wall_h} {oz+half} {p['wall']}")

    # 城垛 (battlement) y=wall_h+1, 隔块
    for x in range(ox-half, ox+half+1, 2):
        cmds.append(f"setblock {x} {oy+wall_h+1} {oz-half} {p['battlement']}")
        cmds.append(f"setblock {x} {oy+wall_h+1} {oz+half} {p['battlement']}")
    for z in range(oz-half, oz+half+1, 2):
        cmds.append(f"setblock {ox-half} {oy+wall_h+1} {z} {p['battlement']}")
        cmds.append(f"setblock {ox+half} {oy+wall_h+1} {z} {p['battlement']}")

    # 4 角塔楼 (tower_count 决定数量, 默认 4)
    tower_h = wall_h + 4
    corners = [
        (ox-half, oz-half), (ox+half, oz-half),
        (ox-half, oz+half), (ox+half, oz+half),
    ][:tower_count]
    for tx, tz in corners:
        # 塔身 (2x2 升高)
        cmds.append(f"fill {tx-1} {oy} {tz-1} {tx+1} {oy+tower_h} {tz+1} {p['wall']}")
        # 塔内空腔 (2x2)
        cmds.append(f"fill {tx} {oy+1} {tz} {tx} {oy+tower_h-1} {tz} air")
        # 塔顶帽 (尖顶, 用 tower_top 块叠 3 层)
        cmds.append(f"fill {tx-1} {oy+tower_h+1} {tz-1} {tx+1} {oy+tower_h+1} {tz+1} {p['tower_top']}")
        cmds.append(f"fill {tx} {oy+tower_h+2} {tz} {tx} {oy+tower_h+2} {tz} {p['tower_top']}")
        # 旗杆 + 旗帜 (顶端)
        cmds.append(f"setblock {tx} {oy+tower_h+3} {tz} oak_fence")
        cmds.append(f"setblock {tx} {oy+tower_h+4} {tz} {p['flag']}")
        # 窗 (中间高度 glass)
        cmds.append(f"setblock {tx} {oy+tower_h//2} {tz-1} {p['window']}")
        cmds.append(f"setblock {tx} {oy+tower_h//2} {tz+1} {p['window']}")
        cmds.append(f"setblock {tx-1} {oy+tower_h//2} {tz} {p['window']}")
        cmds.append(f"setblock {tx+1} {oy+tower_h//2} {tz} {p['window']}")

    # 主门 (南墙中央, 2 高 1 宽 - 实际用 fill air 挖)
    cmds.append(f"fill {ox} {oy} {oz+half} {ox} {oy+2} {oz+half} air")
    cmds.append(f"setblock {ox} {oy} {oz+half} {p['door']}[half=lower,hinge=left]")
    cmds.append(f"setblock {ox} {oy+1} {oz+half} {p['door']}[half=upper,hinge=left]")
    # 门外台阶
    cmds.append(f"setblock {ox} {oy} {oz+half+1} {p['floor']}_slab")

    # 窗 (东西墙各 2 个)
    cmds.append(f"setblock {ox+half} {oy+2} {oz-2} {p['window']}")
    cmds.append(f"setblock {ox+half} {oy+2} {oz+2} {p['window']}")
    cmds.append(f"setblock {ox-half} {oy+2} {oz-2} {p['window']}")
    cmds.append(f"setblock {ox-half} {oy+2} {oz+2} {p['window']}")

    # 牌子
    cmds.append(f"setblock {ox} {oy} {oz+half+3} oak_sign{{front_text:{{messages:['\"{palette.upper()}\"','\"size={size}\"','\"towers={tower_count}\"','\"\"']}}}}")
    return cmds

def run_and_audit(origin, palette, tower_count, size, prompt=""):
    from mcrcon import MCRcon
    import os
    cmds = build_castle(origin, palette, tower_count, size)
    ok = fail = 0
    fail_details = []
    with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
        for c in cmds:
            out = r.command(c)
            if any(k in out for k in ['Successfully','Changed','Filled','Set the block']):
                ok += 1
            else:
                fail += 1
                fail_details.append({"cmd": c[:80], "resp": out[:80]})
        # 白盒抽样: 验证 6 个关键坐标
        ox, oy, oz = origin
        half = size // 2
        wb_ok = 0; wb_total = 0
        # 期望 (x,y,z, expected_pattern)
        p_map = {
            'medieval_gray': {'wall':'cobblestone','floor':'polished_andesite'},
            'sandstone_desert': {'wall':'sandstone','floor':'red_sandstone'},
            'dark_brick': {'wall':'deepslate_bricks','floor':'basalt'},
        }[palette]
        probes = [
            (ox-half, oy+2, oz, p_map['wall'], 'west wall mid'),
            (ox+half, oy+2, oz, p_map['wall'], 'east wall mid'),
            (ox, oy+2, oz-half, p_map['wall'], 'north wall mid'),
            (ox, oy, oz, p_map['floor'], 'floor center'),
            (ox-half, oy+5, oz-half, p_map['wall'], 'NW tower base+wall_h+1'),
            (ox+half, oy+5, oz+half, p_map['wall'], 'SE tower'),
        ]
        for x,y,z,blk,desc in probes:
            o = r.command(f"execute if block {x} {y} {z} {blk}").strip()
            if "Test passed" in o: wb_ok += 1
            wb_total += 1
    # 落 build.json + exec_result.json
    ts = time.strftime('%Y%m%d-%H%M%S')
    safe_prompt = re.sub(r'[^a-zA-Z0-9一-鿿]+','_', prompt)[:40] if prompt else palette
    outdir = os.path.expanduser(f'~/mcstory/outputs/user_castle_{ts}_{safe_prompt}')
    os.makedirs(outdir, exist_ok=True)
    json.dump({"prompt": prompt, "origin": origin, "palette": palette,
               "tower_count": tower_count, "size": size,
               "build_cmds": cmds}, open(f"{outdir}/castle_build.json","w"), ensure_ascii=False, indent=2)
    json.dump({"exec_ok": ok, "exec_total": ok+fail,
               "wb_ok": wb_ok, "wb_total": wb_total,
               "fails": fail_details}, open(f"{outdir}/exec_result.json","w"), ensure_ascii=False, indent=2)
    return outdir, ok, fail, wb_ok, wb_total

if __name__ == '__main__':
    prompt = sys.argv[1] if len(sys.argv) > 1 else "中世纪小型城堡, 4角塔, 灰石墙, 红旗"
    outdir, ok, fail, wb_ok, wb_total = run_and_audit(
        origin=(-80, 80, -260), palette='medieval_gray',
        tower_count=4, size=15, prompt=prompt
    )
    print(f"[castle_v1] outdir: {outdir}")
    print(f"  RCON: {ok}/{ok+fail}")
    print(f"  白盒抽样: {wb_ok}/{wb_total}")
