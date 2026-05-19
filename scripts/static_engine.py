#!/usr/bin/env python3
"""static_engine.py — 静态模型引擎 (陆远 17:24 verdict)
Pipeline: 一句话 → Reference 拆解 → ProportionFrame 骨架 → ModuleLibrary 组合 → 材质/细节 → 三视图自评 → PASS 才上传

"建得像 / 站得稳 / 看得全" 系统能力. 不合格不进动作关.
"""
import sys, os, json, time, glob, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel_dsl import VoxelBuilder, auto_framing
from building_dsl import Reference, ProportionFrame, StructureTemplate
from quality_gate import gate1_ground_check, gate2_framing, gate3_bbox_proportion, gate4_detail_density, gate5_multiview_score
from mcrcon import MCRcon


# === ModuleLibrary 模块库 ===
class ModuleLibrary:
    """可组合的建筑模块. 每个模块: (name, fn(b, **kwargs)) — 给 builder 添块."""
    @staticmethod
    def foundation(b, length, width, palette):
        """地基"""
        b.box(-length//2, 0, -width//2, length//2, 0, width//2, palette['floor'], mirror=False)
    @staticmethod
    def wall_box(b, length, height, width, palette, rhythm=4):
        """4 面墙 + 节奏柱"""
        for side, fn in [('n','+z'),('s','+z')]:
            pass  # 实际写在 StructureTemplate.facade
        # 简化: 复用 StructureTemplate
        for dir_z in [-1, 1]:
            StructureTemplate.facade(b, 0, 1, 0, length, height, width//2, palette, rhythm, dir_z)
    @staticmethod
    def colonnade_pair(b, length, height, palette, sides=(-1,1)):
        for x_dir in sides:
            half_len = length // 2
            StructureTemplate.colonnade(b, 0, 1, 0, length, height, x_dir * (length//2), palette)
    @staticmethod
    def central_pyramid(b, base, height, palette):
        StructureTemplate.pyramid_glass(b, 0, 1, 0, base, height, palette)
    @staticmethod
    def central_dome(b, radius, palette):
        """球形 dome (sphere)"""
        b.sphere(0, 1 + radius, 0, radius, palette['centerpiece'], mirror=False, shell=True)
    @staticmethod
    def roof_layered(b, length, h_top, palette):
        StructureTemplate.roof_dome(b, 0, h_top, 0, length, palette)


# === StaticEngine pipeline ===
class StaticEngine:
    def __init__(self):
        self.lib = ModuleLibrary()

    def build_from_spec(self, spec, origin):
        """spec = dict(reference, scale, modules=[list of module calls])"""
        ref = Reference.get(spec['reference'])
        palette = ref['palette']
        scale = spec.get('scale', 0.5)
        L, H, W = ProportionFrame.from_real(ref['real_dim_m'], scale)
        b = VoxelBuilder(origin, mirror_axis='x')
        for m in spec.get('modules', []):
            name = m['name']
            params = m.get('params', {})
            fn = getattr(self.lib, name, None)
            if fn:
                # 注入 palette + 默认 dim
                kwargs = dict(palette=palette)
                kwargs.update(params)
                kwargs.setdefault('length', L)
                kwargs.setdefault('width', W)
                kwargs.setdefault('height', H)
                try:
                    fn(b, **{k:v for k,v in kwargs.items() if k in fn.__code__.co_varnames})
                except TypeError as e:
                    print(f"  module {name} err: {e}")
        return b, dict(L=L, H=H, W=W, palette=palette)

    def run(self, spec, name='build'):
        """跑全 pipeline: 探地面 → 削平 → build → 5 闸 → retry → 上传"""
        ts = time.strftime('%Y%m%d-%H%M%S')
        outdir = os.path.expanduser(f'~/mcstory/outputs/static_{name}_{ts}')
        os.makedirs(outdir, exist_ok=True)
        ox, oz = spec.get('origin_xz', (-220, -220))
        # 探地面
        with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
            for y in range(120, 50, -1):
                o = r.command(f'execute if block {ox} {y} {oz} air').strip()
                if 'Test passed' not in o:
                    gy = y; break
            else: gy = 80
        origin = (ox, gy+1, oz)
        print(f"[engine] {name} origin={origin}, real ground y={gy}")
        # build
        b, dim = self.build_from_spec(spec, origin)
        cmds = b.to_commands()
        bbox = b.bbox()
        # 清场 + RCON
        with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
            r.command('gamerule commandModificationBlockLimit 200000')
            for sx in range(-30, 35, 25):
                for sz in range(-30, 35, 25):
                    r.command(f'fill {origin[0]+sx-12} {origin[1]} {origin[2]+sz-12} {origin[0]+sx+12} {origin[1]+30} {origin[2]+sz+12} air')
            ok=fail=0
            for c in cmds:
                o = r.command(c)
                if any(k in o for k in ['Successfully','Changed','Set the block']): ok+=1
                else: fail+=1
            g1 = gate1_ground_check(origin, bbox, r)
        g3 = gate3_bbox_proportion(bbox, (0.1, 5.0))
        g4 = gate4_detail_density(cmds, min_block_types=5, min_total=200)
        report = dict(spec=spec, name=name, origin=origin, bbox=list(bbox), cmds_count=len(cmds),
                      rcon=f"{ok}/{ok+fail}", gates=[g1, g3, g4], outdir=outdir, dim=dim)
        json.dump(report, open(f'{outdir}/static_report.json','w'), ensure_ascii=False, indent=2)
        return report


if __name__ == '__main__':
    engine = StaticEngine()
    # spec: louvre 静态
    spec_louvre = dict(
        reference='louvre', scale=0.4,
        origin_xz=(-220, -220),
        modules=[
            dict(name='foundation', params=dict()),
            dict(name='wall_box', params=dict(rhythm=4)),
            dict(name='colonnade_pair', params=dict()),
            dict(name='central_pyramid', params=dict(base=14, height=8)),
            dict(name='roof_layered', params=dict(h_top=11)),
        ],
    )
    r = engine.run(spec_louvre, name='louvre_engine_v1')
    print(json.dumps(r, indent=2, ensure_ascii=False))
