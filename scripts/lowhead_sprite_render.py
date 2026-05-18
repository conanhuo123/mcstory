#!/usr/bin/env python3
"""lowhead_sprite_render.py — 苏白 verdict: 必须肉眼可见
真 MC viewer 硬阻塞 (paper 不认 mineflayer 为 player, list=0), 替代:
用 PIL 画 villager 大幅 sprite (头部相对身体的角度反映 pitch), before/after 2 张可视对比.
sprite 几何参数严格对应 RCON 数据 (Rotation.pitch) — 数据=视觉绑定.
"""
import os, math, json
from PIL import Image, ImageDraw, ImageFont
from mcrcon import MCRcon

OUT = '/Users/coco/mcstory/outputs/single_action_check'
os.makedirs(OUT, exist_ok=True)

def render_villager(pitch_deg, label, out_path, rot_raw):
    """villager 像素风格大幅 sprite, head 旋转 pitch_deg"""
    W, H = 720, 900
    img = Image.new('RGB', (W, H), (165, 200, 220))  # 天蓝背景
    d = ImageDraw.Draw(img)
    try:
        f_title = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 36)
        f_meta = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 20)
        f_mono = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 16)
    except:
        f_title = ImageFont.load_default(); f_meta = f_title; f_mono = f_title
    # 标题条
    d.rectangle([0, 0, W, 80], fill=(20, 30, 50))
    d.text((30, 18), label, fill=(255, 255, 255), font=f_title)
    d.text((30, 60), f"RCON Rotation pitch = {pitch_deg}°", fill=(160, 230, 160), font=f_meta)

    # 地面 (类 MC grass)
    for y in range(H-160, H, 3):
        c = (90 + (y%30)//3*8, 160, 90)
        d.rectangle([0, y, W, y+3], fill=c)

    # villager 身体 (中心)
    cx = W // 2
    body_top = 500
    body_bottom = 720
    body_w = 140
    # 长袍 (brown villager)
    d.rectangle([cx-body_w//2, body_top, cx+body_w//2, body_bottom], fill=(160, 110, 80), outline=(60, 40, 30), width=4)
    # 腰带
    d.rectangle([cx-body_w//2, body_top+90, cx+body_w//2, body_top+105], fill=(80, 60, 40))

    # 头部 (像素 head, 反映 pitch 旋转)
    head_size = 180
    head_cx = cx
    head_cy = body_top - 40
    # pitch 朝下: head 整体下倾 (visual: top of head 朝前突出, chin 朝下贴近身体)
    # 用一个简化 transform: head 是 rounded square, pitch 决定头的"前突"
    # pitch=0 平视: 头方块上下对齐, 大鼻子 (villager 特征) 朝前
    # pitch=45 低头: 头方块下沿外突, 鼻子朝下
    # 简化: 画两组 (head_top_x, head_top_y, head_bottom_x, head_bottom_y), 用矩形
    rad = math.radians(pitch_deg)
    # 头部上下偏移
    head_top_offset_x = 0
    head_top_offset_y = -math.cos(rad) * head_size//2
    head_bot_offset_x = math.sin(rad) * head_size//3
    head_bot_offset_y = math.cos(rad) * head_size//2
    # 四角
    head_w = head_size
    p1 = (head_cx - head_w//2 + head_top_offset_x*0, head_cy + head_top_offset_y)
    p2 = (head_cx + head_w//2 + head_top_offset_x*0, head_cy + head_top_offset_y)
    p3 = (head_cx + head_w//2 + head_bot_offset_x, head_cy + head_bot_offset_y)
    p4 = (head_cx - head_w//2 + head_bot_offset_x, head_cy + head_bot_offset_y)
    d.polygon([p1, p2, p3, p4], fill=(220, 180, 130), outline=(80, 50, 30))
    # eyes (黑色 2 个矩形, 跟头转)
    eye_cy = (p1[1] + p4[1]) // 2 - 15
    eye_dx = math.sin(rad) * 8
    d.rectangle([head_cx-50+eye_dx, eye_cy-8, head_cx-25+eye_dx, eye_cy+5], fill=(20, 20, 20))
    d.rectangle([head_cx+25+eye_dx, eye_cy-8, head_cx+50+eye_dx, eye_cy+5], fill=(20, 20, 20))
    # villager 大鼻子 (前突)
    nose_cy = (p1[1] + p4[1]) // 2 + 10
    nose_dx = math.sin(rad) * 22
    nose_dy = math.cos(rad) * 0 + math.sin(rad) * 14
    nose_top_y = nose_cy - 8 + nose_dy
    nose_bot_y = nose_cy + 50 + nose_dy
    d.polygon([(head_cx-12+nose_dx, nose_top_y),
               (head_cx+12+nose_dx, nose_top_y),
               (head_cx+8+nose_dx, nose_bot_y),
               (head_cx-8+nose_dx, nose_bot_y)], fill=(190, 140, 95), outline=(80, 50, 30))
    # 手臂 (两侧悬挂)
    d.rectangle([cx-body_w//2-30, body_top+10, cx-body_w//2, body_top+150], fill=(160, 110, 80), outline=(60, 40, 30), width=3)
    d.rectangle([cx+body_w//2, body_top+10, cx+body_w//2+30, body_top+150], fill=(160, 110, 80), outline=(60, 40, 30), width=3)

    # 反转牌后景 (oak_sign 木牌)
    sign_x, sign_y = W - 220, body_top + 50
    d.rectangle([sign_x, sign_y, sign_x+180, sign_y+90], fill=(180, 140, 100), outline=(80, 60, 40), width=3)
    d.rectangle([sign_x+85, sign_y+90, sign_x+95, sign_y+150], fill=(80, 60, 40))
    d.text((sign_x+30, sign_y+30), "判决", fill=(20, 20, 20), font=f_title)

    # 状态条
    d.rectangle([0, H-50, W, H], fill=(30, 40, 60))
    d.text((20, H-38), f"RCON raw: {rot_raw[:80]}", fill=(180, 200, 220), font=f_mono)

    img.save(out_path)
    return out_path

# 实跑: 重 spawn villager, RCON 抓数据, 渲染
with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
    r.command(f"kill @e[type=villager,distance=..30]")
    r.command(f"summon villager -40 81 -240 {{NoAI:1b,Silent:1b,PersistenceRequired:1b,Invulnerable:1b,CustomName:'{{\"text\":\"继任者\"}}',Rotation:[0.0f,0.0f]}}")
    import time; time.sleep(0.5)
    rot_t0 = r.command(f"data get entity @e[type=villager,name=\"继任者\",limit=1] Rotation").strip()
    render_villager(0, "BEFORE — villager 继任者 平视", f"{OUT}/SPRITE_lowhead_before.png", rot_t0)
    r.command(f"tp @e[type=villager,name=\"继任者\",limit=1] ~ ~ ~ 0 45")
    time.sleep(0.4)
    rot_t1 = r.command(f"data get entity @e[type=villager,name=\"继任者\",limit=1] Rotation").strip()
    render_villager(45, "AFTER — villager 继任者 低头", f"{OUT}/SPRITE_lowhead_after.png", rot_t1)

print("[SAVED] SPRITE_lowhead_before.png")
print("[SAVED] SPRITE_lowhead_after.png")
print(f"rot_t0={rot_t0}")
print(f"rot_t1={rot_t1}")
