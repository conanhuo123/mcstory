#!/usr/bin/env python3
"""mecha_template.py — 机甲模板参数化 (陆远 09:51 verdict)
头/胸/四肢/武器全参数化, reusable mecha builder.
"""
import sys, json
from typing import Optional

PALETTES = {
    'gundam_RX78': dict(leg='quartz_block', body='lapis_block', accent='red_concrete',
                        head='quartz_block', mask='red_concrete', antenna='yellow_concrete',
                        arm='quartz_block', shoulder='iron_block', weapon='iron_block'),
    'zaku_green': dict(leg='lime_concrete', body='green_concrete', accent='yellow_concrete',
                       head='green_concrete', mask='red_concrete', antenna='iron_block',
                       arm='lime_concrete', shoulder='cyan_concrete', weapon='gray_concrete'),
    'evangelion_purple': dict(leg='purple_concrete', body='purple_concrete', accent='lime_concrete',
                              head='purple_concrete', mask='orange_concrete', antenna='lime_concrete',
                              arm='purple_concrete', shoulder='magenta_concrete', weapon='iron_block'),
    'iron_giant': dict(leg='iron_block', body='iron_block', accent='red_concrete',
                       head='iron_block', mask='black_concrete', antenna='iron_block',
                       arm='iron_block', shoulder='iron_block', weapon='iron_block'),
}

def build_mecha(origin, palette='gundam_RX78', weapon='sword', height_scale=1.0):
    """生成 mecha build_cmds.
    height_scale: 1.0 = 12 块高 (RX-78 默认), 1.5 = 18 块 (zeong sized)
    weapon: sword / rifle / beam_saber / shield
    """
    ox, oy, oz = origin
    p = PALETTES.get(palette, PALETTES['gundam_RX78'])
    h = int(4 * height_scale)  # legs
    body_h = int(3 * height_scale)
    head_h = int(2 * height_scale)
    cmds = []
    # 清场
    cmds.append(f"fill {ox-8} {oy-1} {oz-8} {ox+8} {oy+18} {oz+8} air")
    # 草地底座
    cmds.append(f"fill {ox-5} {oy-1} {oz-5} {ox+5} {oy-1} {oz+5} grass_block")
    # 双腿
    cmds.append(f"fill {ox-1} {oy} {oz} {ox-1} {oy+h-1} {oz} {p['leg']}")
    cmds.append(f"fill {ox+1} {oy} {oz} {ox+1} {oy+h-1} {oz} {p['leg']}")
    cmds.append(f"setblock {ox-1} {oy} {oz} {p['leg']}")  # 脚
    cmds.append(f"setblock {ox+1} {oy} {oz} {p['leg']}")
    # 腰带 (深色 accent)
    cmds.append(f"fill {ox-1} {oy+h} {oz} {ox+1} {oy+h} {oz} {p['accent']}")
    # 躯干
    body_top = oy + h + body_h
    cmds.append(f"fill {ox-1} {oy+h+1} {oz} {ox+1} {body_top} {oz} {p['body']}")
    # 胸前 V (accent)
    cmds.append(f"setblock {ox} {oy+h+2} {oz-1} {p['accent']}")
    cmds.append(f"setblock {ox-1} {body_top} {oz-1} {p['accent']}")
    cmds.append(f"setblock {ox+1} {body_top} {oz-1} {p['accent']}")
    # 双肩
    cmds.append(f"setblock {ox-2} {body_top-1} {oz} {p['shoulder']}")
    cmds.append(f"setblock {ox+2} {body_top-1} {oz} {p['shoulder']}")
    # 双臂 (悬挂)
    arm_bot = oy + h
    cmds.append(f"fill {ox-2} {arm_bot} {oz} {ox-2} {arm_bot+body_h-1} {oz} {p['arm']}")
    cmds.append(f"fill {ox+2} {arm_bot} {oz} {ox+2} {arm_bot+body_h-1} {oz} {p['arm']}")
    # 手 (端点)
    cmds.append(f"setblock {ox-3} {arm_bot+body_h-1} {oz} {p['arm']}")
    cmds.append(f"setblock {ox+3} {arm_bot+body_h-1} {oz} {p['arm']}")
    # 武器
    if weapon == 'sword':
        cmds.append(f"fill {ox+3} {arm_bot+body_h} {oz} {ox+3} {arm_bot+body_h+4} {oz} {p['weapon']}")
        cmds.append(f"setblock {ox+3} {arm_bot+body_h} {oz-1} {p['weapon']}")  # 剑柄
    elif weapon == 'rifle':
        cmds.append(f"fill {ox+3} {arm_bot+body_h-1} {oz-1} {ox+3} {arm_bot+body_h-1} {oz-4} {p['weapon']}")
    elif weapon == 'beam_saber':
        cmds.append(f"fill {ox+3} {arm_bot+body_h} {oz} {ox+3} {arm_bot+body_h+5} {oz} sea_lantern")
    elif weapon == 'shield':
        cmds.append(f"fill {ox-3} {arm_bot+1} {oz-1} {ox-3} {arm_bot+body_h} {oz-1} {p['weapon']}")
        cmds.append(f"setblock {ox-3} {arm_bot+1} {oz-2} {p['accent']}")
        cmds.append(f"setblock {ox-3} {arm_bot+body_h-1} {oz-2} {p['accent']}")
    # 脖颈
    cmds.append(f"setblock {ox} {body_top+1} {oz} {p['head']}")
    # 头部
    head_bot = body_top + 2
    cmds.append(f"fill {ox-1} {head_bot} {oz} {ox+1} {head_bot+head_h-1} {oz} {p['head']}")
    # 面罩 (前)
    cmds.append(f"setblock {ox} {head_bot} {oz-1} {p['mask']}")
    # 眼睛 (yellow 两侧)
    cmds.append(f"setblock {ox-1} {head_bot} {oz-1} {p['antenna']}")
    cmds.append(f"setblock {ox+1} {head_bot} {oz-1} {p['antenna']}")
    # V 形天线
    antenna_y = head_bot + head_h
    cmds.append(f"setblock {ox-1} {antenna_y} {oz} {p['antenna']}")
    cmds.append(f"setblock {ox+1} {antenna_y} {oz} {p['antenna']}")
    cmds.append(f"setblock {ox} {antenna_y} {oz} {p['head']}")
    cmds.append(f"setblock {ox-2} {antenna_y+1} {oz} {p['antenna']}")
    cmds.append(f"setblock {ox+2} {antenna_y+1} {oz} {p['antenna']}")
    # 牌子
    cmds.append(f"setblock {ox} {oy-1} {oz-6} oak_sign{{front_text:{{messages:['\"{palette.upper()}\"','\"{weapon}\"','\"\"','\"\"']}}}}")
    return cmds

def run(origin, palette='gundam_RX78', weapon='sword', height_scale=1.0):
    from mcrcon import MCRcon
    cmds = build_mecha(origin, palette, weapon, height_scale)
    ok = fail = 0
    with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
        for c in cmds:
            out = r.command(c)
            if any(k in out for k in ['Successfully','Changed','Filled','Set the block']):
                ok += 1
            else:
                fail += 1
    return cmds, ok, fail

if __name__ == '__main__':
    # 测 4 变种
    variants = [
        ((-100, 80, -300), 'gundam_RX78', 'sword', 1.0),
        ((-80, 80, -300),  'zaku_green', 'rifle', 1.0),
        ((-60, 80, -300),  'evangelion_purple', 'beam_saber', 1.2),
        ((-40, 80, -300),  'iron_giant', 'shield', 1.0),
    ]
    for o, p, w, h in variants:
        cmds, ok, fail = run(o, p, w, h)
        print(f"  {p:<20} {w:<12} @ {o}: {ok}/{ok+fail} OK ({len(cmds)} cmds)")
