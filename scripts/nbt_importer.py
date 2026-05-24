#!/usr/bin/env python3
"""nbt_importer.py — L1.2 自动 import minecolonies-schematics 精模库
598 个玩家手做 .nbt 精模 (9 style × 13 building type × 5 size).
NLP→ 路由 → /place template 真装入 paper.
"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcrcon import MCRcon

PAPER_STRUCT_DIR = '/Users/coco/video_factory/mc_server/world/generated/minecolonies/structures'
SCHEM_REPO = '/Users/coco/mcstory/schematics/minecolonies'
NAMESPACE = 'minecolonies'

def list_templates():
    """列已 import 到 paper 的 templates"""
    if not os.path.exists(PAPER_STRUCT_DIR): return []
    return sorted(f.replace('.nbt','') for f in os.listdir(PAPER_STRUCT_DIR) if f.endswith('.nbt'))

def import_more(styles=None, building_types=None, max_per_combo=2):
    """从 SCHEM_REPO 拷更多 .nbt 到 paper. styles/building_types 不传则全部."""
    if not os.path.exists(SCHEM_REPO):
        print("schematic repo 不存在, 先 gh repo clone")
        return 0
    if not os.path.exists(PAPER_STRUCT_DIR): os.makedirs(PAPER_STRUCT_DIR)
    if styles is None:
        styles = [d for d in os.listdir(SCHEM_REPO) if os.path.isdir(os.path.join(SCHEM_REPO, d)) and not d.startswith('.')]
    n = 0
    for style in styles:
        sd = os.path.join(SCHEM_REPO, style, 'buildings')
        if not os.path.isdir(sd): continue
        types = building_types or os.listdir(sd)
        for bt in types:
            btd = os.path.join(sd, bt)
            if not os.path.isdir(btd): continue
            files = sorted([f for f in os.listdir(btd) if f.endswith('.nbt')])[:max_per_combo]
            for f in files:
                src = os.path.join(btd, f)
                dest_name = f"{style}_{bt}_{f.replace('.nbt','')}.nbt"
                dest = os.path.join(PAPER_STRUCT_DIR, dest_name)
                if not os.path.exists(dest):
                    subprocess.run(['cp', src, dest], check=False); n += 1
    return n

def place(template_id, origin):
    """RCON forceload + /place template"""
    ox, oy, oz = origin
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        for cx in range(ox-32, ox+33, 16):
            for cz in range(oz-32, oz+33, 16):
                r.command(f'forceload add {cx} {cz}')
        import time; time.sleep(0.5)
        r.command(f'fill {ox-15} {oy} {oz-15} {ox+15} {oy+40} {oz+15} air')
        return r.command(f'place template {NAMESPACE}:{template_id} {ox} {oy} {oz}')

# NLP 关键词 → template_id (后续可接 GPT-5.5 模糊匹配)
KEYWORDS = {
    '市政厅': lambda style='darkoak': f'{style}_townhall_townhall5',
    '议会': lambda style='darkoak': f'{style}_townhall_townhall5',
    '兵营': lambda style='darkoak': f'{style}_barracks_barracks5',
    '军营': lambda style='darkoak': f'{style}_barracks_barracks5',
    '塔楼': lambda style='darkoak': f'{style}_barracktower_barrackstower5',
    '岗哨': lambda style='darkoak': f'{style}_barracktower_barrackstower5',
    '农舍': lambda style='darkoak': f'{style}_farmer_farmer5',
    '农场': lambda style='darkoak': f'{style}_farmer_farmer5',
    '仓库': lambda style='darkoak': f'{style}_warehouse_warehouse5',
}

def route(prompt, default_style='darkoak'):
    for kw, fn in KEYWORDS.items():
        if kw in prompt:
            # detect style hint
            for s in ['birch','darkoak','sandstone','stone','mesa','taiga']:
                if s in prompt or {'橡木':'darkoak','沙石':'sandstone','石头':'stone','桦木':'birch','红岩':'mesa','针叶':'taiga'}.get(s, '') in prompt: pass
            style = default_style
            for cn, en in [('橡木','darkoak'),('沙石','sandstone'),('石头','stone'),('桦木','birch'),('红岩','mesa'),('针叶','taiga')]:
                if cn in prompt: style = en; break
            return fn(style)
    return None

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'import':
        n = import_more()
        print(f"imported {n} new .nbt to {PAPER_STRUCT_DIR}")
        templates = list_templates()
        print(f"total in paper: {len(templates)}")
    elif len(sys.argv) > 1 and sys.argv[1] == 'list':
        for t in list_templates(): print(t)
    elif len(sys.argv) > 1 and sys.argv[1] == 'route':
        prompt = sys.argv[2] if len(sys.argv) > 2 else "建一个市政厅"
        tid = route(prompt)
        print(json.dumps({'prompt':prompt,'template_id':tid}, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == 'place':
        tid = sys.argv[2]
        origin = tuple(int(x) for x in sys.argv[3:6]) if len(sys.argv) >= 6 else (-1000, 80, -1000)
        print(place(tid, origin))
    else:
        print("usage: nbt_importer.py [import|list|route '一句话'|place <tid> <x> <y> <z>]")
