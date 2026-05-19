#!/usr/bin/env python3
"""module_library.py — 静态模板库 4 类 (赵雪/周朗 17:57 verdict)
地基(foundation) / 主体(body) / 装饰(decor) / 取景(framing)
每类含 N 个 reusable module + params
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel_dsl import VoxelBuilder
from building_dsl import StructureTemplate

# === 1. 地基 (Foundation) ===
class Foundation:
    @staticmethod
    def slab(b, length, width, palette, block_key='floor'):
        """平板地基 1 层"""
        b.box(-length//2, 0, -width//2, length//2, 0, width//2, palette.get(block_key,'light_gray_concrete'), mirror=False)
    @staticmethod
    def stepped(b, length, width, palette, steps=3):
        """阶梯地基 (多级台阶)"""
        for i in range(steps):
            d = i + 1
            b.box(-length//2-d, -i, -width//2-d, length//2+d, -i, width//2+d, palette.get('trim','stone'), mirror=False)
    @staticmethod
    def plaza_circle(b, radius, palette):
        """圆形广场"""
        for dx in range(-radius, radius+1):
            for dz in range(-radius, radius+1):
                if dx*dx + dz*dz <= radius*radius:
                    b.set(dx, 0, dz, palette.get('floor','light_gray_concrete'), mirror=False)

# === 2. 主体 (Body) ===
class Body:
    @staticmethod
    def hollow_box(b, length, height, width, palette):
        """4 面墙空心 box"""
        half_l, half_w = length//2, width//2
        # 4 面墙
        for dz in [-half_w, half_w]:
            b.box(-half_l, 1, dz, half_l, height, dz, palette.get('main','sandstone'), mirror=False)
        for dx in [-half_l, half_l]:
            b.box(dx, 1, -half_w, dx, height, half_w, palette.get('main','sandstone'), mirror=False)
    @staticmethod
    def facade_rhythmic(b, length, height, depth, palette, rhythm=4, dir_z=-1):
        """节奏立面 (柱 + 腰带)"""
        StructureTemplate.facade(b, 0, 1, 0, length, height, depth, palette, rhythm, dir_z)
    @staticmethod
    def colonnade_pair(b, length, height, palette):
        """两侧柱廊"""
        StructureTemplate.colonnade(b, 0, 1, 0, length, height, length//2, palette)
        StructureTemplate.colonnade(b, 0, 1, 0, length, height, -length//2, palette)
    @staticmethod
    def central_pyramid(b, base, height, palette):
        """中央金字塔 (玻璃 + 棱)"""
        StructureTemplate.pyramid_glass(b, 0, 1, 0, base, height, palette)
    @staticmethod
    def central_dome(b, radius, palette):
        """中央 dome (球壳)"""
        b.sphere(0, 1+radius, 0, radius, palette.get('centerpiece','glass'), mirror=False, shell=True)
    @staticmethod
    def central_spire(b, base, height, palette):
        """尖塔 (锥形 stairs)"""
        for lvl in range(height):
            r = max(1, base//2 - lvl//2)
            for dx in range(-r, r+1):
                for dz in range(-r, r+1):
                    if abs(dx)==r or abs(dz)==r:
                        b.set(dx, 1+lvl, dz, palette.get('main','quartz_block'), mirror=False)
    @staticmethod
    def tower_layered(b, base, height, layers, palette):
        """多层塔 (e.g. 中国宝塔)"""
        layer_h = max(2, height // layers)
        for layer in range(layers):
            cur_b = max(2, base - layer*2)
            y_base = 1 + layer * layer_h
            for dx in range(-cur_b//2, cur_b//2+1):
                for dz in range(-cur_b//2, cur_b//2+1):
                    if abs(dx)==cur_b//2 or abs(dz)==cur_b//2:
                        b.box(dx, y_base, dz, dx, y_base+layer_h-1, dz, palette.get('main','red_concrete'), mirror=False)
            # 层屋檐
            for dx in range(-cur_b//2-1, cur_b//2+2):
                b.set(dx, y_base+layer_h-1, -cur_b//2-1, palette.get('roof','dark_oak_planks'), mirror=False)
                b.set(dx, y_base+layer_h-1, cur_b//2+1, palette.get('roof','dark_oak_planks'), mirror=False)

# === 3. 装饰 (Decor) ===
class Decor:
    @staticmethod
    def fountain(b, x, z, radius, palette):
        """圆形喷泉 + 灯柱"""
        for dx in range(-radius, radius+1):
            for dz in range(-radius, radius+1):
                if dx*dx + dz*dz <= radius*radius:
                    b.set(x+dx, 1, z+dz, 'water', mirror=False)
                if abs(dx*dx + dz*dz - radius*radius) < 3:
                    b.set(x+dx, 1, z+dz, palette.get('trim','smooth_quartz_block'), mirror=False)
        b.set(x, 2, z, 'sea_lantern', mirror=False)
        b.set(x, 3, z, 'sea_lantern', mirror=False)
        b.set(x, 4, z, palette.get('accent','gold_block'), mirror=False)
    @staticmethod
    def statue_armorstand(rcon, world_x, world_y, world_z, pose='salute'):
        """ArmorStand 雕像 (需 rcon)"""
        if pose == 'salute':
            arm = '[-30f,0f,0f]'
        elif pose == 'point':
            arm = '[-90f,0f,0f]'
        else:
            arm = '[0f,0f,0f]'
        rcon.command(f'summon armor_stand {world_x} {world_y} {world_z} {{ShowArms:1b,NoBasePlate:1b,Invulnerable:1b,Pose:{{RightArm:{arm}}},HandItems:[{{id:torch,Count:1b}},{{}}]}}')
    @staticmethod
    def banner_row(b, y, length, palette, on='north'):
        """旗帜横排"""
        flag_block = palette.get('accent','red_concrete')
        for dx in range(-length//2, length//2+1, 3):
            b.box(dx, y, 0, dx, y+2, 0, flag_block, mirror=False)
    @staticmethod
    def carved_band(b, y, length, palette):
        """雕花腰带 (横绕)"""
        deco = palette.get('deco','chiseled_sandstone')
        for dx in range(-length//2, length//2+1):
            b.set(dx, y, 0, deco, mirror=False)
    @staticmethod
    def torch_perimeter(rcon, ox, oy, oz, length, width, interval=5):
        """灯柱外环"""
        for dx in range(-length//2, length//2+1, interval):
            rcon.command(f'setblock {ox+dx} {oy+1} {oz-width//2} torch')
            rcon.command(f'setblock {ox+dx} {oy+1} {oz+width//2} torch')

# === 4. 取景 (Framing) ===
class Framing:
    @staticmethod
    def front(bbox, fov_deg=70, pad=0.2):
        x1,y1,z1, x2,y2,z2 = bbox
        cx, cy, cz = (x1+x2)/2, (y1+y2)/2, (z1+z2)/2
        h = y2-y1+1; w = max(x2-x1, z2-z1)+1
        dist = max(w, h) / (2 * math.tan(math.radians(fov_deg/2))) * (1 + pad)
        return (cx, cy, cz - dist), (cx, cy, cz)
    @staticmethod
    def side(bbox, fov_deg=70, pad=0.2):
        x1,y1,z1, x2,y2,z2 = bbox
        cx, cy, cz = (x1+x2)/2, (y1+y2)/2, (z1+z2)/2
        h = y2-y1+1; w = x2-x1+1
        dist = max(w, h) / (2 * math.tan(math.radians(fov_deg/2))) * (1 + pad)
        return (cx + dist, cy, cz), (cx, cy, cz)
    @staticmethod
    def top(bbox, fov_deg=70, pad=0.2):
        x1,y1,z1, x2,y2,z2 = bbox
        cx, cy, cz = (x1+x2)/2, (y1+y2)/2, (z1+z2)/2
        l = max(x2-x1, z2-z1)+1
        dist = l / (2 * math.tan(math.radians(fov_deg/2))) * (1 + pad)
        return (cx, cy + dist, cz+1), (cx, cy, cz)
    @staticmethod
    def angle_45(bbox, fov_deg=70, pad=0.2):
        x1,y1,z1, x2,y2,z2 = bbox
        cx, cy, cz = (x1+x2)/2, (y1+y2)/2, (z1+z2)/2
        h = y2-y1+1; w = max(x2-x1, z2-z1)+1
        dist = max(w, h) / (2 * math.tan(math.radians(fov_deg/2))) * (1 + pad)
        return (cx + dist*0.707, cy + h*0.3, cz - dist*0.707), (cx, cy, cz)


if __name__ == '__main__':
    # 自检: print all modules
    for cls in [Foundation, Body, Decor, Framing]:
        print(f"\n=== {cls.__name__} ===")
        for m in dir(cls):
            if not m.startswith('_'):
                fn = getattr(cls, m)
                if callable(fn):
                    sig = fn.__code__.co_varnames[:fn.__code__.co_argcount]
                    print(f"  {m}({', '.join(sig)})")
