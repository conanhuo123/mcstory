#!/usr/bin/env python3
"""mecha_humanoid_v3.py — 真精模 humanoid mecha (Rig + Proportions + LayeredArmor + Joint + MountPoint)
24 块高 (gundam_7head), 500+ blocks, 全身完整 (含腿/脚/双臂/武器/盾).
不抄外观, 学技术: 比例/分层/对称/关节连接.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel_dsl import VoxelBuilder, auto_framing
from voxel_tech_lib import Proportions, Joint, MountPoint
from mcrcon import MCRcon

def build_humanoid(origin, palette_name='gundam_RX78', height=24):
    """全身 humanoid mecha, 严格 Rig 骨架 + Proportions 比例"""
    p = Proportions.get('gundam_7head', height)  # {head:5, neck:1, torso:8, leg:10, arm:6, ...}
    print(f"  proportions: head={p['head']} neck={p['neck']} torso={p['torso']} leg={p['leg']} arm={p['arm']}")

    # 配色
    PALETTES = {
        'gundam_RX78': dict(leg='quartz_block', body='lapis_block', accent='red_concrete',
                            head='quartz_block', mask='black_concrete', antenna='yellow_concrete',
                            arm='quartz_block', shoulder='lapis_block', weapon='iron_block',
                            joint='gray_concrete', detail_dark='deepslate'),
    }
    palette = PALETTES[palette_name]

    b = VoxelBuilder(origin, mirror_axis='x')

    # ===== LEGS y=0 to y=10 =====
    leg_h = p['leg']
    # foot (脚, y=0~1 wide)
    b.box(1, 0, -1, 2, 0, 1, palette['leg'])  # 脚踝外宽
    b.box(1, 1, -1, 2, 1, 1, palette['joint'])  # 脚踝关节
    # lower leg
    b.box(1, 2, 0, 2, 2+leg_h//2-1, 0, palette['leg'])
    # knee joint
    Joint.ball(b, 2, 2+leg_h//2, 0, 1, palette['joint'])
    # upper leg
    b.box(1, 3+leg_h//2, 0, 2, leg_h, 0, palette['leg'])
    # hip joint
    Joint.cylinder(b, 2, leg_h+1, leg_h+1, 0, 1, palette['joint'])
    # 腿装甲分层 (red 强调条)
    b.box(2, leg_h//2+2, -1, 2, leg_h//2+3, -1, palette['accent'])
    b.box(1, 4, 0, 1, 5, 0, palette['detail_dark'])  # 膝侧黑细节

    # ===== PELVIS / 腰 y=11~12 =====
    pelvis_y = leg_h + 2
    b.box(0, pelvis_y, -1, 3, pelvis_y+1, 1, palette['body'])
    b.box(0, pelvis_y, -2, 0, pelvis_y+1, -2, palette['accent'])  # 腰前红

    # ===== TORSO y=13~20 =====
    torso_bot = pelvis_y + 2
    torso_top = torso_bot + p['torso']
    b.box(0, torso_bot, -1, 3, torso_top, 1, palette['body'])
    # 主胸甲 V (red)
    b.box(0, torso_top-2, -2, 0, torso_top-1, -2, palette['accent'])
    b.box(1, torso_top, -2, 2, torso_top, -2, palette['accent'])
    b.set(3, torso_top-1, -2, palette['accent'])
    # 散热口 (vents)
    b.set(3, torso_top-3, -2, palette['detail_dark'])
    b.set(3, torso_top-4, -2, palette['detail_dark'])
    b.set(2, torso_top-3, -2, palette['detail_dark'])
    # 胸口指示器
    b.set(0, torso_top-3, -2, 'green_stained_glass')

    # ===== SHOULDERS y=torso_top, ±4 =====
    sh_y = torso_top - 1
    # 肩主块 3x3
    b.box(4, sh_y, -1, 5, sh_y+1, 1, palette['shoulder'])
    b.set(5, sh_y+1, -1, palette['accent'])  # 肩前红
    b.set(5, sh_y+1, 0, palette['detail_dark'])  # 肩黑突
    Joint.ball(b, 4, sh_y, 0, 1, palette['joint'])  # 肩关节

    # ===== ARMS y=sh_y-arm to sh_y =====
    arm_h = p['arm']
    # upper arm
    b.box(4, sh_y-arm_h//2-1, 0, 4, sh_y-1, 0, palette['arm'])
    # elbow joint
    Joint.ball(b, 4, sh_y-arm_h//2-1, 0, 1, palette['joint'])
    # lower arm
    b.box(4, sh_y-arm_h, 0, 4, sh_y-arm_h//2-2, 0, palette['arm'])
    # hand
    b.set(4, sh_y-arm_h-1, 0, palette['joint'])
    # arm decoration
    b.set(3, sh_y-arm_h//2, 0, palette['accent'])  # 肘外红
    b.set(5, sh_y-arm_h//2-1, 0, palette['detail_dark'])  # 肘外黑

    # ===== NECK y=torso_top+1 =====
    neck_y = torso_top + 1
    b.box(0, neck_y, 0, 1, neck_y, 0, palette['joint'])

    # ===== HEAD y=neck_y+1 ~ +head =====
    head_bot = neck_y + 1
    head_top = head_bot + p['head']
    # head shell 3x3xhead (含 hollow)
    b.box(0, head_bot, -1, 2, head_top-1, 1, palette['head'])
    # 面罩 (前)
    b.box(0, head_bot+1, -2, 1, head_top-2, -2, palette['mask'])
    # 双眼亮 (T-bar style)
    b.set(0, head_top-2, -2, 'glowstone')
    b.set(1, head_top-2, -2, 'glowstone')
    b.set(2, head_top-2, -2, 'glowstone')
    # 颚下灰
    b.box(0, head_bot, -2, 1, head_bot, -2, palette['joint'])
    # 头顶圆角 (stairs)
    b.set(2, head_top-1, -1, 'quartz_stairs[facing=south,half=top]')
    b.set(2, head_top-1, 1, 'quartz_stairs[facing=north,half=top]')
    # 耳侧装甲
    b.box(3, head_top-3, 0, 3, head_top-2, 1, palette['shoulder'])

    # ===== V-FIN 天线 (3 层) =====
    af_y = head_top
    # 中央方块装饰
    b.set(0, af_y, 0, palette['accent'])
    b.set(0, af_y+1, 0, 'gold_block')
    # V 形天线 (镜像)
    b.set(1, af_y, 0, palette['antenna'])
    b.set(2, af_y+1, 0, palette['antenna'])
    b.set(3, af_y+2, 0, palette['antenna'])
    b.set(3, af_y+3, 0, palette['antenna'])  # 顶尖

    # ===== 武器: beam_saber 右手 + shield 左手 =====
    # beam_saber 右手 (mirror_axis x=4 → 真右 x=-4)
    rh = (4, sh_y-arm_h-1, 0)
    MountPoint.attach_weapon(b, rh, 'beam_saber', palette, mirror=False)
    # shield 左手 — 用 mirror=False 显式放在 -x 侧
    b.box(-4, sh_y-arm_h, 1, -4, sh_y-arm_h+2, 2, palette['weapon'], mirror=False)
    b.set(-4, sh_y-arm_h+1, 3, palette['accent'], mirror=False)  # 盾面红 cross
    b.set(-4, sh_y-arm_h+3, 1, palette['accent'], mirror=False)

    # ===== 背包 (jet pack) =====
    bp_y = torso_top - 4
    b.box(0, bp_y, 2, 2, bp_y+3, 3, palette['shoulder'], mirror=True)
    b.set(2, bp_y+1, 3, 'redstone_lamp[lit=true]', mirror=True)  # 推进器红光
    b.set(2, bp_y, 3, palette['accent'], mirror=True)

    # ===== 牌子 =====
    b.set(0, -1, -7, 'oak_sign', mirror=False)

    return b


if __name__ == '__main__':
    ORIGIN = (-100, 80, -340)
    print(f"[v3] building humanoid mecha @ {ORIGIN} ...")
    b = build_humanoid(ORIGIN)
    cmds = b.to_commands()
    bbox = b.bbox()
    print(f"[v3] block-level commands: {len(cmds)}")
    print(f"[v3] bbox: {bbox}, height {bbox[4]-bbox[1]+1}")

    # 清场 + grass
    with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
        ox, oy, oz = ORIGIN
        r.command(f"fill {ox-10} {oy-1} {oz-10} {ox+10} {oy+30} {oz+10} air")
        r.command(f"fill {ox-7} {oy-1} {oz-7} {ox+7} {oy-1} {oz+7} grass_block")
        ok = fail = 0
        for c in cmds:
            out = r.command(c)
            if any(k in out for k in ['Successfully','Changed','Set the block']):
                ok += 1
            else:
                fail += 1
        print(f"[v3] RCON: {ok}/{ok+fail}")

    # 保存 build.json
    ts = time.strftime('%Y%m%d-%H%M%S')
    outdir = os.path.expanduser(f'~/mcstory/outputs/mecha_humanoid_v3_{ts}')
    os.makedirs(outdir, exist_ok=True)
    json.dump({
        'origin': ORIGIN, 'block_count': len(cmds), 'bbox': list(bbox),
        'rcon_ok': ok, 'rcon_total': ok+fail,
        'palette': 'gundam_RX78', 'height_target': 24, 'proportions': 'gundam_7head',
        'tech': ['Rig humanoid', 'Proportions.get', 'mirror_axis', 'Joint.ball', 'Joint.cylinder', 'MountPoint beam_saber+shield', 'LayeredArmor 装甲分层', 'V-fin 4 层', 'jet pack 背包推进器']
    }, open(f'{outdir}/build.json','w'), ensure_ascii=False, indent=2)
    print(f"[v3] outdir: {outdir}")
