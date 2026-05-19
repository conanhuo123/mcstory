#!/usr/bin/env python3
"""smooth_outline_fix.py — 修轮廓 FAIL→PASS (脱方块感)
机甲: 加 stairs (肩部+头顶圆边) + slabs (装甲薄边)
城堡: 加 stairs (塔顶尖顶 4 圈) + sphere 圆顶
"""
from mcrcon import MCRcon

def fix_mecha_outline(rcon, origin):
    """高达 v1 (-100, 80, -300) 加圆边"""
    ox, oy, oz = origin
    cmds = []
    # 肩部圆角 (stairs 4 角)
    # 高达 v1 双肩在 y=85 高度 (z=-300 平面), x=-104 和 x=-96
    cmds.append(f"setblock {ox-4} {oy+6} {oz-1} quartz_stairs[facing=south]")
    cmds.append(f"setblock {ox+4} {oy+6} {oz-1} quartz_stairs[facing=south]")
    cmds.append(f"setblock {ox-4} {oy+6} {oz+1} quartz_stairs[facing=north]")
    cmds.append(f"setblock {ox+4} {oy+6} {oz+1} quartz_stairs[facing=north]")
    # 头顶圆角 (stairs 4 角)
    cmds.append(f"setblock {ox-2} {oy+11} {oz-1} quartz_stairs[facing=south]")
    cmds.append(f"setblock {ox+2} {oy+11} {oz-1} quartz_stairs[facing=south]")
    cmds.append(f"setblock {ox-2} {oy+11} {oz+1} quartz_stairs[facing=north]")
    cmds.append(f"setblock {ox+2} {oy+11} {oz+1} quartz_stairs[facing=north]")
    # 腰部装饰 slab (薄边)
    cmds.append(f"setblock {ox-3} {oy+4} {oz} quartz_slab[type=bottom]")
    cmds.append(f"setblock {ox+3} {oy+4} {oz} quartz_slab[type=bottom]")
    # 胸前圆弧 (red_stained_glass 透半透 + stairs)
    cmds.append(f"setblock {ox-1} {oy+6} {oz-2} red_glazed_terracotta[facing=south]")
    cmds.append(f"setblock {ox+1} {oy+6} {oz-2} red_glazed_terracotta[facing=south]")
    return cmds


def fix_castle_outline(rcon, origin, size=15):
    """城堡 (-80, 80, -260) 塔顶尖顶 + 城垛圆角"""
    ox, oy, oz = origin
    half = size // 2
    cmds = []
    # 4 角塔 顶端 stairs 收尖
    tower_h = 8  # wall(4) + tower extra(4)
    corners = [(ox-half, oz-half), (ox+half, oz-half), (ox-half, oz+half), (ox+half, oz+half)]
    for tx, tz in corners:
        # 第 1 圈 stairs 包围 (面外)
        top_y = oy + tower_h + 2  # 塔顶帽之上 1 块开始
        # 北 stairs facing south (= 朝塔中央)
        cmds.append(f"setblock {tx} {top_y} {tz-1} stone_brick_stairs[facing=south]")
        cmds.append(f"setblock {tx-1} {top_y} {tz} stone_brick_stairs[facing=east]")
        cmds.append(f"setblock {tx+1} {top_y} {tz} stone_brick_stairs[facing=west]")
        cmds.append(f"setblock {tx} {top_y} {tz+1} stone_brick_stairs[facing=north]")
        # 顶尖 (slab + 旗杆)
        cmds.append(f"setblock {tx} {top_y+1} {tz} stone_brick_slab[type=top]")
    # 城垛之间填 slab (薄边过渡, 替代单块直角)
    for x in range(ox-half+1, ox+half, 2):
        cmds.append(f"setblock {x} {oy+5} {oz-half} stone_brick_slab[type=top]")
        cmds.append(f"setblock {x} {oy+5} {oz+half} stone_brick_slab[type=top]")
    for z in range(oz-half+1, oz+half, 2):
        cmds.append(f"setblock {ox-half} {oy+5} {z} stone_brick_slab[type=top]")
        cmds.append(f"setblock {ox+half} {oy+5} {z} stone_brick_slab[type=top]")
    # 主门拱顶 (3 块 stairs)
    cmds.append(f"setblock {ox-1} {oy+3} {oz+half} stone_brick_stairs[facing=west,half=top]")
    cmds.append(f"setblock {ox} {oy+3} {oz+half} stone_brick_slab[type=top]")
    cmds.append(f"setblock {ox+1} {oy+3} {oz+half} stone_brick_stairs[facing=east,half=top]")
    return cmds


if __name__ == '__main__':
    with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
        mecha_cmds = fix_mecha_outline(r, (-100, 80, -300))
        castle_cmds = fix_castle_outline(r, (-80, 80, -260), 15)
        all_cmds = mecha_cmds + castle_cmds
        ok = 0; fail = 0
        for c in all_cmds:
            o = r.command(c)
            if 'Set the block' in o or 'Changed' in o or 'Successfully' in o:
                ok += 1
            else:
                fail += 1
                print(f"  FAIL: {c[:80]} -> {o[:80]}")
        print(f"\nmecha+castle outline fix: {ok}/{ok+fail} OK ({len(mecha_cmds)} mecha + {len(castle_cmds)} castle)")
