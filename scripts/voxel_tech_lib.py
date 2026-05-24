#!/usr/bin/env python3
"""voxel_tech_lib.py — 技术库 (苏白/周朗 11:44 verdict)
6 项可复用参数:
  1. 骨架生成规则 (Rig)
  2. 比例约束 (Proportions)
  3. 装甲分层 (Layered Armor)
  4. 关节连接 (Joints)
  5. 武器挂点 (Mount Points)
  6. 镜头验收 (Frame Audit)
"""
import math, json
from typing import Tuple, Dict, List, Optional
from PIL import Image

# === 1. 骨架生成规则 ===
class Bone:
    def __init__(self, name, parent=None, length=1, axis='y', radius=1):
        self.name, self.parent, self.length, self.axis, self.radius = name, parent, length, axis, radius
        self.origin = (0,0,0)  # 相对 parent 原点

class Rig:
    """humanoid 骨架: pelvis → torso → neck → head
                      pelvis → upper_leg_L/R → lower_leg → foot
                      torso → shoulder_L/R → upper_arm → lower_arm → hand"""
    HUMANOID = {
        'pelvis':       Bone('pelvis', None, 1, 'y'),
        'torso':        Bone('torso', 'pelvis', 4, 'y', 2),
        'neck':         Bone('neck', 'torso', 1, 'y'),
        'head':         Bone('head', 'neck', 3, 'y', 2),
        'shoulder_L':   Bone('shoulder_L', 'torso', 1, 'x'),
        'shoulder_R':   Bone('shoulder_R', 'torso', 1, 'x'),
        'upper_arm_L':  Bone('upper_arm_L', 'shoulder_L', 3, 'y'),
        'upper_arm_R':  Bone('upper_arm_R', 'shoulder_R', 3, 'y'),
        'lower_arm_L':  Bone('lower_arm_L', 'upper_arm_L', 3, 'y'),
        'lower_arm_R':  Bone('lower_arm_R', 'upper_arm_R', 3, 'y'),
        'hand_L':       Bone('hand_L', 'lower_arm_L', 1, 'y'),
        'hand_R':       Bone('hand_R', 'lower_arm_R', 1, 'y'),
        'upper_leg_L':  Bone('upper_leg_L', 'pelvis', 4, 'y'),
        'upper_leg_R':  Bone('upper_leg_R', 'pelvis', 4, 'y'),
        'lower_leg_L':  Bone('lower_leg_L', 'upper_leg_L', 4, 'y'),
        'lower_leg_R':  Bone('lower_leg_R', 'upper_leg_R', 4, 'y'),
        'foot_L':       Bone('foot_L', 'lower_leg_L', 1, 'z'),
        'foot_R':       Bone('foot_R', 'lower_leg_R', 1, 'z'),
    }

# === 2. 比例约束 ===
class Proportions:
    """单位 = head_size (block). 8 头身 = 真实人, 7 = 高达, 5 = SD, 3 = chibi"""
    PRESETS = {
        'realistic_8head':  dict(head=2, neck=0.5, torso=3, arm=3.5, leg=4, hand=0.5, foot=0.5, shoulder_wide=2),
        'gundam_7head':     dict(head=3, neck=1,   torso=5, arm=4,   leg=6, hand=1,   foot=1,   shoulder_wide=3),
        'sd_5head':         dict(head=4, neck=0.5, torso=4, arm=3,   leg=4, hand=1,   foot=1,   shoulder_wide=3),
        'chibi_3head':      dict(head=4, neck=0,   torso=2, arm=2,   leg=2, hand=1,   foot=1,   shoulder_wide=2),
    }
    @classmethod
    def get(cls, name, total_height_blocks):
        """给定 preset name + 目标总高 (blocks), 算每部位真实块数."""
        p = cls.PRESETS[name].copy()
        # head, torso, leg 比例
        unit = total_height_blocks / sum([p['head'], p['neck'], p['torso'], p['leg']])
        for k in p: p[k] = max(1, round(p[k] * unit))
        return p

# === 3. 装甲分层 ===
class LayeredArmor:
    """3 层装甲: base (主装甲, 最厚) / middle (装饰条) / top (尖角/精细)"""
    @staticmethod
    def apply(builder, x, y, z, w, h, d,
              base_block, middle_block=None, top_block=None,
              mirror=True):
        # base
        builder.box(x, y, z, x+w-1, y+h-1, z+d-1, base_block, mirror=mirror)
        # middle 缩 1 块装饰条 (中间高度)
        if middle_block and h >= 3:
            mid_y = y + h // 2
            builder.box(x-1, mid_y, z, x-1, mid_y, z+d-1, middle_block, mirror=mirror)
        # top 上边沿
        if top_block:
            builder.box(x, y+h, z, x+w-1, y+h, z+d-1, top_block, mirror=mirror)

# === 4. 关节连接 ===
class Joint:
    """球关节 / 圆柱关节 / 铰链"""
    @staticmethod
    def ball(builder, cx, cy, cz, r, block, mirror=True):
        """球关节 (sphere)"""
        builder.sphere(cx, cy, cz, r, block, mirror=mirror, shell=False)
    @staticmethod
    def cylinder(builder, cx, cy1, cy2, cz, r, block, mirror=True):
        """圆柱关节 (沿 y)"""
        builder.cylinder(cx, cy1, cz, cy2, r, block, mirror=mirror)
    @staticmethod
    def hinge(builder, x, y, z, length, axis, block, mirror=True):
        """铰链 (沿 axis 的细圆柱)"""
        if axis == 'x':
            for dx in range(length): builder.set(x+dx, y, z, block, mirror=mirror)
        elif axis == 'y':
            for dy in range(length): builder.set(x, y+dy, z, block, mirror=mirror)

# === 5. 武器挂点 ===
class MountPoint:
    """武器/装饰挂点: 给定 anchor + offset + orientation"""
    @staticmethod
    def attach_weapon(builder, anchor_xyz, weapon_type, palette, mirror=False):
        ax, ay, az = anchor_xyz
        if weapon_type == 'beam_saber':
            # 光剑: 持柄 iron + 刃 sea_lantern 上扬
            builder.set(ax, ay, az, palette.get('weapon','iron_block'), mirror=mirror)
            for h in range(1, 6):
                builder.set(ax, ay+h, az, 'sea_lantern', mirror=mirror)
            builder.set(ax, ay+6, az, 'glowstone', mirror=mirror)  # 剑尖
        elif weapon_type == 'beam_rifle':
            # 长枪: iron + glowstone 枪口
            for dz in range(1, 5): builder.set(ax, ay, az-dz, 'gray_concrete', mirror=mirror)
            builder.set(ax, ay, az-5, 'glowstone', mirror=mirror)  # 枪口光
        elif weapon_type == 'shield':
            # 盾: 2x3 装甲
            builder.box(ax, ay-1, az-1, ax, ay+2, az-1, palette.get('weapon','iron_block'), mirror=mirror)
            # 盾面装饰 (cross)
            builder.set(ax, ay+1, az-2, palette.get('accent','red_concrete'), mirror=mirror)
        elif weapon_type == 'monkey_staff':
            # 金箍棒: 7 高斜举, gold + 红环
            for h in range(7):
                builder.set(ax, ay+h, az, palette.get('weapon','gold_block') if h%3 else palette.get('accent','red_concrete'), mirror=mirror)
        elif weapon_type == 'web_shooter':
            # 蛛丝 cobweb 一片
            builder.set(ax, ay, az, palette.get('weapon','iron_block'), mirror=mirror)
            for h in range(1, 5):
                builder.set(ax, ay, az-h, 'cobweb', mirror=mirror)
            builder.set(ax+1, ay, az-2, 'cobweb', mirror=mirror)
        elif weapon_type == 'spear':
            # 长矛: oak_fence 杆 + iron 头
            for h in range(8):
                builder.set(ax, ay+h, az, 'oak_fence', mirror=mirror)
            builder.set(ax, ay+8, az, 'iron_block', mirror=mirror)
        elif weapon_type == 'magic_orb':
            # 魔法球: glowstone + glass
            builder.set(ax, ay, az, palette.get('accent','glowstone'), mirror=mirror)
            builder.set(ax, ay+1, az, 'glass', mirror=mirror)

# === 6. 镜头验收 (Frame Audit) ===
class FrameAudit:
    """截图后 PIL 分析: 物体居中度 / 占画面比例 / 边缘 padding"""
    @staticmethod
    def audit(png_path, bg_color=(135, 206, 235)):
        """背景色 bg_color (sky/grass) 之外的像素 = 物体"""
        img = Image.open(png_path).convert('RGB')
        W, H = img.size
        pixels = list(img.getdata())
        obj_mask = []
        bg_r, bg_g, bg_b = bg_color
        for i, (r,g,b) in enumerate(pixels):
            # tolerance 50
            is_bg = (abs(r-bg_r) < 60 and abs(g-bg_g) < 60 and abs(b-bg_b) < 60)
            obj_mask.append(not is_bg)
        if not any(obj_mask):
            return {'object_present': False, 'verdict': 'FAIL_NO_OBJECT'}
        # bbox of object
        xs, ys = [], []
        for i, m in enumerate(obj_mask):
            if m:
                xs.append(i % W); ys.append(i // W)
        x1, x2 = min(xs), max(xs); y1, y2 = min(ys), max(ys)
        obj_w, obj_h = x2-x1+1, y2-y1+1
        obj_area = sum(obj_mask)
        frame_area = W * H
        obj_ratio = obj_area / frame_area
        # 居中度: bbox 中心 vs 画面中心
        cx, cy = (x1+x2)/2, (y1+y2)/2
        off_x = abs(cx - W/2) / (W/2)
        off_y = abs(cy - H/2) / (H/2)
        # 边缘 padding
        pad_left = x1 / W; pad_right = (W-x2) / W
        pad_top = y1 / H; pad_bot = (H-y2) / H
        # verdict
        if obj_ratio < 0.05: v = 'FAIL_TOO_SMALL'
        elif obj_ratio > 0.85: v = 'FAIL_TOO_BIG'
        elif off_x > 0.4 or off_y > 0.4: v = 'FAIL_OFF_CENTER'
        elif min(pad_left, pad_right, pad_top, pad_bot) < 0.02: v = 'FAIL_EDGE_CUT'
        else: v = 'PASS'
        return {
            'object_present': True, 'verdict': v,
            'obj_bbox': [x1,y1,x2,y2], 'obj_ratio': round(obj_ratio,3),
            'off_center': [round(off_x,3), round(off_y,3)],
            'padding': dict(left=round(pad_left,3), right=round(pad_right,3),
                            top=round(pad_top,3), bottom=round(pad_bot,3)),
            'image_size': [W, H]
        }


if __name__ == '__main__':
    # demo 1: Proportions
    print("=== Proportions ===")
    for n in ['realistic_8head','gundam_7head','sd_5head','chibi_3head']:
        p = Proportions.get(n, 24)
        print(f"  {n} (h=24): head={p['head']} torso={p['torso']} leg={p['leg']} arm={p['arm']}")

    # demo 2: Frame Audit (audit 之前的 截图)
    import os, glob
    for f in sorted(glob.glob('/Users/coco/mcstory/outputs/mecha_bust_v2_*/bust_*.png'))[:3]:
        result = FrameAudit.audit(f)
        print(f"\n=== Audit {os.path.basename(f)} ===")
        print(json.dumps(result, indent=2))
