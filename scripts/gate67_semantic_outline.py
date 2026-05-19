#!/usr/bin/env python3
"""gate67_semantic_outline.py — 第 6/7 闸 algo
⑥ Semantic: 用 palette 期望 vs 实际 block 比例对比 (是否像目标类别)
⑦ 主体轮廓: connected-component cluster size + 边缘 sharpness (Canny)
"""
import sys, os, json, numpy as np
from PIL import Image
try: from scipy import ndimage; HAS_SCIPY=True
except: HAS_SCIPY=False

# 期望 palette (每类目标 RGB 比例阈值)
SEMANTIC_PALETTES = {
    'cottage': {  # 小屋: oak_log + spruce + cobblestone + glass
        'expected_colors': [(110,80,50),(170,130,80),(120,120,120),(200,230,255)],
        'min_ratio_total': 0.10,  # >= 10% 像素是这些色
    },
    'castle': {  # 城堡: cobblestone + stone_bricks + red flag
        'expected_colors': [(120,120,120),(140,140,140),(220,30,30),(80,60,40)],
        'min_ratio_total': 0.10,
    },
    'pyramid': {  # 金字塔: sandstone + cut + chiseled + gold
        'expected_colors': [(230,210,150),(200,170,130),(180,150,90),(255,215,0)],
        'min_ratio_total': 0.10,
    },
    'mecha': {  # 高达: quartz + lapis + red + yellow + gray
        'expected_colors': [(235,230,220),(35,75,200),(220,40,40),(240,220,60),(110,110,110)],
        'min_ratio_total': 0.05,
    },
    'mine': {  # 矿洞: cobblestone + ore (各种颜色)
        'expected_colors': [(120,120,120),(180,140,90),(180,210,240),(50,180,80)],
        'min_ratio_total': 0.05,
    },
    'skyscraper': {  # 摩天楼: light_gray + tinted_glass + iron
        'expected_colors': [(200,200,210),(60,60,80),(220,220,230),(220,30,30)],
        'min_ratio_total': 0.10,
    },
    'temple': {  # 寺庙: dark_oak + red + gold
        'expected_colors': [(60,40,30),(220,40,40),(255,215,0),(180,80,40)],
        'min_ratio_total': 0.10,
    },
}

def gate6_semantic(png_path, target_class):
    """⑥ Semantic: 检 png 中目标 palette 占比"""
    if target_class not in SEMANTIC_PALETTES:
        return {'gate':6, 'name':'semantic', 'status':'SKIP_UNKNOWN_CLASS', 'target':target_class}
    spec = SEMANTIC_PALETTES[target_class]
    arr = np.array(Image.open(png_path).convert('RGB'))
    H, W, _ = arr.shape
    total = H * W
    matched = 0
    for r,g,b in spec['expected_colors']:
        m = (abs(arr[:,:,0].astype(int)-r)<25) & (abs(arr[:,:,1].astype(int)-g)<25) & (abs(arr[:,:,2].astype(int)-b)<25)
        matched += int(m.sum())
    ratio = matched / total
    ok = ratio >= spec['min_ratio_total']
    return {'gate':6, 'name':'semantic', 'target':target_class,
            'matched_pixels':matched, 'total_pixels':total, 'ratio':round(ratio,4),
            'min_required':spec['min_ratio_total'],
            'status':'PASS' if ok else 'FAIL'}

def gate7_outline(png_path, target_class, min_cluster_size=2000, max_cluster_ratio=0.7):
    """⑦ 主体轮廓: connected-component 最大 cluster size + 占图比例 + 边缘 sharpness"""
    if not HAS_SCIPY:
        return {'gate':7, 'name':'outline', 'status':'SKIP_SCIPY'}
    spec = SEMANTIC_PALETTES.get(target_class)
    if not spec: return {'gate':7, 'name':'outline', 'status':'SKIP_UNKNOWN_CLASS'}
    arr = np.array(Image.open(png_path).convert('RGB'))
    H, W, _ = arr.shape
    mask = np.zeros((H,W), bool)
    for r,g,b in spec['expected_colors']:
        m = (abs(arr[:,:,0].astype(int)-r)<25) & (abs(arr[:,:,1].astype(int)-g)<25) & (abs(arr[:,:,2].astype(int)-b)<25)
        mask |= m
    labels, n = ndimage.label(mask)
    if n == 0: return {'gate':7, 'name':'outline', 'status':'FAIL_NO_OBJECT'}
    sizes = ndimage.sum(mask, labels, range(1, n+1))
    biggest = int(np.max(sizes))
    biggest_ratio = biggest / (H*W)
    # 边缘 sharpness (gradient magnitude)
    big_idx = int(np.argmax(sizes)) + 1
    cluster_mask = (labels == big_idx).astype(np.uint8) * 255
    # 简易 edge: sobel
    gy, gx = np.gradient(cluster_mask.astype(float))
    edge_strength = np.sqrt(gx**2 + gy**2)
    edge_pixels = int((edge_strength > 50).sum())
    edge_ratio = edge_pixels / max(1, biggest)

    size_ok = biggest >= min_cluster_size and biggest_ratio <= max_cluster_ratio
    edge_ok = 0.05 < edge_ratio < 0.5  # 主体边缘清晰但不全是边
    ok = size_ok and edge_ok
    return {'gate':7, 'name':'outline', 'target':target_class,
            'biggest_cluster':biggest, 'biggest_ratio':round(biggest_ratio,4),
            'edge_pixels':edge_pixels, 'edge_ratio':round(edge_ratio,4),
            'min_cluster':min_cluster_size, 'max_ratio':max_cluster_ratio,
            'status':'PASS' if ok else 'FAIL',
            'fail_reason':None if ok else f"size_ok={size_ok}, edge_ok={edge_ok}"}


if __name__ == '__main__':
    # 测 3 题
    tests = [
        ('/Users/coco/mcstory/outputs/题库_cottage_final/front.png', 'cottage'),
        ('/Users/coco/mcstory/outputs/题库_pyramid_final/pyramid_front.png', 'pyramid'),
        ('/Users/coco/mcstory/outputs/题库_mecha_v3_final/mech_front.png', 'mecha'),
        ('/Users/coco/mcstory/outputs/题库_castle_v2_final/castle_front.png', 'castle'),
        ('/Users/coco/mcstory/outputs/题库_mine_final/front.png', 'mine'),
    ]
    results = {}
    for png, cls in tests:
        if os.path.exists(png):
            g6 = gate6_semantic(png, cls)
            g7 = gate7_outline(png, cls)
            results[f'{cls}_{os.path.basename(png)}'] = {'gate6':g6, 'gate7':g7}
    print(json.dumps(results, indent=2, ensure_ascii=False))
    json.dump(results, open('/Users/coco/mcstory/outputs/model_registry/gate67_audit.json','w'), ensure_ascii=False, indent=2)
