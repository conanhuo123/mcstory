#!/usr/bin/env python3
"""parse.py — 输入一句话, GPT 输出结构化 30s 剧本 JSON"""
import sys, json, os, urllib.request
sys.path.insert(0, '/Users/coco/video_factory')

GPT55_URL = "https://ax-useast-resource.services.ai.azure.com/api/projects/ax-useast/openai/v1/responses"
GPT55_MODEL = "gpt-5.5-standard"
AUTH = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")

def get_key():
    d = json.load(open(AUTH))
    for p in d.get("profiles", {}).values():
        if p.get("provider") == "co-azure-gpt55":
            return p["key"]
    return None

def parse_prompt(user_prompt):
    """一句话 → 30s 剧本结构 (4 拍式: 3+15+8+4)"""
    # 加载模板
    scenes = json.load(open(os.path.expanduser('~/mcstory/templates/scenes/scenes.json')))
    chars = json.load(open(os.path.expanduser('~/mcstory/templates/characters/characters.json')))
    cams = json.load(open(os.path.expanduser('~/mcstory/templates/cameras/cameras.json')))

    system = f"""你是 MC 短剧导演. 输入一句话用户需求, 输出严格 JSON 格式的 30s 剧本.

可选场景: {[s['id'] for s in scenes['scenes']]}
可选角色: {[c['id'] for c in chars['characters']]}
可选镜头: {[c['id'] for c in cams['cameras']]}

输出 JSON 结构:
{{
  "scene": "courtroom|mine|village (或新自定义 id)",
  "characters": ["steve", "villager", ...],
  "build_cmds": [
    "fill -64 79 -194 -56 79 -190 polished_blackstone",
    "setblock -60 80 -190 oak_sign{{front_text:{{messages:[\\"\\"\\"]}}}}",
    "..."
  ],
  "scene_origin": [-60, 79, -190],
  "character_spawns": [
    {{"actor": "villager", "xyz": [-60, 80, -185]}},
    {{"actor": "iron_golem", "xyz": [-58, 80, -185]}}
  ],
  "shots": [...],
  "title": "封面主标题",
  "subtitle_color": "yellow|red"
}}

【v5.0 AI build (老板 22:11 拍板)】
- build_cmds: 你直接生成 8-15 条 /fill 或 /setblock 命令搭场景
- 命令格式 (不要加 / 前缀, cli_full 会自动加):
  - "fill <x1> <y1> <z1> <x2> <y2> <z2> <block>" — 填充矩形区
  - "setblock <x> <y> <z> <block>" — 单块
  - 坐标基于 scene_origin (e.g. -60, 79, -190 是 paper world 山地)
  - block 名: minecraft:polished_blackstone / quartz_block / oak_planks / oak_sign / iron_bars / water / lava / glass 等
- scene_origin: build 的中心坐标 [-60, 79, -190] 默认
- 旧 templates 不再用, 完全 GPT 生成场景

铁律: 30 秒, 4 拍 (3s 怪事/15s 追查/8s 误导/4s 反转), 用所选场景的角色/方块/特性.

【4 库引用 (v3.6 schema 接入)】
- 动作语法库 (schema/action_grammar.schema.json): 每 shot 的 scene_action 可引用 action_id 如 villager_kneel/creeper_glow/sign_reveal
- 镜头库 (schema/camera_library.schema.json): camera 字段从 [wide,medium,closeup_face,closeup_object,freeze_zoom] 选
- 场景库 (schema/scene_library.schema.json): scene 字段从已有场景选
- 道具/角色库 (schema/character_library.schema.json): characters 引用已有 mob

每 shot 字段 scene_action 写描述; 如能映射到现有 action_id 则在 actions 数组里追加 action_id + actor.

只输出 JSON, 无其他文字."""

    payload = json.dumps({
        "model": GPT55_MODEL,
        "instructions": system,
        "input": f"用户一句话需求: {user_prompt}"
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
                    # 剥离 markdown code block
                    if text.startswith("```"):
                        text = "\n".join(text.split("\n")[1:-1])
                    return json.loads(text)
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: parse.py '一句话'"); sys.exit(1)
    prompt = sys.argv[1]
    script = parse_prompt(prompt)
    print(json.dumps(script, ensure_ascii=False, indent=2))
