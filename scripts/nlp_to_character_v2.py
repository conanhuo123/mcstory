#!/usr/bin/env python3
"""nlp_to_character_v2.py — 精模 humanoid (老板 12:35 要求 '精致+动作+标准提高')

v1 384 blocks 太糙. v2 升级:
  高度 22→35 (压迫感 +60%)
  头部五官 (eye/mouth/cheek + 头饰花纹 face_pattern)
  胸部装饰 (chest_emblem: spider/sun/cross/tiger)
  cape 披风可选 (后方 5 块下垂)
  手指 5 块 (vs v1 1 块)
  靴子细节 (双层)
  武器精模 (金箍棒 12 高 + 红环 + gold cap, 蛛丝 5 节 + 黏点)
  动作 pose (ArmorStand 配真角色完成动作姿态)
预期 1500+ blocks/角色, 锁版 mecha v3 (528) 的 3 倍密度.
"""
import sys, os, json, urllib.request, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel_dsl import VoxelBuilder
from mcrcon import MCRcon

GPT55_URL = "https://ax-useast-resource.services.ai.azure.com/api/projects/ax-useast/openai/v1/responses"
GPT55_MODEL = "gpt-5.5-standard"
AUTH = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")

def get_key():
    d = json.load(open(AUTH))
    for p in d.get("profiles", {}).values():
        if p.get("provider") == "co-azure-gpt55": return p["key"]
    return None

FACE_PATTERNS = ['plain','monkey','spider_mask','cyclops','demon','warrior','none']
CHEST_EMBLEMS = ['spider','sun','star','cross','tiger_stripe','dragon','letter_S','none']
WEAPONS = ['beam_saber_v2','beam_rifle_v2','shield_v2','monkey_staff_v2','web_shooter_v2','spear_v2','magic_orb_v2','hammer','bow','none']
POSES = ['standing','fighting_stance','staff_raised','crouch_pounce','arms_out','jumping','meditating']
COMMON_BLOCKS = [
    'red_concrete','blue_concrete','yellow_concrete','green_concrete','black_concrete','white_concrete',
    'orange_concrete','purple_concrete','pink_concrete','cyan_concrete',
    'iron_block','gold_block','diamond_block','emerald_block','quartz_block','lapis_block','copper_block',
    'red_terracotta','yellow_terracotta','blue_terracotta','green_terracotta','black_terracotta','white_terracotta',
    'orange_terracotta','brown_terracotta',
    'oak_planks','dark_oak_planks','stone','cobblestone','deepslate','obsidian','netherite_block',
    'sea_lantern','glowstone','glass','tinted_glass','red_stained_glass','blue_stained_glass','yellow_stained_glass',
]

SYSTEM_PROMPT = f"""你是 MC 精模角色设计师 (v2 高标准). 给定中文角色描述, 输出 JSON spec, 系统用 35 块高 humanoid 真建 (mecha v3 同级精度).

palette 字段 (12): head, mask, body, torso, arm, shoulder, leg, joint, accent, antenna, weapon, detail_dark
face_pattern (头部五官风格): {FACE_PATTERNS}
chest_emblem (胸口图案): {CHEST_EMBLEMS}
weapon: {WEAPONS}
pose: {POSES}
cape (披风): true/false
cape_color: block name if cape=true
block 候选: {COMMON_BLOCKS}

palette 字段语义:
  head 头肤色/头盔块, mask 面罩/眼罩主色, body 主胸甲, torso 躯干填充
  arm 手臂主色, shoulder 肩甲, leg 大小腿
  joint 关节球 (一般灰/深色), accent 强调色 (红/金), antenna 头顶饰 (角/王冠/天线)
  weapon 武器主色, detail_dark 细节深色

输出严格 JSON:
{{
  "id": "<snake_v2>",
  "name": "<中文角色名>",
  "palette": {{12 字段全填}},
  "face_pattern": "<其一>",
  "chest_emblem": "<其一>",
  "weapon": "<其一>",
  "pose": "<其一>",
  "cape": <bool>,
  "cape_color": "<block_or_null>",
  "design_note": "<一句话>",
  "tags": [...]
}}

不合理 {{"error":"out_of_scope","reason":"..."}}.
"""

def nlp_to_char_spec(prompt):
    payload = json.dumps({"model": GPT55_MODEL, "instructions": SYSTEM_PROMPT, "input": f"角色: {prompt}"}).encode()
    req = urllib.request.Request(GPT55_URL, data=payload, headers={"Authorization": f"Bearer {get_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    for e in data.get("output") or []:
        if e.get("type") == "message":
            for c in e.get("content") or []:
                if c.get("type") == "output_text":
                    t = c.get("text","").strip()
                    if t.startswith("```"): t = "\n".join(t.split("\n")[1:-1])
                    return json.loads(t)
    return None

def draw_face(b, fx, fy, fz, pattern, palette):
    """5x5 脸面 (放在 head_front), fx 中心, fy bottom, fz=-2 朝前"""
    mask = palette['mask']; eye = palette.get('detail_dark','black_concrete'); accent = palette['accent']
    # 基底脸
    for dx in range(-2, 3):
        for dy in range(5):
            b.set(fx+dx, fy+dy, fz, mask)
    # 眼睛
    b.set(fx-1, fy+3, fz, eye); b.set(fx+1, fy+3, fz, eye)
    if pattern == 'monkey':
        # 猴脸: 大眼框 + 黄毛
        b.set(fx-2, fy+3, fz, accent); b.set(fx+2, fy+3, fz, accent)
        b.set(fx, fy+2, fz, accent)  # 鼻
        b.set(fx-1, fy+1, fz, eye); b.set(fx+1, fy+1, fz, eye)  # 嘴角
        b.set(fx, fy+1, fz, accent)
        # 金箍头环
        for dx in range(-2, 3): b.set(fx+dx, fy+5, fz, 'gold_block')
    elif pattern == 'spider_mask':
        # 蛛网纹 (cobweb 散布 + 大眼)
        b.set(fx-2, fy+3, fz, 'white_concrete'); b.set(fx+2, fy+3, fz, 'white_concrete')  # 大眼
        b.set(fx-1, fy+3, fz, eye); b.set(fx+1, fy+3, fz, eye)  # 瞳孔
        b.set(fx-2, fy+4, fz, eye); b.set(fx+2, fy+4, fz, eye)  # 眼角延伸
        # 蛛网射线
        b.set(fx, fy+2, fz, eye); b.set(fx, fy+4, fz, eye)
        b.set(fx-1, fy, fz, eye); b.set(fx+1, fy, fz, eye)
    elif pattern == 'cyclops':
        for dx in range(-1,2): b.set(fx+dx, fy+3, fz, accent)
        b.set(fx, fy+3, fz, eye)
    elif pattern == 'demon':
        b.set(fx-2, fy+5, fz, accent); b.set(fx+2, fy+5, fz, accent)  # 角
        b.set(fx-1, fy+1, fz, eye); b.set(fx+1, fy+1, fz, eye)
    elif pattern == 'warrior':
        # 头盔 + T 形面罩
        for dx in range(-2,3): b.set(fx+dx, fy+5, fz, palette.get('shoulder','iron_block'))
        for dy in range(0, 5): b.set(fx, fy+dy, fz, eye)

def draw_chest_emblem(b, cx, cy, cz, emblem, palette):
    """胸口 emblem 5x5 (cx 中心 cy bottom cz=-2 朝前)"""
    accent = palette['accent']; dark = palette.get('detail_dark','black_concrete')
    if emblem == 'spider':
        # 蛛形: 中心 + 8 腿
        b.set(cx, cy+2, cz, dark)
        for dx,dy in [(-1,3),(1,3),(-2,2),(2,2),(-2,1),(2,1),(-1,0),(1,0)]:
            b.set(cx+dx, cy+dy, cz, dark)
    elif emblem == 'sun':
        b.set(cx, cy+2, cz, accent)
        for dx,dy in [(-2,2),(2,2),(0,4),(0,0),(-1,3),(1,3),(-1,1),(1,1)]:
            b.set(cx+dx, cy+dy, cz, accent)
    elif emblem == 'star':
        for dx,dy in [(0,4),(-2,2),(2,2),(-1,0),(1,0),(0,2)]:
            b.set(cx+dx, cy+dy, cz, accent)
    elif emblem == 'cross':
        for dy in range(0,5): b.set(cx, cy+dy, cz, accent)
        for dx in [-1,1]: b.set(cx+dx, cy+3, cz, accent)
    elif emblem == 'tiger_stripe':
        for dy in [0,2,4]:
            for dx in range(-2,3):
                if (dx+dy)%2==0: b.set(cx+dx, cy+dy, cz, dark)
    elif emblem == 'dragon':
        b.set(cx, cy+3, cz, accent); b.set(cx-1, cy+2, cz, accent); b.set(cx+1, cy+2, cz, accent)
        b.set(cx, cy+1, cz, dark)
    elif emblem == 'letter_S':
        for dx in [-1,0,1]: b.set(cx+dx, cy+4, cz, accent); b.set(cx+dx, cy+0, cz, accent)
        b.set(cx-1, cy+3, cz, accent); b.set(cx+1, cy+1, cz, accent)
        b.set(cx, cy+2, cz, accent)

def draw_cape(b, anchor_x_min, anchor_x_max, anchor_y_top, color):
    """披风: 后方 z=+2 处下垂 5 高"""
    for dx in range(anchor_x_min, anchor_x_max+1):
        for dy in range(-12, 1):  # 下垂 12 块
            b.set(dx, anchor_y_top+dy, 2, color)

def draw_weapon_v2(b, hand_xyz, weapon_type, palette):
    ax, ay, az = hand_xyz
    weapon = palette.get('weapon','iron_block'); accent = palette['accent']; dark = palette.get('detail_dark','black_concrete')
    if weapon_type == 'monkey_staff_v2':
        # 金箍棒: 12 高斜举, gold 主体 + 红环 + gold cap
        for h in range(12):
            block = accent if h in [0,3,6,9,11] else weapon
            b.set(ax+h//3, ay+h, az, block)
        # 顶端 gold_block 突
        b.set(ax+4, ay+12, az, 'gold_block')
        b.set(ax+4, ay+13, az, 'glowstone')
    elif weapon_type == 'web_shooter_v2':
        # 蛛丝大网 5x5 cobweb 散布 + 手腕 iron
        b.set(ax, ay, az, weapon)
        for h in range(1, 7):
            for dz in [-1, 0, 1]:
                if (h+dz)%2: b.set(ax, ay-dz, az-h, 'cobweb')
        b.set(ax+1, ay, az-5, 'cobweb'); b.set(ax-1, ay, az-5, 'cobweb')
    elif weapon_type == 'beam_saber_v2':
        # 光剑 v2: 10 高 + glow tip
        for h in range(10):
            b.set(ax, ay+h, az, weapon if h<2 else 'sea_lantern')
        b.set(ax, ay+10, az, 'glowstone'); b.set(ax, ay+11, az, 'beacon')
    elif weapon_type == 'spear_v2':
        for h in range(12): b.set(ax, ay+h, az, 'oak_fence')
        b.set(ax, ay+12, az, 'iron_block'); b.set(ax, ay+13, az, 'diamond_block')
    elif weapon_type == 'hammer':
        for h in range(8): b.set(ax, ay+h, az, 'oak_fence')
        for dx in [-1,0,1]:
            for dz in [-1,0,1]:
                b.set(ax+dx, ay+8, az+dz, 'iron_block')
        b.set(ax, ay+9, az, 'gold_block')
    elif weapon_type == 'magic_orb_v2':
        b.set(ax, ay, az, weapon)
        for h in range(1,4): b.set(ax, ay+h, az, 'glass')
        b.set(ax, ay+4, az, 'glowstone')
    elif weapon_type == 'bow':
        for dy in range(-2,3): b.set(ax, ay+dy, az, weapon)
        b.set(ax, ay-2, az+1, 'stick'); b.set(ax, ay+2, az+1, 'stick')
    elif weapon_type == 'shield_v2':
        for dy in range(-2,4):
            for dz in range(-2,3):
                b.set(ax, ay+dy, az+dz-2, weapon if abs(dy)+abs(dz)>3 else accent)

def build_character_v2(spec, origin):
    """精模 35 块高 humanoid, mecha v3 同级"""
    if 'error' in spec: raise ValueError(f"GPT rejected: {spec.get('reason')}")
    palette = {**{'leg':'gray_concrete','body':'lapis_block','accent':'red_concrete','head':'quartz_block',
                  'mask':'black_concrete','antenna':'yellow_concrete','arm':'quartz_block','shoulder':'lapis_block',
                  'weapon':'iron_block','joint':'gray_concrete','detail_dark':'deepslate','torso':'lapis_block'},
               **spec.get('palette', {})}
    pose = spec.get('pose', 'standing')
    b = VoxelBuilder(origin, mirror_axis='x')
    # 35 高比例: leg 13 + pelvis 3 + torso 12 + shoulder 1 + head 6
    leg_h = 13; pelvis_h = 3; torso_h = 12; head_h = 6
    # ===== LEGS =====
    # 靴子 (双层 + cap)
    b.box(1, 0, -1, 3, 1, 2, palette['detail_dark'])
    b.box(1, 0, -2, 3, 0, -2, palette['accent'])  # 靴前 accent
    b.box(1, 2, -1, 3, 2, 1, palette['leg'])  # 脚踝
    # 小腿
    b.box(1, 3, 0, 3, 3+leg_h//2-1, 0, palette['leg'])
    b.box(1, 3, -1, 1, 3+leg_h//2-1, -1, palette['detail_dark'])  # 小腿侧深线
    # 膝关节 (圆球)
    for dy in [0,1]:
        for dx in [1,2,3]: b.set(dx, 3+leg_h//2+dy, 0, palette['joint'])
    # 大腿 (粗)
    b.box(1, 3+leg_h//2+2, 0, 3, leg_h+2, 0, palette['leg'])
    b.box(1, leg_h//2+5, -1, 1, leg_h//2+6, -1, palette['accent'])  # 大腿侧红条

    # ===== PELVIS =====
    pelvis_y = leg_h + 3
    b.box(0, pelvis_y, -1, 4, pelvis_y+pelvis_h-1, 2, palette['body'])
    b.box(0, pelvis_y, -2, 1, pelvis_y+pelvis_h-1, -2, palette['accent'])  # 腰带 accent
    b.box(0, pelvis_y, 3, 4, pelvis_y, 3, palette['detail_dark'])  # 后腰深

    # ===== TORSO =====
    torso_bot = pelvis_y + pelvis_h
    torso_top = torso_bot + torso_h
    b.box(0, torso_bot, -1, 4, torso_top, 2, palette['body'])
    # 内填 torso 色 (中心)
    b.box(0, torso_bot+1, 0, 1, torso_top-1, 1, palette.get('torso', palette['body']))
    # 胸前 emblem
    if spec.get('chest_emblem') and spec['chest_emblem'] != 'none':
        draw_chest_emblem(b, 2, torso_bot+3, -2, spec['chest_emblem'], palette)
    # 腰部 accent V
    b.set(0, torso_bot, -2, palette['accent']); b.set(2, torso_bot+1, -2, palette['accent'])
    # 背部 spine accent
    for dy in range(0, torso_h, 2): b.set(0, torso_bot+dy, 3, palette['accent'])

    # ===== SHOULDERS =====
    sh_y = torso_top
    b.box(5, sh_y-1, -1, 6, sh_y+1, 2, palette['shoulder'])
    b.set(6, sh_y+1, -1, palette['accent']); b.set(6, sh_y+1, 0, palette['accent'])
    # 肩关节
    for dx in [4,5]: b.set(dx, sh_y-1, 0, palette['joint']); b.set(dx, sh_y, 0, palette['joint'])

    # ===== ARMS =====
    arm_h = 10
    # 上臂
    if pose in ('staff_raised','arms_out'):
        # 抬手
        b.box(5, sh_y+2, 0, 5, sh_y+arm_h, 0, palette['arm'])
        # 肘
        b.set(5, sh_y+arm_h//2+2, 0, palette['joint'])
        # 前臂 朝上
        b.box(5, sh_y+arm_h//2+3, 0, 5, sh_y+arm_h+3, 0, palette['arm'])
        # 手指 5 块 (cluster 顶端)
        for fx in [4,5,6]: b.set(fx, sh_y+arm_h+4, 0, palette['accent'])
        b.set(5, sh_y+arm_h+5, 0, palette['accent'])
        # 武器在抬高的手
        if spec.get('weapon') and spec['weapon'] != 'none':
            draw_weapon_v2(b, (5, sh_y+arm_h+4, 0), spec['weapon'], palette)
    else:
        # 自然垂
        b.box(5, sh_y-arm_h//2-1, 0, 5, sh_y-1, 0, palette['arm'])
        b.set(5, sh_y-arm_h//2-1, 0, palette['joint'])
        b.box(5, sh_y-arm_h, 0, 5, sh_y-arm_h//2-2, 0, palette['arm'])
        # 手指
        for fx in [4,5,6]: b.set(fx, sh_y-arm_h-1, 0, palette['accent'])
        # 武器 @ 手
        if spec.get('weapon') and spec['weapon'] != 'none':
            draw_weapon_v2(b, (5, sh_y-arm_h-1, 0), spec['weapon'], palette)

    # ===== NECK + HEAD =====
    neck_y = torso_top + 1
    b.box(0, neck_y, 0, 1, neck_y, 0, palette['joint'])
    head_bot = neck_y + 1
    # head cube 6 高
    b.box(-2, head_bot, -1, 2, head_bot+head_h-1, 1, palette['head'])
    # 后脑勺
    b.box(-2, head_bot, 2, 2, head_bot+head_h-1, 2, palette.get('detail_dark', palette['head']))
    # 面部 (5x5 @ z=-2)
    draw_face(b, 0, head_bot, -2, spec.get('face_pattern','plain'), palette)
    # 头顶 antenna / 王冠
    for dx in range(-2,3): b.set(dx, head_bot+head_h, 0, palette['antenna'])
    b.set(0, head_bot+head_h+1, 0, palette['antenna']); b.set(0, head_bot+head_h+2, 0, palette['accent'])

    # ===== CAPE =====
    if spec.get('cape'):
        cape_color = spec.get('cape_color') or palette['accent']
        draw_cape(b, -2, 2, torso_top, cape_color)

    return b, palette, pose

def cmds_from_builder(b):
    return [f"setblock {x} {y} {z} {block}" for (x,y,z), block in sorted(b.blocks.items())]

def run_rcon(cmds):
    ok = 0
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        for c in cmds:
            try: r.command(c); ok += 1
            except: pass
    return ok

def end_to_end(prompt, origin=(-600, 80, -900)):
    print(f"[1/3] NLP→v2 char spec: '{prompt}'")
    spec = nlp_to_char_spec(prompt)
    if not spec or 'error' in spec:
        print(f"❌ {spec}"); return None
    print(json.dumps(spec, ensure_ascii=False, indent=2))
    print(f"\n[2/3] build_v2 @ origin {origin}")
    b, palette, pose = build_character_v2(spec, origin)
    cmds = cmds_from_builder(b)
    print(f"   {len(cmds)} blocks (pose={pose})")
    print(f"\n[3/3] RCON build...")
    t0 = time.time()
    ok = run_rcon(cmds)
    dt = time.time() - t0
    print(f"   {ok}/{len(cmds)} OK in {dt:.1f}s")
    ts = time.strftime('%Y%m%d-%H%M%S')
    out_p = f'/Users/coco/mcstory/outputs/char_v2_{spec["id"]}_{ts}.json'
    json.dump({'prompt':prompt,'spec':spec,'origin':list(origin),'cmds_total':len(cmds),'rcon_ok':ok,
               'palette_resolved':palette,'pose':pose,'ts':ts}, open(out_p,'w'), ensure_ascii=False, indent=2)
    print(f"   → {out_p}")
    return {'spec':spec,'origin':list(origin),'cmds_total':len(cmds),'rcon_ok':ok}

if __name__ == '__main__':
    prompt = sys.argv[1] if len(sys.argv)>1 else "孙悟空, 金箍棒高举"
    origin = tuple(int(x) for x in sys.argv[2:5]) if len(sys.argv)>=5 else (-600, 80, -900)
    end_to_end(prompt, origin)
