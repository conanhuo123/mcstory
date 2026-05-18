#!/usr/bin/env python3
"""translate.py — 剧本 JSON → mineflayer 命令序列 (JSON)"""
import sys, json, os

# 模板 action → mineflayer 命令映射
ACTION_MAP = {
    # 走位类
    "walk_to": lambda a: {"type": "goto", "actor": a["actor"], "xyz": a.get("to_xyz", [0,64,0])},
    "walk": lambda a: {"type": "goto", "actor": a["actor"], "xyz": a.get("to_xyz", [0,64,0])},
    "stand": lambda a: {"type": "look", "actor": a["actor"], "xyz": a.get("to_xyz", [0,64,0])},
    # 视线类
    "look_at": lambda a: {"type": "look", "actor": a["actor"], "xyz": a.get("to_xyz", [0,64,0])},
    # 互动类
    "attack": lambda a: {"type": "attack", "actor": a["actor"], "target": a.get("target", "nearest")},
    "use": lambda a: {"type": "use", "actor": a["actor"], "item": a.get("item", "hand")},
    "place": lambda a: {"type": "place_block", "actor": a["actor"], "xyz": a.get("to_xyz"), "block": a.get("block", "stone")},
    # 说话类 (用 /tellraw 出气泡)
    "say": lambda a: {"type": "tellraw", "actor": a["actor"], "text": a.get("text", "...")},
    "shout": lambda a: {"type": "tellraw", "actor": a["actor"], "text": a.get("text", "..."), "color": "red"},
    # 特殊类 (mod / 命令模拟)
    "explode": lambda a: {"type": "particle", "particle": "explosion", "xyz": a.get("to_xyz")},
    "summon_block": lambda a: {"type": "setblock", "xyz": a.get("to_xyz"), "block": a.get("block", "chest")},
    # 默认: 未知动作降级为 look
    "_default": lambda a: {"type": "look", "actor": a["actor"], "xyz": a.get("to_xyz", [0,64,0])},
}

# 镜头 → ReplayMod 关键帧 (简化版, 给秒级位置/角度)
CAMERA_PRESETS = {
    "wide":          {"pos": [10, 70, 10], "look_at": [0, 64, 0], "fov": 70},
    "medium":        {"pos": [3, 66, 3],   "look_at": [0, 64, 0], "fov": 60},
    "closeup_face":  {"pos": [1, 65, 1],   "look_at": [0, 65, 0], "fov": 50},
    "closeup_object":{"pos": [1, 64.5, 1], "look_at": [0, 64, 0], "fov": 40},
    "freeze_zoom":   {"pos": [2, 65, 2],   "look_at": [0, 64.5, 0], "fov": 55, "freeze": True, "zoom_to": 50},
}

def translate(script):
    """script JSON → 可执行命令序列"""
    out = {
        "scene": script["scene"],
        "spawn_chars": script["characters"],
        "title": script.get("title", ""),
        "subtitle_color": script.get("subtitle_color", "yellow"),
        "timeline": []
    }
    for shot in script["shots"]:
        # 兼容两种格式: {start_sec, end_sec} (parse.py) 或 {t: [s, e]} (samples/)
        if "start_sec" in shot:
            s, e = shot["start_sec"], shot["end_sec"]
        elif "t" in shot and isinstance(shot["t"], list):
            s, e = shot["t"][0], shot["t"][1]
        else:
            continue
        cam = CAMERA_PRESETS.get(shot["camera"], CAMERA_PRESETS["medium"])
        # 镜头切换
        out["timeline"].append({"t": s, "type": "camera", "preset": shot["camera"], **cam})
        # 角色动作
        for a in shot.get("actions", []):
            act_name = a["action"]
            # 找最接近的 action mapping
            mapped = None
            for key in ACTION_MAP:
                if key != "_default" and (key in act_name.lower() or act_name.lower().startswith(key)):
                    mapped = ACTION_MAP[key](a)
                    break
            if not mapped:
                mapped = ACTION_MAP["_default"](a)
            mapped["t"] = s + 0.5  # 动作在镜头切换 0.5s 后触发
            out["timeline"].append(mapped)
        # 字幕 + 旁白
        if shot.get("subtitle"):
            out["timeline"].append({"t": s, "type": "subtitle", "text": shot["subtitle"], "end_t": e})
        if shot.get("voiceover"):
            out["timeline"].append({"t": s + 0.3, "type": "voiceover", "text": shot["voiceover"], "end_t": e})
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: translate.py script.json [out.json]"); sys.exit(1)
    script = json.load(open(sys.argv[1]))
    timeline = translate(script)
    out_path = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].replace(".json", "_timeline.json")
    json.dump(timeline, open(out_path, "w"), ensure_ascii=False, indent=2)
    print(f"✓ {out_path}")
    print(f"  scene: {timeline['scene']}")
    print(f"  characters: {timeline['spawn_chars']}")
    print(f"  timeline events: {len(timeline['timeline'])}")
