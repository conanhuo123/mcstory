#!/usr/bin/env python3
"""topdown_mosaic.py — 把所有 topdown PNG 拼一张 4x4 mosaic"""
import os, glob
from PIL import Image, ImageDraw, ImageFont

PNGS = sorted(
    glob.glob('/Users/coco/mcstory/outputs/gate1_acceptance/TOPDOWN_*.png') +
    glob.glob('/Users/coco/mcstory/outputs/gate1_batch10/TOPDOWN_*.png')
)
LABELS = {
    '01_shulker_ship': '深海沉船 潜影贝',
    '02_ender_dragon': '末影龙 花海产卵',
    '03_creeper_piano': '苦力怕 监狱钢琴',
    '00': '末影杀手 偷金条',
    '01': '村民 红石音乐会',
    '02': '钻石龙 末地祭坛',
    '03': '苦力怕 求婚',
    '04': '潜影贝 写日记',
    '05': '唤魔者 召唤幻影',
    '06': '守卫者 竖琴',
    '07': '猪灵银行 被抢劫',
    '08': '美西螈 预言',
    '09': '幻影邮局 寄信',
}

cols = 4
thumb_w = 360
cell_h = thumb_w + 50
pad = 20
title_h = 60

n = len(PNGS)
rows = (n + cols - 1) // cols
W = cols * thumb_w + (cols + 1) * pad
H = title_h + rows * cell_h + pad

out = Image.new('RGB', (W, H), (10, 14, 24))
d = ImageDraw.Draw(out)
try:
    f_title = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 28)
    f_cap = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 18)
except:
    f_title = ImageFont.load_default(); f_cap = f_title

d.text((pad, 18), 'mcstory · 14 ad-hoc one-sentence → JSON → top-down (D1 6/18)',
       fill=(220, 230, 255), font=f_title)

for i, png in enumerate(PNGS):
    r, c = divmod(i, cols)
    x = pad + c * (thumb_w + pad)
    y = title_h + r * cell_h
    img = Image.open(png).convert('RGB')
    img.thumbnail((thumb_w, thumb_w))
    out.paste(img, (x, y))
    # 标题
    key = os.path.basename(png).replace('TOPDOWN_','').replace('.png','')
    label = LABELS.get(key, key)
    d.text((x, y + img.height + 4), label, fill=(180, 200, 240), font=f_cap)

out_path = '/Users/coco/mcstory/outputs/gate1_acceptance/MOSAIC_all14.png'
out.save(out_path, optimize=True)
print(f'[SAVED] {out_path}  ({out.size})')
print(f'  thumbs: {n}')
