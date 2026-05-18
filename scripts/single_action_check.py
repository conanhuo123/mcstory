#!/usr/bin/env python3
"""single_action_check.py — 陆远 03:01 verdict: 关 3 单动作.
primary: 村民低头 (Rotation pitch 0→45 RCON 数据级)
fallback: ArmorStand 举斧 (Pose.RightArm 0→-90 数据级)
只输出 JSON 报告, 不拍视频, 不跑剧情, 不发散.
"""
import json, re, time, os
from mcrcon import MCRcon

OUT = '/Users/coco/mcstory/outputs/single_action_check'
os.makedirs(OUT, exist_ok=True)
TS = time.strftime('%Y%m%d-%H%M%S')
OX, OY, OZ = -40, 79, -240
fails = []

def fail(label, detail):
    fails.append({'label': label, 'detail': detail[:200]})

with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
    print(f"[setup] @ origin {OX},{OY},{OZ}")
    r.command(f"kill @e[type=armor_stand,distance=..30]")
    r.command(f"kill @e[type=villager,distance=..30]")

    # === primary: 村民低头 ===
    print("\n[A] primary — villager low_head (pitch 0→45)")
    r.command(f"summon villager {OX} {OY+2} {OZ} {{NoAI:1b,Silent:1b,PersistenceRequired:1b,Invulnerable:1b,CustomName:'{{\"text\":\"继任者\"}}',CustomNameVisible:1b,Rotation:[0.0f,0.0f]}}")
    time.sleep(0.5)
    rot_t0 = r.command(f"data get entity @e[type=villager,name=\"继任者\",limit=1] Rotation").strip()
    print(f"  t0 Rotation: {rot_t0[:80]}")
    r.command(f"tp @e[type=villager,name=\"继任者\",limit=1] ~ ~ ~ 0 45")
    time.sleep(0.4)
    rot_t1 = r.command(f"data get entity @e[type=villager,name=\"继任者\",limit=1] Rotation").strip()
    print(f"  t1 Rotation: {rot_t1[:80]}")
    m = re.search(r'[\[\,]\s*(-?\d+\.\d+)f\s*\]', rot_t1)
    pitch_t1 = float(m.group(1)) if m else None
    a_pass = pitch_t1 is not None and 40 < pitch_t1 < 50
    if a_pass:
        print(f"  ✓ primary PASS: pitch_t1={pitch_t1} ∈ (40,50)")
    else:
        fail("primary_lowhead_fail", f"pitch_t1={pitch_t1} raw={rot_t1[:100]}")
        print(f"  ✗ primary FAIL pitch_t1={pitch_t1}")

    # === fallback: ArmorStand 举斧 ===
    print("\n[B] fallback — armor_stand swing_axe (RightArm Pose 0→-90)")
    r.command(f"summon armor_stand {OX+3} {OY+1} {OZ} {{ShowArms:1b,NoBasePlate:1b,Invulnerable:1b,Tags:[\"axswing\"],HandItems:[{{id:\"minecraft:iron_axe\",Count:1b}},{{}}],Pose:{{RightArm:[0f,0f,0f]}},CustomName:'{{\"text\":\"执行者\"}}',CustomNameVisible:1b}}")
    time.sleep(0.5)
    pose_t0 = r.command(f"data get entity @e[type=armor_stand,tag=axswing,limit=1] Pose").strip()
    print(f"  t0 Pose: {pose_t0[:120]}")
    # 修改 RightArm 抬起 (-90 0 0 = 手臂向前/上)
    r.command(f"data merge entity @e[type=armor_stand,tag=axswing,limit=1] {{Pose:{{RightArm:[-90f,0f,0f]}}}}")
    time.sleep(0.4)
    pose_t1 = r.command(f"data get entity @e[type=armor_stand,tag=axswing,limit=1] Pose").strip()
    print(f"  t1 Pose: {pose_t1[:120]}")
    m2 = re.search(r'RightArm:\s*\[\s*(-?\d+\.\d+)f', pose_t1)
    rarm_t1 = float(m2.group(1)) if m2 else None
    b_pass = rarm_t1 is not None and -95 < rarm_t1 < -85
    if b_pass:
        print(f"  ✓ fallback PASS: RightArm.x={rarm_t1} ∈ (-95,-85)")
    else:
        fail("fallback_swing_fail", f"rarm_t1={rarm_t1} raw={pose_t1[:120]}")
        print(f"  ✗ fallback FAIL rarm_t1={rarm_t1}")
    # 也验证 HandItems 持斧
    hi = r.command(f"data get entity @e[type=armor_stand,tag=axswing,limit=1] HandItems[0].id").strip()
    print(f"  HandItems[0].id: {hi[:80]}")
    axe_ok = 'iron_axe' in hi
    if not axe_ok: fail("fallback_axe_missing", hi[:80])

summary = {
    'ts': TS,
    'primary': {'name': 'villager_lowhead', 'pass': a_pass, 'rot_t0': rot_t0[:120], 'rot_t1': rot_t1[:120], 'pitch_t1': pitch_t1},
    'fallback': {'name': 'armor_stand_swing_axe', 'pass': b_pass and axe_ok, 'pose_t0': pose_t0[:120], 'pose_t1': pose_t1[:120], 'rarm_t1': rarm_t1, 'axe_present': axe_ok},
    'fails': fails,
}
json.dump(summary, open(f'{OUT}/{TS}_summary.json','w'), ensure_ascii=False, indent=2)
print(f"\n=== single_action_check ===")
print(f"  primary (低头): {'PASS' if a_pass else 'FAIL'}")
print(f"  fallback (举斧): {'PASS' if (b_pass and axe_ok) else 'FAIL'}")
print(f"  失败沉淀: {len(fails)} 条 → {OUT}/{TS}_summary.json")
