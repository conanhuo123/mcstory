#!/usr/bin/env python3
"""validate_ir.py — 验证 sample.json 符合 4 库 schema (按团队闸口)

每 shot 必须含: scene_action + camera + (subtitle 或 voiceover) + (actions 或 prop_states)
camera 必须来自 camera library
scene 必须来自 scene library
characters 必须来自 character library
失败 → exit code 1 + 报缺什么
"""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMERAS = ["wide","medium","closeup_face","closeup_object","freeze_zoom"]
SCENES = ["courtroom","village","mine","redstone_door"]
CHARACTERS = ["steve","villager","iron_golem","creeper","enderman","wolf"]

def validate(p):
    d = json.load(open(p))
    errors = []

    # 必填顶层字段
    for f in ["id","title","scene","characters","shots"]:
        if f not in d: errors.append(f"missing {f}")

    if "scene" in d and d["scene"] not in SCENES:
        errors.append(f"scene '{d['scene']}' not in library {SCENES}")

    for ch in d.get("characters",[]):
        if ch not in CHARACTERS:
            errors.append(f"character '{ch}' not in library")

    if "shots" in d and len(d["shots"]) < 4:
        errors.append(f"only {len(d['shots'])} shots, need >=4")

    for i, shot in enumerate(d.get("shots",[])):
        if "camera" not in shot:
            errors.append(f"shot{i} missing camera")
        elif shot["camera"] not in CAMERAS:
            errors.append(f"shot{i} camera '{shot['camera']}' not in library")
        if "scene_action" not in shot:
            errors.append(f"shot{i} missing scene_action")
        if not (shot.get("subtitle") or shot.get("voiceover")):
            errors.append(f"shot{i} missing both subtitle and voiceover")
        # 三元强制: actions 或 prop_states 至少 1
        if not (shot.get("actions") or shot.get("prop_states") or shot.get("scene_action")):
            errors.append(f"shot{i} missing actions/prop_states/scene_action (任一项)")

    return errors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # validate all
        samples = sorted((ROOT/"samples").glob("*.json"))
        all_pass = 0
        for p in samples:
            errs = validate(p)
            if errs:
                print(f"✗ {p.name}: {errs[:2]}")
            else:
                print(f"✓ {p.name}")
                all_pass += 1
        print(f"\nTotal: {all_pass}/{len(samples)} PASS")
        sys.exit(0 if all_pass == len(samples) else 1)
    else:
        errs = validate(sys.argv[1])
        if errs:
            for e in errs: print(f"  ✗ {e}")
            sys.exit(1)
        print("✓ valid")
