#!/usr/bin/env python3
"""nlp_to_character.py — L3 humanoid 通用化
一句话 → GPT-5.5 出 character spec (palette + weapon + accessory) → 复用 mecha_humanoid_v3 rig 真建
让 mcstory 解 '孙悟空大战蜘蛛侠' 这种原创请求.
"""
import sys, os, json, urllib.request, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcrcon import MCRcon

GPT55_URL = "https://ax-useast-resource.services.ai.azure.com/api/projects/ax-useast/openai/v1/responses"
GPT55_MODEL = "gpt-5.5-standard"
AUTH = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")

def get_key():
    d = json.load(open(AUTH))
    for p in d.get("profiles", {}).values():
        if p.get("provider") == "co-azure-gpt55":
            return p["key"]
    return None

HUMANOID_BODY_PARTS = ['head','body','torso','arm','shoulder','leg','joint','accent','mask','antenna','weapon','detail_dark']
WEAPONS = ['beam_saber','beam_rifle','shield','monkey_staff','web_shooter','spear','magic_orb','none']
COMMON_BLOCKS = [
    'red_concrete','blue_concrete','yellow_concrete','green_concrete','black_concrete','white_concrete','orange_concrete','purple_concrete','pink_concrete',
    'iron_block','gold_block','diamond_block','emerald_block','quartz_block','lapis_block',
    'red_terracotta','yellow_terracotta','blue_terracotta','green_terracotta','black_terracotta','white_terracotta','orange_terracotta','brown_terracotta',
    'oak_planks','dark_oak_planks','stone','cobblestone','deepslate','obsidian',
    'sea_lantern','glowstone','glass','tinted_glass','red_stained_glass','blue_stained_glass',
]

SYSTEM_PROMPT = f"""你是 MC 角色设计师. 给定中文角色描述, 输出 JSON spec, 系统会用 humanoid rig (18 骨, gundam_7head 比例) 真建.

可选 palette 字段 (12 个): {HUMANOID_BODY_PARTS}
可选 block 值: {COMMON_BLOCKS}

可选武器 (持右手): {WEAPONS}

palette 字段语义 (按这个填):
  head 头颅块色 (脸/头盔), mask 面罩/眼罩色, body 主胸甲, torso 主躯干色
  arm 上下臂色, shoulder 肩甲色, leg 大腿/小腿色
  joint 关节球色 (一般灰/黑), accent 强调色 (红/金/亮色)
  antenna 头顶天线/触角色, weapon 武器主体色, detail_dark 细节深色

输出严格 JSON (无 markdown 无解释):
{{
  "id": "<lowercase_snake_v1>",
  "name": "<中文角色名>",
  "palette": {{"head":"...","mask":"...","body":"...","torso":"...","arm":"...","shoulder":"...","leg":"...","joint":"...","accent":"...","antenna":"...","weapon":"...","detail_dark":"..."}},
  "weapon": "<one_of {WEAPONS}>",
  "height_blocks": 22,
  "design_note": "<一句话设计意图>",
  "tags": [...]
}}

不合理的 (e.g. '建个银河系角色') 输出 {{"error":"out_of_scope","reason":"..."}}.
"""

def nlp_to_char_spec(prompt):
    payload = json.dumps({
        "model": GPT55_MODEL,
        "instructions": SYSTEM_PROMPT,
        "input": f"用户角色描述: {prompt}"
    }).encode("utf-8")
    req = urllib.request.Request(GPT55_URL, data=payload,
        headers={"Authorization": f"Bearer {get_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    for entry in data.get("output") or []:
        if entry.get("type") == "message":
            for block in entry.get("content") or []:
                if block.get("type") == "output_text":
                    text = block.get("text", "").strip()
                    if text.startswith("```"):
                        text = "\n".join(text.split("\n")[1:-1])
                    return json.loads(text)
    return None

def build_character(spec, origin):
    """spec → 调 mecha_humanoid_v3 同款 rig + spec.palette + spec.weapon"""
    if 'error' in spec:
        raise ValueError(f"GPT rejected: {spec.get('reason')}")
    # 注入到 mecha_humanoid_v3.PALETTES, 调 build_humanoid
    import mecha_humanoid_v3 as mh3
    pid = f"_nlp_{spec['id']}"
    # 完善 palette (补缺省)
    DEFAULTS = dict(leg='gray_concrete', body='lapis_block', accent='red_concrete',
                    head='quartz_block', mask='black_concrete', antenna='yellow_concrete',
                    arm='quartz_block', shoulder='lapis_block', weapon='iron_block',
                    joint='gray_concrete', detail_dark='deepslate', torso='lapis_block')
    full_palette = dict(DEFAULTS)
    full_palette.update(spec.get('palette', {}))
    mh3.PALETTES = getattr(mh3, 'PALETTES', {})
    # build_humanoid 现在 hardcode PALETTES, 我 patch 直接 inject
    # 实际策略: 直接抄 build_humanoid 的逻辑, 用 spec.palette + weapon

    from voxel_dsl import VoxelBuilder
    from voxel_tech_lib import Proportions, Joint, MountPoint
    p = Proportions.get('gundam_7head', spec.get('height_blocks', 22))
    palette = full_palette
    b = VoxelBuilder(origin, mirror_axis='x')

    # legs
    leg_h = p['leg']
    b.box(1, 0, -1, 2, 0, 1, palette['leg'])
    b.box(1, 1, -1, 2, 1, 1, palette['joint'])
    b.box(1, 2, 0, 2, 2+leg_h//2-1, 0, palette['leg'])
    Joint.ball(b, 2, 2+leg_h//2, 0, 1, palette['joint'])
    b.box(1, 3+leg_h//2, 0, 2, leg_h, 0, palette['leg'])
    Joint.cylinder(b, 2, leg_h+1, leg_h+1, 0, 1, palette['joint'])
    b.box(2, leg_h//2+2, -1, 2, leg_h//2+3, -1, palette['accent'])

    # pelvis
    pelvis_y = leg_h + 2
    b.box(0, pelvis_y, -1, 3, pelvis_y+1, 1, palette['body'])
    b.box(0, pelvis_y, -2, 0, pelvis_y+1, -2, palette['accent'])

    # torso
    torso_bot = pelvis_y + 2
    torso_top = torso_bot + p['torso']
    b.box(0, torso_bot, -1, 3, torso_top, 1, palette['body'])
    b.box(0, torso_top-2, -2, 0, torso_top-1, -2, palette['accent'])
    b.box(1, torso_top, -2, 2, torso_top, -2, palette['accent'])

    # shoulders
    sh_y = torso_top - 1
    b.box(4, sh_y, -1, 5, sh_y+1, 1, palette['shoulder'])
    b.set(5, sh_y+1, -1, palette['accent'])
    Joint.ball(b, 4, sh_y, 0, 1, palette['joint'])

    # arms
    arm_h = p['arm']
    b.box(4, sh_y-arm_h//2-1, 0, 4, sh_y-1, 0, palette['arm'])
    Joint.ball(b, 4, sh_y-arm_h//2-1, 0, 1, palette['joint'])
    b.box(4, sh_y-arm_h, 0, 4, sh_y-arm_h//2-2, 0, palette['arm'])

    # head
    neck_y = torso_top + 1
    b.box(0, neck_y, 0, 0, neck_y, 0, palette['joint'])  # 颈
    head_y = neck_y + 1
    head_size = p['head']
    b.box(-1, head_y, -1, 1, head_y+head_size-1, 1, palette['head'])
    b.box(-1, head_y+head_size//2, -2, 1, head_y+head_size//2+1, -2, palette['mask'])  # 面罩
    # 头顶天线
    b.set(0, head_y+head_size, 0, palette['antenna'])
    b.set(0, head_y+head_size+1, 0, palette['antenna'])

    # weapon @ right hand
    weapon = spec.get('weapon', 'none')
    if weapon and weapon != 'none':
        hand_xyz = (5, sh_y-arm_h, 0)
        MountPoint.attach_weapon(b, hand_xyz, weapon, palette, mirror=False)

    return b, palette

def cmds_from_builder(b):
    return [f"setblock {x} {y} {z} {block}" for (x,y,z), block in sorted(b.blocks.items())]

def run_rcon(cmds):
    ok = 0
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        for c in cmds:
            try: r.command(c); ok += 1
            except: pass
    return ok

def end_to_end(prompt, origin=(-600, 80, -800)):
    print(f"[1/3] NLP→char spec: '{prompt}'")
    spec = nlp_to_char_spec(prompt)
    if not spec or 'error' in spec:
        print(f"❌ {spec}"); return None
    print(json.dumps(spec, ensure_ascii=False, indent=2))

    print(f"\n[2/3] build @ origin {origin}")
    b, palette = build_character(spec, origin)
    cmds = cmds_from_builder(b)
    print(f"   {len(cmds)} blocks")

    print(f"\n[3/3] RCON build...")
    t0 = time.time()
    ok = run_rcon(cmds)
    dt = time.time() - t0
    print(f"   {ok}/{len(cmds)} OK in {dt:.1f}s")

    ts = time.strftime('%Y%m%d-%H%M%S')
    out_p = f'/Users/coco/mcstory/outputs/char_{spec["id"]}_{ts}.json'
    json.dump({
        'prompt':prompt,'spec':spec,'origin':list(origin),
        'cmds_total':len(cmds),'rcon_ok':ok,'palette_resolved':palette,'ts':ts,
    }, open(out_p,'w'), ensure_ascii=False, indent=2)
    print(f"   → {out_p}")
    return {'spec':spec,'origin':list(origin),'cmds_total':len(cmds),'rcon_ok':ok}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: nlp_to_character.py '一句话角色' [x y z]"); sys.exit(1)
    prompt = sys.argv[1]
    origin = tuple(int(x) for x in sys.argv[2:5]) if len(sys.argv) >= 5 else (-600, 80, -800)
    end_to_end(prompt, origin)
