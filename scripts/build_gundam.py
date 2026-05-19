#!/usr/bin/env python3
"""build_gundam.py — 在 paper world 搭一个简单高达 (~12 块高, 5 块宽)
站立姿势 + 蓝红白配色 + 头部 V 形天线 + 双臂持剑
"""
from mcrcon import MCRcon

OX, OY, OZ = -100, 80, -300  # 干净区域

cmds = [
    # 清场 (大方块 air)
    f"fill {OX-8} {OY} {OZ-8} {OX+8} {OY+18} {OZ+8} air",
    # 地基 (草方块底座 11x11)
    f"fill {OX-5} {OY-1} {OZ-5} {OX+5} {OY-1} {OZ+5} grass_block",
    # === 双腿 (y=80-83) ===
    f"fill {OX-1} {OY} {OZ} {OX-1} {OY+3} {OZ} iron_block",          # 左腿
    f"fill {OX+1} {OY} {OZ} {OX+1} {OY+3} {OZ} iron_block",          # 右腿
    f"setblock {OX-1} {OY} {OZ} quartz_block",                        # 左脚白
    f"setblock {OX+1} {OY} {OZ} quartz_block",                        # 右脚白
    # === 腰 (y=84) ===
    f"fill {OX-1} {OY+4} {OZ} {OX+1} {OY+4} {OZ} quartz_block",
    # === 躯干 (y=85-87) 蓝色 ===
    f"fill {OX-1} {OY+5} {OZ} {OX+1} {OY+7} {OZ} lapis_block",
    # 胸前红色 V (装甲)
    f"setblock {OX} {OY+6} {OZ-1} red_concrete",
    f"setblock {OX-1} {OY+7} {OZ-1} red_concrete",
    f"setblock {OX+1} {OY+7} {OZ-1} red_concrete",
    # === 双肩 (y=86) ===
    f"setblock {OX-2} {OY+6} {OZ} iron_block",
    f"setblock {OX+2} {OY+6} {OZ} iron_block",
    # === 双臂 (y=84-87) ===
    f"fill {OX-2} {OY+4} {OZ} {OX-2} {OY+5} {OZ} quartz_block",       # 左上臂
    f"fill {OX+2} {OY+4} {OZ} {OX+2} {OY+5} {OZ} quartz_block",       # 右上臂
    # === 手持剑 (y=83 双手悬剑) ===
    f"setblock {OX-3} {OY+5} {OZ} iron_block",                         # 左手
    f"setblock {OX+3} {OY+5} {OZ} iron_block",                         # 右手
    f"fill {OX+3} {OY+6} {OZ} {OX+3} {OY+10} {OZ} iron_block",        # 右手剑刃竖
    f"setblock {OX+3} {OY+5} {OZ-1} iron_block",                       # 剑柄
    # === 脖颈 (y=88) ===
    f"setblock {OX} {OY+8} {OZ} quartz_block",
    # === 头部 (y=89-90) ===
    f"fill {OX-1} {OY+9} {OZ} {OX+1} {OY+10} {OZ} quartz_block",
    # 红色面罩
    f"setblock {OX} {OY+9} {OZ-1} red_concrete",
    # 黄色眼镜带
    f"setblock {OX-1} {OY+9} {OZ-1} yellow_concrete",
    f"setblock {OX+1} {OY+9} {OZ-1} yellow_concrete",
    # === V 形天线 ===
    f"setblock {OX-1} {OY+11} {OZ} yellow_concrete",
    f"setblock {OX+1} {OY+11} {OZ} yellow_concrete",
    f"setblock {OX} {OY+11} {OZ} iron_block",
    f"setblock {OX-2} {OY+12} {OZ} yellow_concrete",
    f"setblock {OX+2} {OY+12} {OZ} yellow_concrete",
    # === 牌子: "GUNDAM" ===
    f"setblock {OX} {OY-1} {OZ-6} oak_sign{{front_text:{{messages:['\"GUNDAM\"','\"v0.1\"','\"\"','\"\"']}}}}",
]

print(f"build gundam at origin ({OX},{OY},{OZ}), {len(cmds)} commands")
ok = fail = 0
with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
    for c in cmds:
        out = r.command(c)
        if 'Successfully' in out or 'Changed' in out or 'Filled' in out or 'Set the block' in out:
            ok += 1
        else:
            fail += 1
            print(f"  FAIL: {c[:60]} -> {out[:80]}")
print(f"\n result: {ok}/{ok+fail} OK")
