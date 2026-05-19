#!/usr/bin/env python3
"""building_dsl.py — 建筑 DSL 固化 (陆远 17:06 verdict)
节奏: 参考图拆解 → 比例框架 → 结构模板 → 材质分层 → 自动取景 → 评分
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel_dsl import VoxelBuilder

# === 1. 参考图拆解 (Reference) ===
class Reference:
    """从真实建筑 lookup 比例 + 材质分层"""
    PRESETS = {
        'louvre': dict(
            real_dim_m=(135, 27, 65),  # 长 135m, 高 27m, 宽 65m (真实卢浮宫)
            pei_pyramid_m=(35, 22, 35),  # Pei 真实 35m 底, 22m 高
            facade_rhythm=4,  # 立面节奏: 每 4 块 1 柱
            palette={'main':'sandstone','trim':'cut_sandstone','deco':'chiseled_sandstone',
                     'pillar':'smooth_quartz_block','roof':'dark_oak_planks',
                     'roof_edge':'dark_oak_stairs','floor':'light_gray_concrete',
                     'centerpiece':'glass','iron_frame':'iron_block','accent':'gold_block'},
        ),
        'temple': dict(
            real_dim_m=(40, 25, 40),
            facade_rhythm=3,
            palette={'main':'dark_oak_log','trim':'red_concrete','deco':'gold_block',
                     'pillar':'red_concrete','roof':'red_glazed_terracotta',
                     'roof_edge':'red_glazed_terracotta','floor':'oak_planks',
                     'centerpiece':'gold_block','iron_frame':'oak_log','accent':'gold_block'},
        ),
        'skyscraper': dict(
            real_dim_m=(20, 80, 20),
            facade_rhythm=2,
            palette={'main':'light_gray_concrete','trim':'gray_concrete','deco':'tinted_glass',
                     'pillar':'iron_block','roof':'iron_block','roof_edge':'gray_concrete_powder',
                     'floor':'polished_andesite','centerpiece':'beacon','iron_frame':'iron_bars','accent':'redstone_lamp[lit=true]'},
        ),
    }
    @classmethod
    def get(cls, name): return cls.PRESETS.get(name, cls.PRESETS['louvre'])

# === 2. 比例框架 (ProportionFrame) ===
class ProportionFrame:
    """1 块 = 1m, 给定 real_dim → block bbox"""
    @staticmethod
    def from_real(real_dim_m, scale=1.0):
        return tuple(max(3, int(d * scale)) for d in real_dim_m)

# === 3. 结构模板 (StructureTemplate) ===
class StructureTemplate:
    @staticmethod
    def facade(b, ox, oy, oz, length, height, depth, palette, rhythm=4, dir_z=-1):
        """立面墙 + 节奏柱 + 雕花腰带"""
        half_l = length // 2
        # 主墙
        b.box(-half_l, oy, dir_z*depth, half_l, oy+height-1, dir_z*depth, palette['main'], mirror=False)
        # 节奏柱
        for x in range(-half_l, half_l+1, rhythm):
            b.box(x, oy, dir_z*depth, x, oy+height-1, dir_z*depth, palette['pillar'], mirror=False)
            b.set(x, oy+height, dir_z*depth, palette['trim'], mirror=False)  # 柱头
        # 横腰带 (中部)
        for x in range(-half_l, half_l+1):
            b.set(x, oy+height//2, dir_z*depth, palette['trim'], mirror=False)
        # 装饰浮雕 (每节奏 1 个)
        for x in range(-half_l, half_l+1, rhythm):
            b.set(x, oy + height - 2, dir_z*depth - dir_z, palette['deco'], mirror=False)
    @staticmethod
    def colonnade(b, ox, oy, oz, length, height, side_x, palette):
        """侧翼柱廊"""
        for cz in range(-length//2, length//2 + 1, 3):
            b.box(side_x, oy, cz, side_x, oy+height-1, cz, palette['pillar'], mirror=False)
            b.set(side_x, oy+height, cz, palette['trim'], mirror=False)
    @staticmethod
    def pyramid_glass(b, cx, cy, cz, base_size, height, palette):
        """Pei 玻璃金字塔 + iron 棱"""
        for lvl in range(height):
            s = (base_size // 2) - lvl
            if s <= 0: break
            for dx in range(-s, s+1):
                for dz in range(-s, s+1):
                    if abs(dx)==s or abs(dz)==s:
                        b.set(cx+dx, cy+lvl, cz+dz, palette['centerpiece'], mirror=False)
            # 4 主棱
            for sx,sz in [(s,s),(-s,s),(s,-s),(-s,-s)]:
                b.set(cx+sx, cy+lvl, cz+sz, palette['iron_frame'], mirror=False)
            # 4 边中棱
            for sx,sz in [(s,0),(-s,0),(0,s),(0,-s)]:
                b.set(cx+sx, cy+lvl, cz+sz, palette['iron_frame'], mirror=False)
        # 顶尖
        b.set(cx, cy+height, cz, palette['accent'], mirror=False)
    @staticmethod
    def roof_dome(b, ox, oy, oz, length, palette):
        """屋顶 stairs 圆弧 dome"""
        half = length // 2
        for dx in range(-half, half+1):
            b.set(dx, oy+1, oz, f"{palette['roof_edge']}[facing=south,half=bottom]", mirror=False)
            b.set(dx, oy+1, oz-1, f"{palette['roof_edge']}[facing=north,half=bottom]", mirror=False)
            b.set(dx, oy+2, oz, palette['roof'], mirror=False)

# === 4. 材质分层 (LayerMaterial) ===
# 在 StructureTemplate 已用 palette[main/trim/deco/pillar/roof] 分层

# === 5. 自动取景 (AutoFramer) — 已在 voxel_dsl.auto_framing ===

# === 6. 评分: 在 quality_gate.py ===

def build_louvre_v3(origin, scale=0.4):
    """用 building_dsl 重建 louvre v3"""
    ref = Reference.get('louvre')
    palette = ref['palette']
    L, H, W = ProportionFrame.from_real(ref['real_dim_m'], scale)
    pyr_L, pyr_H, _ = ProportionFrame.from_real(ref['pei_pyramid_m'], scale)
    print(f"  louvre dim (blocks): {L}x{H}x{W}, pyramid: {pyr_L}x{pyr_H}")

    b = VoxelBuilder(origin, mirror_axis='x')
    ox, oy, oz = origin

    # 庭院地板
    b.box(-L//2, 0, -W//2, L//2, 0, W//2, palette['floor'], mirror=False)
    # 北翼立面
    StructureTemplate.facade(b, ox, 1, oz, L, H, W//2, palette, rhythm=ref['facade_rhythm'], dir_z=-1)
    # 东西翼柱廊
    StructureTemplate.colonnade(b, ox, 1, oz, W, H, L//2, palette)
    StructureTemplate.colonnade(b, ox, 1, oz, W, H, -L//2, palette)
    # Pei 中央
    StructureTemplate.pyramid_glass(b, 0, 1, 0, pyr_L, pyr_H, palette)
    # 屋顶 dome
    StructureTemplate.roof_dome(b, ox, H, oz, L, palette)

    return b, dict(L=L, H=H, W=W, pyr_L=pyr_L, pyr_H=pyr_H)


if __name__ == '__main__':
    from mcrcon import MCRcon
    import time, glob
    # 探地面
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        for y in range(120, 50, -1):
            o = r.command(f'execute if block -260 {y} -260 air').strip()
            if 'Test passed' not in o:
                gy = y; break
        else: gy = 80
    ORIGIN = (-260, gy+1, -260)
    print(f"louvre v3 origin {ORIGIN}")
    b, dim = build_louvre_v3(ORIGIN, scale=0.4)
    cmds = b.to_commands()
    bbox = b.bbox()
    print(f"v3 cmds={len(cmds)} bbox={bbox}")
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        r.command('gamerule commandModificationBlockLimit 200000')
        for sx in range(-30, 35, 25):
            for sz in range(-30, 35, 25):
                r.command(f'fill {ORIGIN[0]+sx-12} {ORIGIN[1]} {ORIGIN[2]+sz-12} {ORIGIN[0]+sx+12} {ORIGIN[1]+30} {ORIGIN[2]+sz+12} air')
        ok=fail=0
        for c in cmds:
            o = r.command(c)
            if any(k in o for k in ['Successfully','Changed','Set the block']): ok+=1
            else: fail+=1
    print(f"v3 rcon: {ok}/{ok+fail}")
    ts = time.strftime('%Y%m%d-%H%M%S')
    outdir = os.path.expanduser(f'~/mcstory/outputs/louvre_v3_{ts}')
    os.makedirs(outdir, exist_ok=True)
    json.dump({'origin':ORIGIN,'cmds':len(cmds),'bbox':list(bbox),'dim':dim,'rcon_ok':ok,'rcon_total':ok+fail,
               'tech':['Reference.louvre','ProportionFrame.from_real (scale 0.4)','StructureTemplate.facade/colonnade/pyramid/roof_dome','材质分层 palette']},
               open(f'{outdir}/build.json','w'), ensure_ascii=False, indent=2)
    print(f"outdir: {outdir}")
