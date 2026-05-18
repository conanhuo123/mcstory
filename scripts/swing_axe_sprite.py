#!/usr/bin/env python3
"""swing_axe_sprite.py — 举斧 before/after sprite, 几何严格绑定 ArmorStand Pose.RightArm"""
import os, math, json, time
from PIL import Image, ImageDraw, ImageFont
from mcrcon import MCRcon

OUT = '/Users/coco/mcstory/outputs/single_action_check'
os.makedirs(OUT, exist_ok=True)

def render_swing(arm_deg, label, out_path, pose_raw):
    W, H = 720, 900
    img = Image.new('RGB', (W, H), (165, 200, 220))
    d = ImageDraw.Draw(img)
    try:
        f_title = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 32)
        f_meta = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 20)
        f_mono = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 14)
    except:
        f_title = ImageFont.load_default(); f_meta=f_title; f_mono=f_title
    d.rectangle([0,0,W,80], fill=(20,30,50))
    d.text((30,18), label, fill=(255,255,255), font=f_title)
    d.text((30,52), f"ArmorStand Pose.RightArm.x = {arm_deg}°", fill=(160,230,160), font=f_meta)
    # 地面
    for y in range(H-160, H, 3):
        c = (90 + (y%30)//3*8, 160, 90)
        d.rectangle([0,y,W,y+3], fill=c)
    # ArmorStand 身体 (深灰长方体)
    cx = W//2; body_top=480; body_bottom=720; body_w=110
    d.rectangle([cx-body_w//2, body_top, cx+body_w//2, body_bottom], fill=(80,80,90), outline=(40,40,50), width=3)
    # 头 (灰色方块)
    d.rectangle([cx-60, body_top-120, cx+60, body_top-10], fill=(120,120,130), outline=(40,40,50), width=3)
    d.rectangle([cx-30, body_top-90, cx-15, body_top-75], fill=(20,20,20))
    d.rectangle([cx+15, body_top-90, cx+30, body_top-75], fill=(20,20,20))
    # 左手 (固定下垂)
    d.rectangle([cx-body_w//2-22, body_top+10, cx-body_w//2, body_top+150], fill=(80,80,90), outline=(40,40,50), width=2)
    # 右手 (旋转 arm_deg 度, MC Pose.x 是 pitch, -90=向前抬)
    rad = math.radians(arm_deg)  # arm_deg=0: 垂下, -90: 向前/向上举
    shoulder_x = cx + body_w//2
    shoulder_y = body_top + 20
    arm_len = 140
    # arm rotation: x-axis (pitch) — 在矢面内旋转, arm_deg=0 朝下, arm_deg=-90 朝前
    arm_tip_x = shoulder_x + arm_len * math.sin(-rad) * 1.0  # 朝前 (+x)
    arm_tip_y = shoulder_y + arm_len * math.cos(-rad)  # 0 时朝下
    # 把手臂画成 4 角矩形
    arm_w = 22
    perp_x = arm_w * math.cos(-rad) * 0.5
    perp_y = -arm_w * math.sin(-rad) * 0.5
    p1 = (shoulder_x - perp_x, shoulder_y - perp_y)
    p2 = (shoulder_x + perp_x, shoulder_y + perp_y)
    p3 = (arm_tip_x + perp_x, arm_tip_y + perp_y)
    p4 = (arm_tip_x - perp_x, arm_tip_y - perp_y)
    d.polygon([p1,p2,p3,p4], fill=(85,85,95), outline=(30,30,40))
    # 手心 (圆)
    d.ellipse([arm_tip_x-14, arm_tip_y-14, arm_tip_x+14, arm_tip_y+14], fill=(200,170,140), outline=(40,40,50))
    # 铁斧 — 长方形柄 + 三角刃, 放在手心 + arm 方向延伸
    if arm_deg < -10:  # 举起时显示斧扬起
        axe_dx = math.sin(-rad) * 50
        axe_dy = math.cos(-rad) * 50
        # 柄
        d.line([arm_tip_x, arm_tip_y, arm_tip_x+axe_dx, arm_tip_y+axe_dy], fill=(140,90,50), width=8)
        # 刃 (三角铁色)
        head_x = arm_tip_x + axe_dx
        head_y = arm_tip_y + axe_dy
        perp_axe_x = math.cos(-rad) * 40
        perp_axe_y = -math.sin(-rad) * 40
        d.polygon([(head_x, head_y),
                   (head_x + perp_axe_x*0.5 + axe_dx*0.4, head_y + perp_axe_y*0.5 + axe_dy*0.4),
                   (head_x - perp_axe_x*0.5 + axe_dx*0.4, head_y - perp_axe_y*0.5 + axe_dy*0.4)],
                   fill=(220,220,230), outline=(40,40,50))
    else:  # 垂下时, 斧柄垂直下挂
        d.line([arm_tip_x, arm_tip_y+5, arm_tip_x, arm_tip_y+55], fill=(140,90,50), width=8)
        d.polygon([(arm_tip_x, arm_tip_y+60),
                   (arm_tip_x+30, arm_tip_y+60),
                   (arm_tip_x+30, arm_tip_y+100),
                   (arm_tip_x-10, arm_tip_y+95)], fill=(220,220,230), outline=(40,40,50))
    # 状态条
    d.rectangle([0,H-50,W,H], fill=(30,40,60))
    d.text((20,H-32), f"RCON raw: {pose_raw[:80]}", fill=(180,200,220), font=f_mono)
    img.save(out_path)

with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
    r.command("kill @e[type=armor_stand,tag=axswing]")
    r.command(f"summon armor_stand -37 80 -240 {{ShowArms:1b,NoBasePlate:1b,Invulnerable:1b,Tags:[\"axswing\"],HandItems:[{{id:\"minecraft:iron_axe\",Count:1b}},{{}}],Pose:{{RightArm:[0f,0f,0f]}},CustomName:'{{\"text\":\"executioner\"}}',CustomNameVisible:1b}}")
    time.sleep(0.4)
    pose_t0 = r.command("data get entity @e[type=armor_stand,tag=axswing,limit=1] Pose").strip()
    render_swing(0, "BEFORE — executioner arm rest", f"{OUT}/SPRITE_swing_before.png", pose_t0)
    r.command("data merge entity @e[type=armor_stand,tag=axswing,limit=1] {Pose:{RightArm:[-90f,0f,0f]}}")
    time.sleep(0.4)
    pose_t1 = r.command("data get entity @e[type=armor_stand,tag=axswing,limit=1] Pose").strip()
    render_swing(-90, "AFTER — executioner arm raised", f"{OUT}/SPRITE_swing_after.png", pose_t1)

# 拼 side-by-side
from PIL import Image as PI
b = PI.open(f'{OUT}/SPRITE_swing_before.png'); a = PI.open(f'{OUT}/SPRITE_swing_after.png')
m = PI.new('RGB', (b.width + a.width + 20, b.height), (10,14,24))
m.paste(b,(0,0)); m.paste(a,(b.width+20,0))
m.save(f'{OUT}/SPRITE_swing_compare.png')
print('[SAVED]', f'{OUT}/SPRITE_swing_compare.png')
print('pose_t0:', pose_t0[:100])
print('pose_t1:', pose_t1[:100])
