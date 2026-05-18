#!/usr/bin/env python3
"""gate1_simulate_topdown.py — 真白盒可见:
直接读 GPT JSON 的 build_cmds, 在 Python dict 里 simulate fill/setblock,
然后输出 ASCII 顶视图 + PIL PNG 顶视图.

这等价于 paper world 状态 (因 RCON 已 14/14 验证 build 命令执行成功).
不依赖 viewer/puppeteer/chunk-sync.
"""
import sys, json, re, os
from PIL import Image, ImageDraw, ImageFont

# block → 字符 + 颜色 (RGB)
BLOCK_MAP = {
    'water': ('~', (40, 80, 200)),
    'lava': ('L', (220, 90, 0)),
    'air': ('.', (255, 255, 255)),
    'sand': ('s', (230, 210, 150)),
    'grass_block': ('g', (80, 170, 80)),
    'dirt': ('d', (130, 90, 60)),
    'stone': ('#', (130, 130, 130)),
    'cobblestone': ('#', (120, 120, 120)),
    'stone_bricks': ('#', (140, 140, 140)),
    'polished_blackstone': ('B', (40, 40, 50)),
    'blackstone': ('B', (50, 50, 60)),
    'basalt': ('b', (60, 60, 70)),
    'netherrack': ('r', (140, 40, 40)),
    'obsidian': ('O', (30, 20, 50)),
    'magma_block': ('m', (200, 80, 30)),
    'oak_planks': ('P', (170, 130, 80)),
    'dark_oak_planks': ('P', (90, 60, 40)),
    'spruce_log': ('|', (90, 70, 50)),
    'spruce_planks': ('P', (130, 90, 60)),
    'oak_log': ('|', (130, 100, 70)),
    'white_wool': ('W', (245, 245, 245)),
    'pink_concrete': ('w', (240, 150, 200)),
    'glass': ('+', (200, 230, 255)),
    'iron_bars': ('/', (180, 180, 200)),
    'iron_block': ('I', (220, 220, 230)),
    'chest': ('C', (160, 110, 60)),
    'shulker_box': ('S', (170, 120, 170)),
    'purple_shulker_box': ('S', (140, 80, 170)),
    'sea_lantern': ('*', (240, 240, 200)),
    'dragon_egg': ('E', (40, 20, 60)),
    'dragon_head': ('E', (60, 30, 80)),
    'diamond_block': ('D', (130, 230, 240)),
    'gold_block': ('G', (240, 220, 80)),
    'emerald_block': ('M', (40, 220, 100)),
    'oak_sign': ('T', (170, 130, 80)),
    'sign': ('T', (170, 130, 80)),
    'end_stone': ('e', (220, 220, 170)),
    'purpur_block': ('p', (180, 130, 180)),
    'end_portal_frame': ('Z', (100, 80, 60)),
    'end_portal': ('Z', (10, 10, 20)),
    'prismarine': ('q', (90, 150, 140)),
    'soul_sand': ('u', (90, 70, 60)),
    'soul_lantern': ('*', (140, 200, 220)),
    'cake': ('c', (240, 230, 220)),
    'oak_fence': ('f', (170, 130, 80)),
    'redstone_block': ('R', (220, 30, 30)),
    'redstone_torch': ('t', (220, 50, 50)),
    'piston': ('p', (150, 130, 100)),
    'repeater': ('p', (150, 130, 100)),
    'lodestone': ('l', (180, 180, 200)),
    'sculk': ('k', (20, 30, 40)),
    'sculk_vein': ('k', (30, 40, 50)),
    'sculk_shrieker': ('K', (40, 50, 70)),
    'sculk_sensor': ('K', (40, 50, 70)),
    'nether_brick': ('n', (60, 30, 30)),
    'dark_oak_log': ('|', (60, 40, 30)),
    'cyan_concrete': ('y', (40, 160, 180)),
    'cobblestone': ('#', (120, 120, 120)),
    'cauldron': ('a', (100, 100, 110)),
    'lectern': ('L', (170, 130, 80)),
    'jukebox': ('j', (130, 90, 60)),
    'brewing_stand': ('a', (140, 120, 100)),
    'oak_door': ('o', (170, 130, 80)),
    'lantern': ('*', (220, 200, 100)),
}

def parse_block(name):
    if not name: return 'unknown'
    n = name.replace('minecraft:', '').strip()
    # 去 NBT/block state: oak_sign[rotation=...] 或 chest{Items:...}
    n = re.split(r'[\[\{]', n)[0]
    return n

def simulate(build_cmds):
    """{(x,y,z): block_name}"""
    world = {}
    for cmd in build_cmds:
        cmd = cmd.strip()
        if cmd.startswith('/'): cmd = cmd[1:]
        m = re.match(r'fill\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\S+)', cmd)
        if m:
            x1,y1,z1,x2,y2,z2 = [int(m.group(i)) for i in range(1,7)]
            blk = parse_block(m.group(7))
            xs = range(min(x1,x2), max(x1,x2)+1)
            ys = range(min(y1,y2), max(y1,y2)+1)
            zs = range(min(z1,z2), max(z1,z2)+1)
            for x in xs:
                for y in ys:
                    for z in zs:
                        world[(x,y,z)] = blk
            continue
        m = re.match(r'setblock\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\S+)', cmd)
        if m:
            x,y,z = int(m.group(1)), int(m.group(2)), int(m.group(3))
            blk = parse_block(m.group(4))
            world[(x,y,z)] = blk
    return world

TRANSPARENT = {'air', 'water'}  # 透视: 不渲染 water/air, 找下方实体
def topdown(world, origin, half=14, y_top=92, y_bottom=78):
    ox, oy, oz = origin
    grid = []
    legend = set()
    for dz in range(-half, half+1):
        row = []
        for dx in range(-half, half+1):
            x, z = ox + dx, oz + dz
            found = None
            for y in range(y_top, y_bottom-1, -1):
                blk = world.get((x,y,z))
                if blk and blk not in TRANSPARENT:
                    found = blk
                    break
            if found:
                ch, _ = BLOCK_MAP.get(found, ('?', (200,0,200)))
                row.append(ch)
                legend.add(found)
            else:
                row.append(' ')
        grid.append(row)
    return grid, legend

def render_png(world, origin, half=14, y_top=92, y_bottom=78, out='topdown.png', label='', spawns=None, shots=None):
    ox, oy, oz = origin
    n = half*2+1
    px = 24  # 每格 24px
    pad = 40
    legend_h = 120
    W = n*px + pad*2
    H = n*px + pad*2 + legend_h
    img = Image.new('RGB', (W, H), (200, 220, 240))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
        f_big = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 18)
    except:
        f = ImageFont.load_default(); f_big = f
    d.text((pad, 8), f"{label}  origin {origin}  (top-down sim from build_cmds)", fill=(20,20,40), font=f_big)
    legend = set()
    for dz in range(-half, half+1):
        for dx in range(-half, half+1):
            x, z = ox + dx, oz + dz
            found = None
            for y in range(y_top, y_bottom-1, -1):
                b = world.get((x,y,z))
                if b and b not in TRANSPARENT:
                    found = b
                    break
            color = (255,255,255)
            if found:
                _, color = BLOCK_MAP.get(found, ('?', (180,0,180)))
                legend.add(found)
            px_x = pad + (dx+half)*px
            px_y = pad + (dz+half)*px
            d.rectangle([px_x, px_y, px_x+px-1, px_y+px-1], fill=color, outline=(180,180,180))
    # 标注 origin
    cx = pad + half*px + px//2
    cy = pad + half*px + px//2
    d.ellipse([cx-5, cy-5, cx+5, cy+5], outline=(220,0,0), width=2)

    # 叠加 character_spawns (关 2 视觉级)
    CHAR_COLOR = {
        'villager': (200, 140, 80), 'iron_golem': (220, 220, 220), 'creeper': (60, 200, 60),
        'steve': (90, 130, 220), 'enderman': (40, 30, 60), 'wolf': (240, 240, 220),
        'warden': (40, 70, 100), 'piglin': (200, 140, 90), 'witch': (130, 70, 130),
        'phantom': (60, 60, 120), 'shulker': (170, 120, 170), 'axolotl': (240, 160, 180),
        'evoker': (160, 140, 120),
    }
    if spawns:
        for sp in spawns:
            actor = sp.get('actor','')
            x, y, z = sp.get('xyz',[0,0,0])
            dx, dz = x - ox, z - oz
            if -half <= dx <= half and -half <= dz <= half:
                px_x = pad + (dx+half)*px + px//2
                px_y = pad + (dz+half)*px + px//2
                color = CHAR_COLOR.get(actor, (220,80,80))
                d.ellipse([px_x-8, px_y-8, px_x+8, px_y+8], fill=color, outline=(0,0,0), width=2)
                d.text((px_x+10, px_y-7), actor[:10], fill=(20,20,20), font=f)
    # 叠加 shots (关 3 视觉级): 简单显示每个 shot 的 camera 偏移点
    if shots:
        for i, s in enumerate(shots):
            cam_type = s.get('camera', 'wide')
            # 用 shot index 表示
            tx = pad + n*px + 10
            ty = pad + i*18
            d.text((tx, ty), f"shot{i}: {cam_type[:14]}", fill=(80,30,150), font=f)
    # legend
    ly = pad + n*px + 16
    lx = pad
    for i, b in enumerate(sorted(legend)):
        ch, color = BLOCK_MAP.get(b, ('?', (180,0,180)))
        d.rectangle([lx, ly, lx+14, ly+14], fill=color, outline=(0,0,0))
        d.text((lx+18, ly-2), f"{b}", fill=(20,20,20), font=f)
        lx += 180
        if lx > W - 200:
            lx = pad; ly += 22
    img.save(out)
    return out

if __name__ == '__main__':
    json_path = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(json_path).replace('.json','')
    out_png = sys.argv[3] if len(sys.argv) > 3 else f'/Users/coco/mcstory/outputs/gate1_acceptance/TOPDOWN_{label}.png'
    out_txt = out_png.replace('.png', '.txt')
    d = json.load(open(json_path))
    origin = d.get('scene_origin') or [-60, 79, -190]
    world = simulate(d['build_cmds'])
    grid, legend = topdown(world, origin)
    lines = [f"# {label} top-down (build_cmds={len(d['build_cmds'])})  origin={origin}"]
    lines.append("")
    for row in grid: lines.append(''.join(row))
    lines.append("")
    lines.append("# legend:")
    for b in sorted(legend):
        ch, _ = BLOCK_MAP.get(b, ('?', (180,0,180)))
        lines.append(f"#   {ch} = {b}")
    open(out_txt, 'w').write('\n'.join(lines))
    render_png(world, origin, out=out_png, label=label,
               spawns=d.get('character_spawns', []),
               shots=d.get('shots', []))
    print(f"[SAVED] {out_txt}")
    print(f"[SAVED] {out_png}")
    print()
    print('\n'.join(lines))
