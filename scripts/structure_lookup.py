#!/usr/bin/env python3
"""structure_lookup.py — L1.1 NLP→mc 内置 structure_id 路由
50+ Mojang 原生精模, 一句话 → /place structure, 0 net 0 captcha.
"""
import sys, json, urllib.request, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcrcon import MCRcon

# mc 1.20.4 内置 structure (全部 Mojang 原生设计):
STRUCTURES = {
    # 大型建筑 (Mojang 真精模, 50-200+ blocks)
    'minecraft:mansion':           '林地豪宅 (60x60+, 多层多房间, mc 最大单结构)',
    'minecraft:desert_pyramid':    '沙漠金字塔 (4 角塔 + 中央陷阱室)',
    'minecraft:jungle_pyramid':    '丛林神庙 (3 层 + 机关室)',
    'minecraft:ancient_city':      '远古之城 (deep dark, sculk + 中央灯塔, 巨大)',
    'minecraft:end_city':          '末地城 (浮空 purpur 塔群)',
    'minecraft:monument':          '海底神殿 (prismarine 大型, 需水)',
    'minecraft:fortress':          'Nether 要塞 (nether_brick 桥/塔)',
    'minecraft:bastion_remnant':   'Nether 堡垒废墟',
    'minecraft:stronghold':        '要塞 (地下迷宫 + end portal)',
    'minecraft:igloo':             '雪屋 (小屋 + 地下室)',
    'minecraft:pillager_outpost':  '掠夺者前哨 (塔楼)',
    'minecraft:swamp_hut':         '女巫小屋 (沼泽)',
    'minecraft:trail_ruins':       '探险家遗迹 (考古)',
    'minecraft:ocean_ruin_cold':   '寒带海底废墟',
    'minecraft:ocean_ruin_warm':   '热带海底废墟',
    'minecraft:shipwreck':         '沉船',
    'minecraft:buried_treasure':   '埋藏宝箱',
    'minecraft:mineshaft':         '废弃矿井',
    # 村庄 (5 biome variant, 一个村庄是多 building 集合)
    'minecraft:village_plains':    '平原村庄',
    'minecraft:village_desert':    '沙漠村庄',
    'minecraft:village_savanna':   '稀树草原村庄',
    'minecraft:village_snowy':     '雪地村庄',
    'minecraft:village_taiga':     '针叶林村庄',
    # Ruined Portal (多 variant)
    'minecraft:ruined_portal_standard': '废弃下界传送门 (地表)',
    'minecraft:ruined_portal_jungle':   '废弃下界传送门 (丛林)',
}

# NLP 关键词 → structure_id
KEYWORD_MAP = {
    '豪宅': 'minecraft:mansion', '别墅': 'minecraft:mansion', '森林': 'minecraft:mansion', '林地': 'minecraft:mansion',
    '金字塔': 'minecraft:desert_pyramid', '法老': 'minecraft:desert_pyramid', '法老王': 'minecraft:desert_pyramid',
    '丛林': 'minecraft:jungle_pyramid', '神庙': 'minecraft:jungle_pyramid',
    '远古': 'minecraft:ancient_city', '黑暗': 'minecraft:ancient_city', 'sculk': 'minecraft:ancient_city',
    '末地': 'minecraft:end_city', '紫塔': 'minecraft:end_city',
    '海底': 'minecraft:monument', '海洋神殿': 'minecraft:monument', '神殿': 'minecraft:monument',
    '地狱': 'minecraft:fortress', '下界': 'minecraft:fortress', 'nether': 'minecraft:fortress', '要塞': 'minecraft:fortress',
    '猪灵': 'minecraft:bastion_remnant', '堡垒': 'minecraft:bastion_remnant',
    '末地传送门': 'minecraft:stronghold', '迷宫': 'minecraft:stronghold',
    '雪屋': 'minecraft:igloo', '冰屋': 'minecraft:igloo', '爱斯基摩': 'minecraft:igloo',
    '掠夺者': 'minecraft:pillager_outpost', '前哨': 'minecraft:pillager_outpost',
    '女巫': 'minecraft:swamp_hut', '沼泽小屋': 'minecraft:swamp_hut',
    '考古': 'minecraft:trail_ruins', '遗迹': 'minecraft:trail_ruins',
    '沉船': 'minecraft:shipwreck', '船': 'minecraft:shipwreck',
    '矿井': 'minecraft:mineshaft', '矿洞': 'minecraft:mineshaft',
    '宝藏': 'minecraft:buried_treasure', '宝箱': 'minecraft:buried_treasure',
    '村庄': 'minecraft:village_plains', '平原村': 'minecraft:village_plains',
    '沙漠村': 'minecraft:village_desert',
    '草原村': 'minecraft:village_savanna',
    '雪村': 'minecraft:village_snowy',
    '针叶': 'minecraft:village_taiga', '寒林': 'minecraft:village_taiga',
}

def route(prompt):
    """中文 prompt → structure_id (None 表示走 L2 voxel_dsl)"""
    p = prompt.lower()
    for kw, sid in KEYWORD_MAP.items():
        if kw in prompt or kw.lower() in p:
            return sid
    return None

def place_structure(structure_id, origin, rcon_pass='mcstory123'):
    """RCON force load + place"""
    ox, oy, oz = origin
    with MCRcon('127.0.0.1', rcon_pass, port=25575) as r:
        for cx in range(ox-32, ox+33, 16):
            for cz in range(oz-32, oz+33, 16):
                r.command(f'forceload add {cx} {cz}')
        import time; time.sleep(1)
        result = r.command(f'place structure {structure_id} {ox} {oy} {oz}')
        if 'Generated' in result:
            r.command(f'setblock {ox-3} {oy+3} {oz-3} oak_sign{{front_text:{{messages:[\'"{STRUCTURES.get(structure_id,"")[:14]}"\',\'""\',\'"Mojang 原生"\',\'"{structure_id[:18]}"\']}}}}')
        return result

def end_to_end(prompt, origin=(-1000, 80, -100)):
    sid = route(prompt)
    if not sid:
        return {'matched': False, 'prompt': prompt, 'fallback': 'go L2 voxel_dsl'}
    result = place_structure(sid, origin)
    return {'matched': True, 'structure_id': sid, 'origin': origin, 'result': result,
            'description': STRUCTURES.get(sid, '')}

if __name__ == '__main__':
    prompt = sys.argv[1] if len(sys.argv)>1 else "建一座林地豪宅"
    origin = tuple(int(x) for x in sys.argv[2:5]) if len(sys.argv)>=5 else (-1000, 80, -100)
    print(json.dumps(end_to_end(prompt, origin), ensure_ascii=False, indent=2))
