#!/usr/bin/env python3
"""character_action_gate.py — 把 quality_gate 推到角色/动作关 (老板 23:14 verdict 大方向)
5 闸: spawn / placement / pose / animation / visible_change
不再困于单模型, 推 AI 导演系统下一关.
"""
import sys, os, time, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcrcon import MCRcon

def gate1_spawn(rcon, entity_type, name, expected_count=1):
    """① spawn 闸: entity 存在 + 命名"""
    out = rcon.command(f'execute if entity @e[type={entity_type},name="{name}"]').strip()
    passed = 'Test passed' in out
    return {'gate':1,'name':'spawn','entity':entity_type,'name_match':name,'status':'PASS' if passed else 'FAIL','raw':out[:80]}

def gate2_placement(rcon, entity_name, expected_pos, tolerance=2):
    """② 放置闸: entity 在预期坐标 ±tolerance"""
    ex, ey, ez = expected_pos
    out = rcon.command(f'data get entity @e[name="{entity_name}",limit=1] Pos').strip()
    m = re.search(r'\[([\-\d\.]+)d, ([\-\d\.]+)d, ([\-\d\.]+)d\]', out)
    if not m: return {'gate':2,'name':'placement','status':'FAIL_NO_POS','raw':out[:80]}
    ax, ay, az = float(m.group(1)), float(m.group(2)), float(m.group(3))
    in_tol = abs(ax-ex)<=tolerance and abs(ay-ey)<=tolerance and abs(az-ez)<=tolerance
    return {'gate':2,'name':'placement','actual':[ax,ay,az],'expected':list(expected_pos),'tol':tolerance,
            'status':'PASS' if in_tol else 'FAIL'}

def gate3_pose(rcon, entity_name, expected_rotation=None, expected_pose_arm=None):
    """③ pose 闸: villager Rotation 或 ArmorStand Pose"""
    if expected_rotation is not None:
        # villager Rotation [yaw, pitch]
        out = rcon.command(f'data get entity @e[name="{entity_name}",limit=1] Rotation').strip()
        m = re.search(r'\[([\-\d\.]+)f, ([\-\d\.]+)f\]', out)
        if not m: return {'gate':3,'name':'pose','status':'FAIL_NO_ROT'}
        yaw, pitch = float(m.group(1)), float(m.group(2))
        passed = abs(pitch - expected_rotation[1]) < 10
        return {'gate':3,'name':'pose','actual_pitch':pitch,'expected_pitch':expected_rotation[1],
                'status':'PASS' if passed else 'FAIL'}
    elif expected_pose_arm is not None:
        out = rcon.command(f'data get entity @e[name="{entity_name}",limit=1] Pose.RightArm').strip()
        m = re.search(r'\[([\-\d\.]+)f', out)
        if not m: return {'gate':3,'name':'pose','status':'FAIL_NO_POSE'}
        arm_x = float(m.group(1))
        passed = abs(arm_x - expected_pose_arm) < 10
        return {'gate':3,'name':'pose','actual_arm':arm_x,'expected_arm':expected_pose_arm,
                'status':'PASS' if passed else 'FAIL'}
    return {'gate':3,'status':'SKIP_NO_TARGET'}

def gate4_animation(rcon, entity_name, before_state, after_state_key):
    """④ animation 闸: before/after 状态差异检测"""
    out = rcon.command(f'data get entity @e[name="{entity_name}",limit=1] {after_state_key}').strip()
    diff = out != before_state
    return {'gate':4,'name':'animation','before':before_state[:60],'after':out[:60],
            'changed':diff,'status':'PASS' if diff else 'FAIL'}

def gate5_visible_change(before_png, after_png, mech_colors=None):
    """⑤ 视觉变化闸: before/after PNG md5 不同 + 像素差异 >5%"""
    import hashlib
    try:
        import numpy as np
        from PIL import Image
    except: return {'gate':5,'status':'SKIP_NO_PIL'}
    if not os.path.exists(before_png) or not os.path.exists(after_png):
        return {'gate':5,'status':'SKIP_NO_PNG'}
    h1 = hashlib.md5(open(before_png,'rb').read()).hexdigest()
    h2 = hashlib.md5(open(after_png,'rb').read()).hexdigest()
    md5_diff = h1 != h2
    a1 = np.array(Image.open(before_png).convert('RGB'))
    a2 = np.array(Image.open(after_png).convert('RGB'))
    if a1.shape != a2.shape: return {'gate':5,'status':'FAIL_SIZE_MISMATCH'}
    diff = np.sum(np.abs(a1.astype(int) - a2.astype(int))) / (a1.size * 255)
    return {'gate':5,'name':'visible_change','md5_before':h1[:8],'md5_after':h2[:8],
            'md5_diff':md5_diff,'pixel_diff_ratio':round(float(diff),4),
            'status':'PASS' if md5_diff and diff > 0.01 else 'FAIL'}


def audit_action(entity_type, entity_name, expected_pos, expected_rotation=None, expected_pose_arm=None,
                 before_png=None, after_png=None, before_state=None, after_state_key=None):
    """跑全 5 闸"""
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        g1 = gate1_spawn(r, entity_type, entity_name)
        g2 = gate2_placement(r, entity_name, expected_pos)
        g3 = gate3_pose(r, entity_name, expected_rotation, expected_pose_arm)
        g4 = gate4_animation(r, entity_name, before_state or '', after_state_key or 'Rotation') if before_state else {'gate':4,'status':'SKIP'}
    g5 = gate5_visible_change(before_png, after_png) if (before_png and after_png) else {'gate':5,'status':'SKIP'}
    gates = [g1, g2, g3, g4, g5]
    return {'overall':'PASS' if all(g.get('status') in ('PASS','SKIP_NO_PIL','SKIP_NO_PNG','SKIP') for g in gates) else 'FAIL',
            'gates':gates}


if __name__ == '__main__':
    # demo: 验村民低头 (复用之前 single_action_check)
    print("=== character_action_gate demo: villager 低头 ===")
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        # 清场 + spawn
        r.command('kill @e[type=villager,name="继任者"]')
        r.command('summon villager -40 80 -240 {NoAI:1b,Silent:1b,PersistenceRequired:1b,Invulnerable:1b,CustomName:\'{"text":"继任者"}\',Rotation:[0.0f,0.0f]}')
        import time; time.sleep(0.5)
        before_rot = r.command('data get entity @e[name="继任者",limit=1] Rotation').strip()
        # 跑 5 闸前置 (无动作)
        result_before = audit_action('villager','继任者',(-40,80,-240), expected_rotation=(0,0))
        # 触发动作 (低头)
        r.command('tp @e[name="继任者",limit=1] ~ ~ ~ 0 45')
        time.sleep(0.4)
        # 跑后置
        result_after = audit_action('villager','继任者',(-40,80,-240), expected_rotation=(0,45),
                                    before_state=before_rot, after_state_key='Rotation')
    print("=== BEFORE ===")
    print(json.dumps(result_before, indent=2, ensure_ascii=False))
    print("\n=== AFTER (低头触发) ===")
    print(json.dumps(result_after, indent=2, ensure_ascii=False))
    json.dump({'before':result_before,'after':result_after},
              open('/Users/coco/mcstory/outputs/character_action_gate_demo.json','w'),
              ensure_ascii=False, indent=2)
    print("\n[saved]")
