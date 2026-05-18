#!/usr/bin/env python3
"""gate1_judge_death_min.py — 苏白+沈砚最小画面 + 一个动作 (村民低头)
关 1: superflat + 牢笼 + 村民 + 玩家举斧 (sprite=zombie 持 iron_axe item_frame)
关 3: 一个动作 — 村民低头 (RCON tp pitch=45 → data get Rotation 验证)
失败逐条落盘, PASS 不落只 summary.
"""
import json, time, re, os
from mcrcon import MCRcon

OUT = '/Users/coco/mcstory/outputs/gate1_judge_death_min'
os.makedirs(OUT, exist_ok=True)
TS = time.strftime('%Y%m%d-%H%M%S')

# 选一块远离之前 build 的干净区域 (y=80 superflat 平面)
OX, OY, OZ = -40, 79, -240
fails = []

def w(label, ok, detail):
    if not ok:
        fails.append({'label': label, 'detail': detail})
    return ok

with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
    print(f"[setup] 清场 @ {OX},{OY},{OZ} 区域")
    r.command(f"kill @e[type=villager,distance=..30]")
    r.command(f"kill @e[type=zombie,distance=..30]")
    r.command(f"kill @e[type=item_frame,distance=..30]")
    r.command(f"fill {OX-10} {OY} {OZ-10} {OX+10} {OY+8} {OZ+10} air")

    # === 关 1: superflat + 牢笼 ===
    print("\n[关 1] superflat + 牢笼 build")
    build_cmds = [
        # superflat 底座 (15x15 grass_block at y=79)
        f"fill {OX-7} {OY} {OZ-7} {OX+7} {OY} {OZ+7} grass_block",
        # 牢笼地板 (内部 polished_blackstone)
        f"fill {OX-2} {OY+1} {OZ-2} {OX+2} {OY+1} {OZ+2} polished_blackstone",
        # 牢笼 4 面 iron_bars
        f"fill {OX-2} {OY+2} {OZ-2} {OX+2} {OY+4} {OZ-2} iron_bars",  # 北
        f"fill {OX-2} {OY+2} {OZ+2} {OX+2} {OY+4} {OZ+2} iron_bars",  # 南
        f"fill {OX-2} {OY+2} {OZ-2} {OX-2} {OY+4} {OZ+2} iron_bars",  # 西
        f"fill {OX+2} {OY+2} {OZ-2} {OX+2} {OY+4} {OZ+2} iron_bars",  # 东
        # 顶板 (留出空让 entity 可见)
        f"fill {OX-2} {OY+5} {OZ-2} {OX+2} {OY+5} {OZ+2} oak_slab",
        # 反转牌
        f"setblock {OX} {OY+1} {OZ+3} oak_sign{{front_text:{{messages:['\"判决\"','\"\"','\"\"','\"\"']}}}}",
    ]
    for c in build_cmds:
        out = r.command(c)
        if 'Successfully' not in out and 'Changed' not in out and 'Filled' not in out and 'Set the block' not in out:
            w(f"build_fail: {c[:50]}", False, out[:100])

    print("\n[白盒 room]")
    # whitebox_room 7 检查
    room_probes = [
        (OX, OY, OZ, "grass_block", "底座中心"),
        (OX+5, OY, OZ, "grass_block", "底座边"),
        (OX, OY+1, OZ, "polished_blackstone", "牢笼地板"),
        (OX-2, OY+3, OZ, "iron_bars", "西面栏杆"),
        (OX+2, OY+3, OZ, "iron_bars", "东面栏杆"),
        (OX, OY+5, OZ, "oak_slab", "顶板"),
        (OX, OY+1, OZ+3, "oak_sign", "反转牌"),
    ]
    room_ok = 0
    for x,y,z,blk,desc in room_probes:
        out = r.command(f"execute if block {x} {y} {z} {blk}").strip()
        ok = "Test passed" in out
        if ok: room_ok += 1
        else: w(f"room_fail: {desc} expect {blk}", False, out[:80])
        print(f"  {'✓' if ok else '✗'} ({x:>3},{y:>2},{z:>4}) {desc:<15} expect {blk:<22} → {out[:50]}")
    print(f"[room] {room_ok}/{len(room_probes)} PASS")

    # === 关 2: 放角色 + 道具 ===
    print("\n[关 2] 村民(牢笼内) + 僵尸(牢笼外) + 铁斧(item_frame)")
    r.command(f"summon villager {OX} {OY+2} {OZ} {{NoAI:1b,Silent:1b,PersistenceRequired:1b,Invulnerable:1b,CustomName:'{{\"text\":\"继任者\"}}',CustomNameVisible:1b,Rotation:[0.0f,0.0f]}}")
    r.command(f"summon zombie {OX} {OY+1} {OZ+4} {{NoAI:1b,Silent:1b,PersistenceRequired:1b,Invulnerable:1b,CustomName:'{{\"text\":\"执行者\"}}',CustomNameVisible:1b,HandItems:[{{id:\"minecraft:iron_axe\",Count:1b}},{{}}]}}")
    # item_frame 稳定展示斧 (面朝南挂在执行者手位)
    r.command(f"summon item_frame {OX} {OY+2} {OZ+4} {{Facing:0b,Item:{{id:\"minecraft:iron_axe\",Count:1b}}}}")
    time.sleep(0.5)

    print("\n[白盒 cast]")
    cast_probes = [
        (f"execute if entity @e[type=villager,distance=..5]", "villager 在牢笼附近"),
        (f"execute if entity @e[type=villager,name=\"继任者\"]", "villager 命名继任者"),
        (f"execute if entity @e[type=zombie,distance=..6]", "zombie 在附近"),
        (f"execute if entity @e[type=zombie,name=\"执行者\"]", "zombie 命名执行者"),
        (f"execute if entity @e[type=item_frame,distance=..5]", "item_frame 存在"),
    ]
    cast_ok = 0
    for cmd, desc in cast_probes:
        out = r.command(cmd).strip()
        ok = "Test passed" in out
        if ok: cast_ok += 1
        else: w(f"cast_fail: {desc}", False, out[:80])
        print(f"  {'✓' if ok else '✗'} {desc:<22} → {out[:50]}")
    # 验证 villager Rotation NBT (初始 0)
    out = r.command(f"data get entity @e[type=villager,limit=1,sort=nearest] Rotation").strip()
    print(f"  villager Rotation t=0: {out[:80]}")
    rot_t0 = out
    # 验证 item_frame 持斧
    out = r.command(f"data get entity @e[type=item_frame,limit=1,sort=nearest] Item.id").strip()
    print(f"  item_frame Item.id: {out[:80]}")
    if 'iron_axe' in out: cast_ok += 1
    else: w(f"item_frame_axe_fail", False, out[:80])
    print(f"[cast] {cast_ok}/{len(cast_probes)+1} PASS")

    # === 关 3: 一个动作 = 村民低头 ===
    print("\n[关 3] 动作: 村民低头 /tp pitch=45")
    r.command(f"tp @e[type=villager,limit=1,sort=nearest] ~ ~ ~ 0 45")
    time.sleep(0.5)
    out = r.command(f"data get entity @e[type=villager,limit=1,sort=nearest] Rotation").strip()
    rot_t1 = out
    print(f"  villager Rotation t=1 (after tp pitch=45): {out[:80]}")
    # 抽 pitch 值
    m = re.search(r'pitch:\s*([\-\d\.]+)', out) or re.search(r'(-?\d+\.\d+)f\]', out)
    pitch_now = float(m.group(1)) if m else None
    if pitch_now is not None and 40 < pitch_now < 50:
        action_ok = True
        print(f"  ✓ 动作可见 (数据级): pitch={pitch_now} ∈ (40,50) — 村民低头成功")
    else:
        action_ok = False
        w(f"action_fail: pitch not in (40,50)", False, f"pitch={pitch_now} raw={out[:80]}")
        print(f"  ✗ 动作不成立: pitch={pitch_now}")

# 汇总
summary = {
    'ts': TS,
    'origin': [OX, OY, OZ],
    'room': {'pass': room_ok, 'total': len(room_probes)},
    'cast': {'pass': cast_ok, 'total': len(cast_probes)+1},
    'action': {'pass': action_ok, 'rot_t0': rot_t0[:200], 'rot_t1': rot_t1[:200], 'pitch_now': pitch_now},
    'fails': fails,
}
json.dump(summary, open(f'{OUT}/{TS}_summary.json','w'), ensure_ascii=False, indent=2)
print(f"\n=== 总结 ===")
print(f"  room: {room_ok}/{len(room_probes)} | cast: {cast_ok}/{len(cast_probes)+1} | action: {'PASS' if action_ok else 'FAIL'}")
print(f"  失败沉淀: {len(fails)} 条 → {OUT}/{TS}_summary.json")
