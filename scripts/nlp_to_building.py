#!/usr/bin/env python3
"""nlp_to_building.py — 一句话 → voxel spec → 真建筑 → 7 闸 → scene_library
GPT-5.5 (Azure, parse.py 同款 key) 解析一句话场景描述出 spec, 跑 voxel_dsl/module_library 真建.
"""
import sys, os, json, time, urllib.request, re, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel_dsl import VoxelBuilder
from building_dsl import Reference, ProportionFrame
from module_library import Foundation, Body, Decor
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

PRESET_BASES = list(Reference.PRESETS.keys())  # louvre/temple/skyscraper

MODULE_CATALOG = {
    'Foundation': ['slab', 'stepped', 'plaza_circle'],
    'Body': ['hollow_box', 'tower_layered'],
    'Decor': ['fountain', 'banner_row', 'carved_band'],
}

COMMON_BLOCKS = [
    'sandstone','smooth_sandstone','cut_sandstone','chiseled_sandstone',
    'stone','cobblestone','stone_bricks','mossy_stone_bricks','polished_andesite',
    'oak_log','oak_planks','dark_oak_log','dark_oak_planks','spruce_log','spruce_planks',
    'red_concrete','blue_concrete','gold_block','iron_block','quartz_block','smooth_quartz_block',
    'red_glazed_terracotta','glass','tinted_glass','light_gray_concrete','gray_concrete',
    'bone_block','end_stone','prismarine','dark_prismarine','glowstone','sea_lantern',
]

SYSTEM_PROMPT = f"""你是 MC 体素建筑师. 给定中文场景描述, 输出 JSON spec, 系统会用 voxel_dsl 真实建造.

可选 preset_base (取最接近, 不需要外形完全相同, 主要是 palette 基础):
  {PRESET_BASES}

可选 modules (按顺序执行, Foundation→Body→Decor):
  Foundation: {MODULE_CATALOG['Foundation']}
  Body: {MODULE_CATALOG['Body']}
  Decor: {MODULE_CATALOG['Decor']}

可选 palette blocks (palette_override 用):
  {COMMON_BLOCKS}

palette 字段语义:
  floor: 地板  main: 主墙  trim: 装饰带  deco: 雕刻装饰  pillar: 柱  roof: 屋顶
  roof_edge: 屋檐  centerpiece: 中央亮点  iron_frame: 框架  accent: 强调色

real_dim_m: 真实尺寸 (长 高 宽, 单位米=block). 例如教堂 25×18×15, 高塔 12×30×12, 大殿 50×20×30.

输出严格 JSON (无 markdown, 无解释):
{{
  "id": "<lowercase_snake_id_v1>",
  "name": "<中文名称>",
  "preset_base": "<{'|'.join(PRESET_BASES)}>",
  "real_dim_m": [<length>, <height>, <width>],
  "modules": ["Foundation.<x>", "Body.<x>", "Decor.<x>", ...],
  "palette_override": {{"main":"...","trim":"...","roof":"...","centerpiece":"..."}},
  "tags": ["..."],
  "design_note": "<一句话设计意图>"
}}

reject 不合理: 比如"建一个银河系" 输出 {{"error":"out_of_scope","reason":"..."}}.
"""

def nlp_to_spec(user_prompt):
    """调 GPT-5.5 把一句话变 voxel spec"""
    payload = json.dumps({
        "model": GPT55_MODEL,
        "instructions": SYSTEM_PROMPT,
        "input": f"用户场景描述: {user_prompt}"
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

def spec_to_builder(spec, origin):
    """spec → 跑 voxel_dsl/module_library, 返 (builder, palette, bbox).
    每个 module 用精确签名 dispatch (不同 module 参数不同)."""
    if 'error' in spec:
        raise ValueError(f"GPT rejected: {spec.get('reason')}")
    ref = Reference.get(spec['preset_base'])
    palette = dict(ref['palette'])
    palette.update(spec.get('palette_override', {}))
    L, H, W = ProportionFrame.from_real(spec['real_dim_m'], scale=1.0)
    b = VoxelBuilder(origin)

    DISPATCH = {
        'Foundation.slab':         lambda: Foundation.slab(b, L, W, palette),
        'Foundation.stepped':      lambda: Foundation.stepped(b, L, W, palette, steps=3),
        'Foundation.plaza_circle': lambda: Foundation.plaza_circle(b, max(L,W)//2, palette),
        'Body.hollow_box':         lambda: Body.hollow_box(b, L, H, W, palette),
        'Body.tower_layered':      lambda: Body.tower_layered(b, max(L,W), H, max(3, H//6), palette),
        'Decor.fountain':          lambda: Decor.fountain(b, 0, 0, max(2, min(L,W)//5), palette),
        'Decor.banner_row':        lambda: Decor.banner_row(b, H, L, palette, on='north'),
        'Decor.carved_band':       lambda: Decor.carved_band(b, H//2, L, palette),
    }

    for module_path in spec.get('modules', []):
        fn = DISPATCH.get(module_path)
        if not fn:
            print(f"[warn] unknown module {module_path}, skip")
            continue
        try:
            fn()
        except Exception as e:
            print(f"[warn] {module_path} failed: {e}")
    return b, palette, (L, H, W)

def builder_to_cmds(b):
    """提取 setblock 命令列表"""
    cmds = []
    for (x,y,z), block in sorted(b.blocks.items()):
        cmds.append(f"setblock {x} {y} {z} {block}")
    return cmds

def probe_real_ground(r, ox, oz):
    """探测 (ox,oz) 实际地面 y (从 95 往下扫第一个非 air)"""
    for y in range(95, 50, -1):
        o = r.command(f'execute if block {ox} {y} {oz} air').strip()
        if 'Test passed' not in o:
            return y
    return None

def ground_prep(r, origin, L, W, margin=3):
    """5 点采样 footprint 实际地面 + 外扩 margin grass platform + 清上空.
    返 build_origin_y = target_ground + 1 (build 从此 y 开始)."""
    ox, _, oz = origin
    half_l, half_w = L//2, W//2
    samples = [(ox, oz), (ox-half_l, oz-half_w), (ox+half_l, oz-half_w),
               (ox-half_l, oz+half_w), (ox+half_l, oz+half_w)]
    grounds = [probe_real_ground(r, x, z) for x,z in samples]
    grounds = [g for g in grounds if g is not None]
    if not grounds:
        return origin[1]  # fallback
    target = max(grounds)
    # fill grass platform 外扩 margin
    r.command(f"fill {ox-half_l-margin} {target} {oz-half_w-margin} {ox+half_l+margin} {target} {oz+half_w+margin} grass_block")
    # 清上空 (avoid 树/草杂物)
    r.command(f"fill {ox-half_l-margin} {target+1} {oz-half_w-margin} {ox+half_l+margin} {target+25} {oz+half_w+margin} air")
    return target + 1

def run_via_rcon(cmds, host='127.0.0.1', port=25575, password='mcstory123', prep_origin=None, prep_bbox=None):
    """跑 cmds. 若 prep_origin+prep_bbox 给, 先垫平 + 返 (ok, adjusted_origin_y)."""
    ok = 0
    adjusted_y = None
    with MCRcon(host, password, port=port) as r:
        if prep_origin and prep_bbox:
            L, _, W = prep_bbox
            adjusted_y = ground_prep(r, prep_origin, L, W)
        for c in cmds:
            try:
                r.command(c)
                ok += 1
            except: pass
    return ok, adjusted_y

def end_to_end(prompt, origin=(-300, 80, -300), prep_ground=True):
    print(f"[1/5] NLP→spec: '{prompt}'")
    spec = nlp_to_spec(prompt)
    if not spec or 'error' in spec:
        print(f"❌ spec error: {spec}"); return None
    print(json.dumps(spec, ensure_ascii=False, indent=2))

    print(f"\n[2/5] spec→builder @ origin {origin} (preview, will adjust y)")
    # 先用 origin 占位算 bbox
    b_tmp, palette, (L, H, W) = spec_to_builder(spec, origin)
    print(f"   bbox preview {L}x{H}x{W}")

    if prep_ground:
        print(f"\n[3/5] probe real ground + lay grass platform...")
        with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
            real_y = ground_prep(r, origin, L, W)
        if real_y and real_y != origin[1]:
            origin = (origin[0], real_y, origin[2])
            print(f"   adjusted origin → {origin} (grass platform laid)")

    # 真重 build 用新 origin
    b, palette, (L, H, W) = spec_to_builder(spec, origin)
    cmds = builder_to_cmds(b)
    print(f"\n[4/5] RCON build {len(cmds)} blocks...")
    t0 = time.time()
    ok, _ = run_via_rcon(cmds)
    dt = time.time() - t0
    print(f"   {ok}/{len(cmds)} cmds OK in {dt:.1f}s ({100*ok/max(1,len(cmds)):.1f}%)")

    print(f"\n[5/5] save result")
    ts = time.strftime('%Y%m%d-%H%M%S')
    out = {
        'prompt': prompt,
        'spec': spec,
        'origin': list(origin),
        'bbox': [L, H, W],
        'cmds_total': len(cmds),
        'rcon_ok': ok,
        'palette_resolved': palette,
        'ts': ts,
    }
    out_path = f'/Users/coco/mcstory/outputs/nlp_{spec.get("id","unknown")}_{ts}.json'
    json.dump(out, open(out_path, 'w'), ensure_ascii=False, indent=2)
    print(f"   → {out_path}")
    return out

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: nlp_to_building.py '一句话' [origin_x origin_y origin_z]"); sys.exit(1)
    prompt = sys.argv[1]
    if len(sys.argv) >= 5:
        origin = tuple(int(x) for x in sys.argv[2:5])
    else:
        origin = (-300, 80, -300)
    end_to_end(prompt, origin)
