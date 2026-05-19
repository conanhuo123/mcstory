#!/usr/bin/env python3
"""voxel_dsl.py — 体素建模 DSL: mirror/layer/box/sphere/line + auto framing + frame audit
不抄外观, 学技术: 对称生成 / 分层装甲 / 比例约束 / 自动取景 / 截图自检.
"""
import sys, json, time, re, os, math
from typing import List, Tuple

class VoxelBuilder:
    """DSL: 累积 (x,y,z,block) 集合, 最后输出 fill/setblock 优化命令."""
    def __init__(self, origin, mirror_axis='x'):
        self.ox, self.oy, self.oz = origin
        self.blocks = {}  # (x,y,z) -> block_name
        self.mirror_axis = mirror_axis  # 'x' 沿 x 镜像 (左右对称)

    def set(self, x, y, z, block, mirror=True):
        """放一块. mirror=True 自动沿 mirror_axis 添镜像块"""
        key = (self.ox + x, self.oy + y, self.oz + z)
        self.blocks[key] = block
        if mirror and x != 0:  # 中线不镜像
            if self.mirror_axis == 'x':
                self.blocks[(self.ox - x, self.oy + y, self.oz + z)] = block

    def box(self, x1, y1, z1, x2, y2, z2, block, mirror=True):
        """填充 box (相对 origin), 自动镜像."""
        for x in range(min(x1,x2), max(x1,x2)+1):
            for y in range(min(y1,y2), max(y1,y2)+1):
                for z in range(min(z1,z2), max(z1,z2)+1):
                    self.set(x, y, z, block, mirror=mirror)

    def hollow_box(self, x1, y1, z1, x2, y2, z2, block, mirror=True):
        """空心 box (只外壳)"""
        xs, ys, zs = sorted([x1,x2]), sorted([y1,y2]), sorted([z1,z2])
        for x in range(xs[0], xs[1]+1):
            for y in range(ys[0], ys[1]+1):
                for z in range(zs[0], zs[1]+1):
                    if x in xs or y in ys or z in zs:
                        self.set(x,y,z, block, mirror=mirror)

    def line(self, x1, y1, z1, x2, y2, z2, block, mirror=True):
        """Bresenham 3D 线"""
        dx, dy, dz = x2-x1, y2-y1, z2-z1
        steps = max(abs(dx), abs(dy), abs(dz), 1)
        for i in range(steps + 1):
            t = i / steps
            self.set(round(x1+dx*t), round(y1+dy*t), round(z1+dz*t), block, mirror=mirror)

    def sphere(self, cx, cy, cz, r, block, mirror=True, shell=False):
        """半径 r 球. shell=True 只外壳"""
        for x in range(cx-r, cx+r+1):
            for y in range(cy-r, cy+r+1):
                for z in range(cz-r, cz+r+1):
                    d = math.sqrt((x-cx)**2 + (y-cy)**2 + (z-cz)**2)
                    if (shell and r-1 < d <= r) or (not shell and d <= r):
                        self.set(x,y,z, block, mirror=mirror)

    def cylinder(self, cx, cy1, cz, cy2, r, block, axis='y', mirror=True):
        """沿 axis 的柱"""
        for y in range(min(cy1,cy2), max(cy1,cy2)+1):
            for dx in range(-r, r+1):
                for dz in range(-r, r+1):
                    if dx*dx + dz*dz <= r*r:
                        self.set(cx+dx, y, cz+dz, block, mirror=mirror)

    def to_commands(self):
        """输出 setblock 命令 (每块一条, 简单稳定)"""
        cmds = []
        for (x,y,z), blk in sorted(self.blocks.items()):
            cmds.append(f"setblock {x} {y} {z} {blk}")
        return cmds

    def bbox(self):
        """bbox: (x_min,y_min,z_min, x_max,y_max,z_max)"""
        if not self.blocks: return None
        xs = [k[0] for k in self.blocks]; ys = [k[1] for k in self.blocks]; zs = [k[2] for k in self.blocks]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def auto_framing(bbox, view_angle='front'):
    """给定 bbox, 算 cam 位置 + look point. 保证物体填满画面 60-70%."""
    x1,y1,z1, x2,y2,z2 = bbox
    cx, cy, cz = (x1+x2)/2, (y1+y2)/2, (z1+z2)/2
    h = y2 - y1 + 1; w = x2 - x1 + 1; d = z2 - z1 + 1
    diag = math.sqrt(h*h + max(w,d)**2)
    # 距离: 60° fov 下, dist = max(w,h)/(2 * tan(30°)) * 1.4 (留 30% padding)
    dist = max(w, h) / (2 * math.tan(math.radians(30))) * 1.4
    if view_angle == 'front':
        cam = (cx, cy, cz - dist)
    elif view_angle == '45':
        cam = (cx + dist * 0.707, cy + h * 0.3, cz - dist * 0.707)
    elif view_angle == 'close':
        cam = (cx, cy + h * 0.2, cz - dist * 0.5)
    elif view_angle == 'top':
        cam = (cx, cy + dist, cz)
    look = (cx, cy, cz)
    return cam, look


# === 应用 1: 可识别机甲胸像 (RX-78 风, 300+ blocks via 镜像 + 分层) ===
def build_mecha_bust(origin):
    """胸像 = 头+颈+上半身. 强调头部精细 / 分层装甲 / 双肩 3x3."""
    b = VoxelBuilder(origin, mirror_axis='x')
    # 清场 + 草地
    # 注: 清场用单独 fill 命令 (DSL 外)

    # === 躯干主装甲 (蓝色 lapis) ===
    # 主胸甲 ±3 wide × 6 high × ±1 deep
    b.box(0, 0, -1, 3, 6, 1, 'lapis_block', mirror=True)

    # === 胸前 V 装饰 (红 + accent) ===
    b.set(0, 4, -2, 'red_concrete')
    b.set(0, 3, -2, 'red_concrete')
    b.box(1, 5, -2, 2, 5, -2, 'red_concrete', mirror=True)
    b.set(0, 2, -2, 'yellow_concrete')  # 中央点缀

    # === 散热口 chest vents (黑色细条) ===
    b.set(2, 5, -2, 'deepslate')
    b.set(2, 4, -2, 'deepslate')
    b.set(3, 5, -1, 'deepslate')
    b.set(3, 4, -1, 'deepslate')

    # === 双肩护甲 3x3 多层 (white + accent edge) ===
    b.box(4, 5, -1, 4, 6, 1, 'quartz_block', mirror=True)  # 肩主块
    b.box(5, 6, 0, 5, 6, 0, 'iron_block', mirror=True)     # 肩顶尖
    b.set(4, 7, 0, 'red_concrete', mirror=True)            # 肩饰红
    b.set(5, 5, -1, 'lapis_block', mirror=True)            # 肩前蓝边

    # === 双臂上节 (悬挂) ===
    b.box(4, 1, 0, 4, 4, 0, 'quartz_block', mirror=True)
    b.set(4, 0, 0, 'lapis_block', mirror=True)  # 臂底蓝

    # === 颈部 ===
    b.box(0, 7, -1, 1, 7, 0, 'gray_concrete', mirror=True)  # 颈基
    b.set(0, 8, 0, 'quartz_block')  # 颈轴

    # === 头部主体 ===
    # 头骨 3x3x3 (y=9-11)
    b.box(0, 9, -1, 2, 11, 1, 'quartz_block', mirror=True)

    # === 头部细节 ===
    # 面罩黑 (前)
    b.box(0, 10, -2, 1, 10, -2, 'black_concrete', mirror=True)
    # 双眼黄 (亮)
    b.set(1, 10, -2, 'glowstone', mirror=True)
    b.set(2, 10, -2, 'redstone_lamp[lit=true]', mirror=True)
    # 下巴/颚 (灰)
    b.box(0, 9, -2, 1, 9, -2, 'gray_concrete', mirror=True)
    # 额头红 V
    b.box(0, 11, -2, 1, 11, -2, 'red_concrete', mirror=True)
    # 耳侧装甲 (圆筒, accent)
    b.set(3, 10, 0, 'iron_block', mirror=True)
    b.set(3, 10, 1, 'iron_block', mirror=True)

    # === V-fin 天线 (3 层精细) ===
    # 根部 (yellow)
    b.set(1, 12, 0, 'yellow_concrete', mirror=True)
    # 中节
    b.set(2, 13, 0, 'yellow_concrete', mirror=True)
    # 顶尖
    b.set(3, 14, 0, 'yellow_concrete', mirror=True)
    # 中央方头饰
    b.set(0, 12, 0, 'red_concrete')
    b.set(0, 13, 0, 'gold_block')

    # === 装甲细节: 颈环 (黑色细条围一周) ===
    b.set(0, 8, -1, 'deepslate')
    b.set(1, 8, 0, 'deepslate', mirror=True)

    # === 胸口中央指示器 (玻璃 + 染色玻璃) ===
    b.set(0, 5, -2, 'green_stained_glass')

    # === 装甲层: 腰带 (深色边缘) ===
    b.box(0, 0, -1, 3, 0, 1, 'gray_concrete', mirror=True)

    return b


if __name__ == '__main__':
    # 测试 build mecha bust
    from mcrcon import MCRcon
    ORIGIN = (-130, 80, -300)

    print("[voxel] building mecha bust ...")
    b = build_mecha_bust(ORIGIN)
    cmds = b.to_commands()
    print(f"[voxel] {len(cmds)} block-level commands")
    bbox = b.bbox()
    print(f"[voxel] bbox: {bbox}")
    cam_front, look = auto_framing(bbox, 'front')
    cam_close, _ = auto_framing(bbox, 'close')
    print(f"[voxel] front cam: {cam_front} look {look}")
    print(f"[voxel] close cam: {cam_close} look {look}")

    # 清场 + 跑
    with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
        ox, oy, oz = ORIGIN
        r.command(f"fill {ox-10} {oy-1} {oz-10} {ox+10} {oy+18} {oz+10} air")
        r.command(f"fill {ox-7} {oy-1} {oz-7} {ox+7} {oy-1} {oz+7} grass_block")
        ok = fail = 0
        for c in cmds:
            out = r.command(c)
            if any(k in out for k in ['Successfully','Changed','Set the block']):
                ok += 1
            else:
                fail += 1
        print(f"[voxel] RCON: {ok}/{ok+fail}")

    # 落 metadata
    ts = time.strftime('%Y%m%d-%H%M%S')
    outdir = os.path.expanduser(f'~/mcstory/outputs/mecha_bust_v2_{ts}')
    os.makedirs(outdir, exist_ok=True)
    json.dump({
        'origin': ORIGIN, 'block_count': len(cmds),
        'bbox': list(bbox),
        'cam_front': list(cam_front), 'cam_close': list(cam_close),
        'look': list(look),
        'tech': ['voxel DSL', 'mirror_axis=x', 'layered armor', 'auto framing'],
        'rcon_ok': ok, 'rcon_total': ok+fail,
    }, open(f'{outdir}/build.json','w'), ensure_ascii=False, indent=2)
    print(f"[voxel] meta saved: {outdir}/build.json")
