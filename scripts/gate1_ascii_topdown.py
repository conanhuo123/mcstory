#!/usr/bin/env python3
"""gate1_ascii_topdown.py — 白盒可见 (data-driven, 不依赖 viewer)
对 build 区域 (origin±范围), 从 y_top 往下扫每列, 找第一个非 air 块, 输出 ASCII 顶视图.
"""
import sys, json
from mcrcon import MCRcon

# block → 单字符 (语义聚类)
BLOCK_CHAR = {
    'minecraft:water': '~',
    'minecraft:lava': 'L',
    'minecraft:air': '.',
    'minecraft:sand': 's',
    'minecraft:grass_block': 'g',
    'minecraft:dirt': 'd',
    'minecraft:stone': '#',
    'minecraft:cobblestone': '#',
    'minecraft:stone_bricks': '#',
    'minecraft:polished_blackstone': 'B',
    'minecraft:blackstone': 'B',
    'minecraft:basalt': 'b',
    'minecraft:netherrack': 'r',
    'minecraft:obsidian': 'O',
    'minecraft:magma_block': 'm',
    'minecraft:oak_planks': 'P',
    'minecraft:dark_oak_planks': 'P',
    'minecraft:spruce_log': '|',
    'minecraft:white_wool': 'W',
    'minecraft:glass': '+',
    'minecraft:iron_bars': '/',
    'minecraft:chest': 'C',
    'minecraft:shulker_box': 'S',
    'minecraft:purple_shulker_box': 'S',
    'minecraft:sea_lantern': '*',
    'minecraft:dragon_egg': 'E',
    'minecraft:dragon_head': 'E',
    'minecraft:diamond_block': 'D',
    'minecraft:gold_block': 'G',
    'minecraft:oak_sign': 'T',
    'minecraft:sign': 'T',
}

def char_for(block):
    if not block: return '?'
    if block in BLOCK_CHAR: return BLOCK_CHAR[block]
    # 没映射: 大写首字母
    return block.split(':')[-1][0].upper()

def topdown(origin, half=12, y_top=92, y_bottom=78):
    ox, oy, oz = origin
    grid = []
    legend = set()
    with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
        for dz in range(-half, half+1):
            row = []
            for dx in range(-half, half+1):
                x, z = ox + dx, oz + dz
                found = None
                # 从 y_top 往下扫
                for y in range(y_top, y_bottom-1, -1):
                    # 用 execute if block ... <each common> ... 太慢. 改 data get block 取 block id.
                    # paper 的 'execute if block ... #' 不支持. 用 data get block 取 NBT 但只有 entity 块有 NBT.
                    # 改: execute if block 试 air. 不 match 就猜其他.
                    out = r.command(f"execute if block {x} {y} {z} air").strip()
                    if "Test passed" not in out:
                        # 这格非 air → 试 common block
                        for blk_full in BLOCK_CHAR:
                            blk = blk_full.split(':')[-1]
                            out2 = r.command(f"execute if block {x} {y} {z} {blk}").strip()
                            if "Test passed" in out2:
                                found = blk_full
                                break
                        if found is None: found = 'minecraft:other'
                        break
                row.append(char_for(found) if found else '.')
                if found: legend.add(found)
            grid.append(row)
    return grid, legend

if __name__ == '__main__':
    origin = json.loads(sys.argv[1]) if len(sys.argv) > 1 else [-60, 79, -190]
    label = sys.argv[2] if len(sys.argv) > 2 else 'scene'
    out_path = sys.argv[3] if len(sys.argv) > 3 else f'/Users/coco/mcstory/outputs/gate1_acceptance/ASCII_{label}.txt'
    grid, legend = topdown(origin)
    lines = [f"# ASCII topdown — {label} @ origin {origin}"]
    lines.append(f"# 25x25 顶视图, 从 y=92 向下扫到 y=78 第一个非 air 块")
    lines.append("")
    for row in grid:
        lines.append(''.join(row))
    lines.append("")
    lines.append("# legend:")
    for b in sorted(legend):
        lines.append(f"#   {char_for(b)} = {b}")
    open(out_path, 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    print(f"\n[SAVED] {out_path}")
