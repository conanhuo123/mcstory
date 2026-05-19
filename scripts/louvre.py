#!/usr/bin/env python3
"""louvre.py — 卢浮宫 (Louvre + Pei 金字塔, paper world 真搭)
特征:
  - 中央玻璃金字塔 (透明 + iron 骨架)
  - U 形宫殿环抱 (3 翼: 北/东/西)
  - 法式古典 (sandstone 黄 + smooth_quartz 白 + dark_oak)
  - 柱廊 (柱子 + stairs 拱形)
  - 庭院 (light_gray_concrete 铺地)
  - 喷泉 (水 + sea_lantern 灯)
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel_dsl import VoxelBuilder
from mcrcon import MCRcon

def build_louvre(origin):
    """origin = 庭院中心 (xz). 整体 occupies 50x40x25."""
    ox, oy, oz = origin
    b = VoxelBuilder(origin, mirror_axis='x')

    WALL = 'sandstone'  # 主色法式黄石
    TRIM = 'smooth_quartz_block'  # 白边
    ROOF = 'dark_oak_planks'  # 屋顶深色
    FLOOR = 'light_gray_concrete'
    PYRAMID_GLASS = 'glass'
    PYRAMID_FRAME = 'iron_block'
    FOUNTAIN = 'water'
    LIGHT = 'sea_lantern'

    # === 庭院地面 35x25 ===
    for dx in range(-17, 18):
        for dz in range(-12, 13):
            b.set(dx, 0, dz, FLOOR, mirror=False)

    # === 主宫殿 U 形 (北翼 + 东西翼) ===
    # 北翼 (z=-12): 长 35, 宽 5, 高 12
    # 主墙 (back wall z=-15)
    b.box(-17, 1, -15, 17, 12, -15, WALL, mirror=False)
    # 前墙 (z=-12)
    b.box(-17, 1, -12, 17, 12, -12, WALL, mirror=False)
    # 侧墙 (north 内空)
    for dx in [-17, 17]:
        b.box(dx, 1, -15, dx, 12, -12, WALL, mirror=False)
    # 北翼 屋顶
    b.box(-18, 13, -16, 18, 13, -11, ROOF, mirror=False)
    # 屋顶坡 (stairs 圆收)
    for dx in range(-18, 19):
        b.set(dx, 14, -13, 'dark_oak_stairs[facing=south]', mirror=False)
    for dx in range(-18, 19):
        b.set(dx, 14, -14, 'dark_oak_stairs[facing=north]', mirror=False)

    # === 东西翼 (x=±17, 沿 z=-12 到 z=+12 延伸) ===
    for x_sign in [-1, 1]:
        xs = 17 * x_sign
        # 主墙 (外墙)
        outer_x = xs + (1 * x_sign)
        b.box(outer_x, 1, -12, outer_x, 12, 12, WALL, mirror=False)
        # 内墙 (面对庭院)
        b.box(xs, 1, -10, xs, 12, 12, WALL, mirror=False)
        # 屋顶
        b.box(xs, 13, -12, outer_x, 13, 12, ROOF, mirror=False)
        # 柱廊 (柱子 + stairs)
        for cz in range(-10, 13, 3):
            b.set(xs - x_sign, 1, cz, TRIM, mirror=False)  # 柱基
            b.box(xs - x_sign, 2, cz, xs - x_sign, 10, cz, TRIM, mirror=False)
            b.set(xs - x_sign, 11, cz, TRIM, mirror=False)
            # 柱顶 stairs 拱
            face = 'east' if x_sign < 0 else 'west'
            b.set(xs - x_sign, 11, cz-1, f'{TRIM[:-6]}_stairs[facing={face},half=top]', mirror=False)
            b.set(xs - x_sign, 11, cz+1, f'{TRIM[:-6]}_stairs[facing={face},half=top]', mirror=False)

    # === 中央玻璃金字塔 (Pei) ===
    # 庭院中心 (0, 1, 0), 底 11x11, 顶 1 块, 高 6
    for lvl in range(6):
        size = 5 - lvl  # 5,4,3,2,1,0
        for dx in range(-size, size+1):
            for dz in range(-size, size+1):
                if abs(dx) == size or abs(dz) == size:  # shell
                    b.set(dx, 1 + lvl, dz, PYRAMID_GLASS, mirror=False)
    # 顶尖
    b.set(0, 6, 0, PYRAMID_FRAME, mirror=False)
    # 四条 iron 棱 (底→顶 4 条线)
    for lvl in range(5):
        s = 5 - lvl
        b.set(s, 1+lvl, s, PYRAMID_FRAME, mirror=False)
        b.set(-s, 1+lvl, s, PYRAMID_FRAME, mirror=False)
        b.set(s, 1+lvl, -s, PYRAMID_FRAME, mirror=False)
        b.set(-s, 1+lvl, -s, PYRAMID_FRAME, mirror=False)

    # === 4 个 mini 金字塔 (Pei 卫星) ===
    for px, pz in [(-10, -5), (10, -5), (-10, 5), (10, 5)]:
        for lvl in range(3):
            s = 2 - lvl
            for dx in range(-s, s+1):
                for dz in range(-s, s+1):
                    if abs(dx) == s or abs(dz) == s:
                        b.set(px+dx, 1+lvl, pz+dz, PYRAMID_GLASS, mirror=False)

    # === 庭院两侧喷泉 (圆形水池) ===
    for fx in [-12, 12]:
        # 圆形池 (3 块半径)
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if dx*dx + dz*dz <= 9:
                    b.set(fx+dx, 1, dz, FOUNTAIN, mirror=False)
                if dx*dx + dz*dz == 9:
                    b.set(fx+dx, 1, dz, TRIM, mirror=False)  # 边
        # 中央喷泉雕像 (灯柱)
        b.set(fx, 1, 0, LIGHT, mirror=False)
        b.set(fx, 2, 0, LIGHT, mirror=False)
        b.set(fx, 3, 0, LIGHT, mirror=False)

    # === 北翼大门 (拱形 + 柱) ===
    b.box(-2, 1, -12, 2, 5, -12, 'air', mirror=False)  # 挖门洞 5 wide 5 high
    # 门拱 (top stairs)
    for dx, sf in [(-2,'east'),(2,'west')]:
        b.set(dx, 5, -12, f'sandstone_stairs[facing={sf},half=top]', mirror=False)
    b.set(0, 5, -12, 'sandstone_slab[type=top]', mirror=False)
    # 门 (oak)
    b.set(0, 1, -12, 'oak_door[half=lower,hinge=left]', mirror=False)
    b.set(0, 2, -12, 'oak_door[half=upper,hinge=left]', mirror=False)
    # 门两侧柱
    for dx in [-3, 3]:
        b.box(dx, 1, -12, dx, 12, -12, TRIM, mirror=False)

    # === 墙面雕花 (横向窗 + slabs 装饰) ===
    for dx in range(-15, 16, 3):
        if abs(dx) < 4: continue  # 门附近不挖
        b.set(dx, 3, -12, 'glass_pane', mirror=False)
        b.set(dx, 7, -12, 'glass_pane', mirror=False)

    # === 牌子 ===
    b.set(0, 0, -16, 'oak_sign', mirror=False)

    return b


if __name__ == '__main__':
    ORIGIN = (-300, 80, -300)  # 远离已建建筑 (高达/城堡)
    print(f"[louvre] building @ {ORIGIN}")
    b = build_louvre(ORIGIN)
    cmds = b.to_commands()
    bbox = b.bbox()
    print(f"[louvre] cmds: {len(cmds)}")
    print(f"[louvre] bbox: {bbox}")

    with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
        ox, oy, oz = ORIGIN
        # 清场 + 平整地基
        r.command(f"fill {ox-25} {oy-1} {oz-20} {ox+25} {oy+20} {oz+20} air")
        r.command(f"fill {ox-25} {oy-1} {oz-20} {ox+25} {oy-1} {oz+20} grass_block")
        ok = fail = 0
        for c in cmds:
            out = r.command(c)
            if any(k in out for k in ['Successfully','Changed','Set the block']):
                ok += 1
            else:
                fail += 1
        print(f"[louvre] RCON: {ok}/{ok+fail}")

    ts = time.strftime('%Y%m%d-%H%M%S')
    outdir = os.path.expanduser(f'~/mcstory/outputs/louvre_{ts}')
    os.makedirs(outdir, exist_ok=True)
    json.dump({
        'origin': ORIGIN, 'block_count': len(cmds), 'bbox': list(bbox),
        'rcon_ok': ok, 'rcon_total': ok+fail,
        'features': ['Pei 中央玻璃金字塔', '4 mini 金字塔 (卫星)', 'U 形宫殿 3 翼',
                     '柱廊 (柱+stairs拱)', '法式 sandstone+smooth_quartz 配色',
                     '2 圆形喷泉 + sea_lantern 雕像', '北翼大门拱形', '横向窗+雕花']
    }, open(f'{outdir}/build.json','w'), ensure_ascii=False, indent=2)
    print(f"[louvre] outdir: {outdir}")
