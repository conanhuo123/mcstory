#!/usr/bin/env python3
"""cinematic_director.py — 30s 哥斯拉空降紫禁城 cinematic
关键帧编排: tp + setblock + particle + sound + lightning + title
"""
import sys, time, os
sys.path.insert(0, '/Users/coco/mcstory/scripts')
from mcrcon import MCRcon

# 战场中心 = 紫禁城太和殿 (已建)
CX, CY, CZ = -1500, 80, -1500
GODZILLA_X, GODZILLA_Z = CX-15, CZ
KONG_X, KONG_Z = CX+15, CZ

def r_cmd(rcon, cmd, log=False):
    out = rcon.command(cmd)
    if log: print(f"  >{cmd[:80]} → {out[:60]}")
    return out

def tp_godzilla(r, x, y, z):
    r_cmd(r, f'tp @e[type=ender_dragon,limit=1] {x} {y} {z}')

def tp_kong(r, x, y, z):
    r_cmd(r, f'tp @e[type=iron_golem,limit=1] {x} {y} {z}')

def particle(r, p, x, y, z, count=30, dx=2, dy=2, dz=2, force='force'):
    r_cmd(r, f'particle {p} {x} {y} {z} {dx} {dy} {dz} 0.1 {count} {force}')

def title(r, text, sub='', who='@a', color='gold'):
    r_cmd(r, f'title {who} title {{"text":"{text}","color":"{color}"}}')
    if sub:
        r_cmd(r, f'title {who} subtitle {{"text":"{sub}"}}')

def lightning(r, x, y, z):
    r_cmd(r, f'summon lightning_bolt {x} {y} {z}')

def play(r, sound, who='@a', vol=2.0, pitch=1.0):
    r_cmd(r, f'execute as {who} at @s run playsound {sound} master @s ~ ~ ~ {vol} {pitch}')

def cinematic():
    print("=== 30s 哥斯拉空降紫禁城 cinematic ===\n")
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        # 准备: 老板 spectator + 上空俯瞰 + 黑夜雷暴 + ender_dragon NoAI=0 (开 AI)
        r_cmd(r, 'gamemode spectator conanhuo')
        r_cmd(r, f'tp conanhuo {CX} {CY+40} {CZ-50} 0 30')
        r_cmd(r, 'time set 18000')
        r_cmd(r, 'weather thunder 600')
        r_cmd(r, 'kill @e[type=lightning_bolt]')
        # 确保 ender_dragon 在天上 (起点 100 高)
        r_cmd(r, f'data merge entity @e[type=ender_dragon,limit=1] {{NoAI:1b,Invulnerable:1b,Health:200.0f}}')
        # iron_golem 复活
        r_cmd(r, 'kill @e[type=iron_golem]')
        r_cmd(r, f'summon iron_golem {KONG_X} {CY+1} {KONG_Z} {{CustomName:\'"§8§l金刚 KING KONG"\',CustomNameVisible:1b,PlayerCreated:0b,Health:200.0f,Attributes:[{{Name:"generic.max_health",Base:200.0}}]}}')
        time.sleep(1)

        # ===== ACT 1 (0-5s): 平静夜景 + 哥斯拉天降 =====
        title(r, '§e§l第一幕', '§f紫禁城宁静夜景')
        tp_godzilla(r, GODZILLA_X, CY+50, GODZILLA_Z)
        play(r, 'ambient.cave', vol=3.0)
        for t in range(5):
            # 哥斯拉慢慢从天而降
            y = CY + 50 - t*8
            tp_godzilla(r, GODZILLA_X, y, GODZILLA_Z)
            particle(r, 'dragon_breath', GODZILLA_X, y, GODZILLA_Z, 50)
            particle(r, 'flame', GODZILLA_X, y, GODZILLA_Z, 20)
            time.sleep(1)
        # 落地 lightning
        lightning(r, GODZILLA_X, CY+5, GODZILLA_Z)
        lightning(r, GODZILLA_X-3, CY+5, GODZILLA_Z)
        play(r, 'entity.lightning_bolt.thunder', vol=5.0)
        time.sleep(0.5)

        # ===== ACT 2 (5-12s): 哥斯拉吼 + 紫禁城被破坏 =====
        title(r, '§4§l哥斯拉降临', '§f紫禁城遭袭')
        play(r, 'entity.ender_dragon.growl', vol=10.0)
        # 紫禁城屋顶 setblock fire (3 个 building 屋顶)
        for bx, bz in [(CX, CZ),(CX-30, CZ),(CX+30, CZ),(CX, CZ-30),(CX, CZ+30)]:
            for fx in range(-5, 6):
                for fz in range(-5, 6):
                    r_cmd(r, f'execute if block {bx+fx} {CY+10} {bz+fz} #minecraft:planks run setblock {bx+fx} {CY+11} {bz+fz} fire')
        # 龙息粒子大爆发
        for _ in range(7):
            particle(r, 'dragon_breath', GODZILLA_X, CY+10, GODZILLA_Z, 200, 5, 3, 5)
            particle(r, 'flame', CX, CY+15, CZ, 100, 10, 5, 10)
            particle(r, 'explosion', GODZILLA_X+3, CY+8, GODZILLA_Z, 5)
            lightning(r, CX, CY+5, CZ)
            play(r, 'entity.generic.explode', vol=4.0)
            time.sleep(1)

        # ===== ACT 3 (12-20s): 金刚冲锋 =====
        title(r, '§8§l金刚出击', '§f保护紫禁城')
        play(r, 'entity.iron_golem.attack', vol=8.0)
        # 金刚 tp 跳跃冲向哥斯拉 (3 跳)
        kong_steps = [
            (CX+8, CY+8, CZ),     # 跳起
            (CX+3, CY+12, CZ),    # 高跳
            (CX-3, CY+10, CZ),    # 接近
            (CX-8, CY+5, CZ),     # 落到哥斯拉旁
        ]
        for sx, sy, sz in kong_steps:
            tp_kong(r, sx, sy, sz)
            particle(r, 'cloud', sx, sy, sz, 50)
            particle(r, 'crit', sx, sy, sz, 30)
            play(r, 'entity.iron_golem.step', vol=5.0)
            lightning(r, sx, sy+3, sz)
            time.sleep(1.5)
        # 接触 — 大爆炸
        play(r, 'entity.generic.explode', vol=10.0)
        for _ in range(3):
            particle(r, 'explosion_emitter', GODZILLA_X, CY+6, GODZILLA_Z, 5)
            particle(r, 'lava', GODZILLA_X, CY+6, GODZILLA_Z, 100, 5, 3, 5)
            time.sleep(0.5)

        # ===== ACT 4 (20-25s): 紫禁城坍塌 + 战火 =====
        title(r, '§c§l激烈对战', '§f紫禁城坍塌中')
        # 4 角红柱倒塌 (setblock air 顶部分)
        for ax, az in [(CX-40, CZ-40),(CX+40, CZ-40),(CX-40, CZ+40),(CX+40, CZ+40)]:
            for h in range(20, 35):
                r_cmd(r, f'setblock {ax-1} {CY+h} {az-1} air')
                r_cmd(r, f'setblock {ax} {CY+h} {az} air')
                r_cmd(r, f'setblock {ax+1} {CY+h} {az+1} air')
        # 漫天火 + 烟
        for _ in range(5):
            particle(r, 'campfire_signal_smoke', CX, CY+20, CZ, 100, 30, 10, 30)
            particle(r, 'flame', CX, CY+15, CZ, 200, 20, 5, 20)
            lightning(r, CX + ((_ * 5) % 20 - 10), CY+5, CZ)
            time.sleep(1)

        # ===== ACT 5 (25-30s): 决战胜负 =====
        title(r, '§e§l胜负已分', '§f伤痕累累')
        # 哥斯拉撤退 — 飞回天空
        for t in range(5):
            y = CY + 5 + t*8
            tp_godzilla(r, GODZILLA_X-2*t, y, GODZILLA_Z-3*t)
            particle(r, 'dragon_breath', GODZILLA_X, y, GODZILLA_Z, 50)
            play(r, 'entity.ender_dragon.flap', vol=5.0)
            time.sleep(1)

        # 金刚胜利 + 烟花
        title(r, '§a§l金刚胜利', '§f紫禁城保住了')
        play(r, 'ui.toast.challenge_complete', vol=8.0)
        for i in range(20):
            r_cmd(r, f'summon firework_rocket {CX + (i%5)*4 - 8} {CY+20} {CZ + (i%3)*4} {{LifeTime:30,FireworksItem:{{id:"firework_rocket",Count:1b,tag:{{Fireworks:{{Flight:2b,Explosions:[{{Type:1b,Colors:[I;16711680,16776960,255]}}]}}}}}}}}')

        time.sleep(2)
        title(r, '§6§l剧终', '§e哥斯拉 VS 金刚 · 紫禁城大战')

    print("\n=== cinematic 完 (30s) ===")

if __name__ == '__main__':
    cinematic()
