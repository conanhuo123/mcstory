#!/usr/bin/env python3
"""cli_full.py — 一行命令: 一句话(或 sample.json) → 15s mp4 → 飞书+网盘
Usage:
  python3 cli_full.py "苦力怕跟村民道歉"
  python3 cli_full.py samples/creeper_refuse.json
"""
import sys, os, json, subprocess, time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
VF = Path.home() / "video_factory"

def run(cmd, cwd=None, timeout=120):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    if r.returncode != 0:
        print(f"❌ {' '.join(map(str,cmd))[:80]}: {r.stderr[-300:]}"); sys.exit(1)
    return r.stdout

def to_timeline(inp, work):
    """如果是 .json sample → 直接 translate; 否则 parse"""
    if inp.endswith(".json") and Path(inp).exists():
        script_p = Path(inp); 
        # translate.py 期望特定字段, samples 字段更全, 直接复用
        target = work / "script.json"
        target.write_text(script_p.read_text())
        return target
    else:
        # parse 输出到 stdout
        out = run(["python3", str(ROOT/"scripts/parse.py"), inp])
        target = work / "script.json"
        target.write_text(out)
        return target

def main(inp):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    sample_id = Path(inp).stem if inp.endswith(".json") else "adhoc"
    work = ROOT / "outputs" / f"{sample_id}_{stamp}"
    work.mkdir(parents=True, exist_ok=True)
    print(f"=== mcstory full pipeline: {sample_id} @ {stamp} ===")
    
    # 1. script
    script_p = to_timeline(inp, work)
    print(f"[1/6] script: {script_p}")
    
    # 2. translate
    tl_p = work / "timeline.json"
    run(["python3", str(ROOT/"scripts/translate.py"), str(script_p), str(tl_p)])
    print(f"[2/6] timeline: {tl_p}")
    
    # 3. record → bot.js
    run(["python3", str(ROOT/"scripts/record.py"), str(tl_p)])
    bot_js = work / "bot.js"
    print(f"[3/6] bot.js: {bot_js}")
    
    # 4. 启 viewer + chrome + 录屏 (复用 viewer_director.js 的 camera bot 模式)
    # 写 inline viewer script: camera bot + director bot 跑 timeline
    title = json.loads(script_p.read_text()).get("title", sample_id)
    timeline = json.loads(tl_p.read_text())
    chat_lines = [(ev["t"], ev["text"]) for ev in timeline["timeline"] if ev["type"] == "tellraw" or ev["type"] == "subtitle"]
    chat_lines = sorted(set(chat_lines), key=lambda x: x[0])[:10]
    # v0.2: 加载 scene build commands
    sc = json.loads(script_p.read_text())
    scene_id = sc.get("scene", "courtroom")
    builds = json.loads((ROOT/"templates/scenes/builds.json").read_text()).get("builds", {})
    scene_build = builds.get(scene_id, {})
    # v5.0 (老板 22:11 拍板): GPT 直接生成 build_cmds 优先于 templates
    build_cmds = sc.get("build_cmds") or [b["cmd"] for b in scene_build.get("blocks", []) if "cmd" in b]
    origin = sc.get("scene_origin") or scene_build.get("origin", [-60, 80, -190])
    # v0.2.1: summon characters in scene
    SUMMON_MAP = {
        "villager": "/summon villager",
        "iron_golem": "/summon iron_golem",
        "creeper": "/summon creeper",
        "steve": None,  # steve = director player, 不 summon
    }
    char_summons = []
    chars = sc.get("characters", [])
    # v5.2 (老板 22:11+22:38): 用 GPT 输出的 character_spawns 坐标, fallback hardcoded
    gpt_spawns = {s["actor"]: s["xyz"] for s in sc.get("character_spawns",[]) if "actor" in s and "xyz" in s}
    for i, ch in enumerate(chars):
        cmd = SUMMON_MAP.get(ch)
        if cmd:
            if ch in gpt_spawns:
                x, y, z = gpt_spawns[ch]
            else:
                x, y, z = origin[0] + (i-1)*2, origin[1] + 1, origin[2] + 5
            char_summons.append(f"{cmd} {x} {y} {z}")
    # v0.3: 镜头切换表 (5 shot × 7 字段: t, cam_x/y/z, look_x/y/z)
    # camera 类型 → 相对 origin 偏移
    CAM_OFFSETS = {
        "wide":           {"pos": [6, 4, 8], "look": [0, 1, 0]},   # 远 + 高
        "medium":         {"pos": [6, 4, 8],   "look": [0, 1, 0]},   # 中距
        "closeup_face":   {"pos": [3, 2, 4],   "look": [0, 1, 0]},   # 近
        "closeup_object": {"pos": [2, 1, 3],   "look": [0, 0, 0]},   # 极近, 看物
        "freeze_zoom":    {"pos": [4, 1, 5],   "look": [4, 1, 2]},   # 看牌
    }
    import math
    # v0.6: 固定 1 个 wide camera (不再切换), 节省 viewer sync 问题
    off = CAM_OFFSETS["wide"]
    cx, cy, cz = origin[0] + off["pos"][0], origin[1] + off["pos"][1], origin[2] + off["pos"][2]
    lx, ly, lz = origin[0] + off["look"][0], origin[1] + off["look"][1], origin[2] + off["look"][2]
    dx, dy, dz = lx - cx, ly - cy, lz - cz
    yaw = round(math.degrees(math.atan2(-dx, dz)), 1)
    pitch = round(math.degrees(math.atan2(-dy, math.sqrt(dx*dx + dz*dz))), 1)
    camera_moves = [[0, cx, cy, cz, yaw, pitch]]
    # v0.6: 角色动作时间表 (根据 shots 生成)
    # villager 默认在 (origin+(-1, 1, 2)), 5 shot:
    #   t=0 牢笼里低头, t=3 tp 到处决台中央 (押上来), t=6 抬头 (求饶), t=9 不变, t=12 setblock 反转牌
    char_actions = []
    if "villager" in chars:
        vx, vy, vz = origin[0]-1, origin[1]+1, origin[2]+2
        ctr_x, ctr_y, ctr_z = origin[0], origin[1]+1, origin[2]   # 处决台中央
        char_actions += [
            [3, f"/tp @e[type=villager,limit=1,sort=nearest,x={vx},y={vy},z={vz}] {ctr_x} {ctr_y} {ctr_z}"],
            [6, f"/tp @e[type=villager,limit=1,sort=nearest,x={ctr_x},y={ctr_y},z={ctr_z}] {ctr_x} {ctr_y} {ctr_z} 0 -30"],   # 抬头
            [9, f"/effect give @e[type=villager,limit=1,sort=nearest,x={ctr_x},y={ctr_y},z={ctr_z}] glowing 5 0 true"],
        ]
    # 反转牌: shot5 把旧牌从空 → 写 "上一任服主"
    sign_x, sign_y, sign_z = origin[0]+4, origin[1]+1, origin[2]-2
    char_actions += [
        [12, f"/setblock {sign_x} {sign_y} {sign_z} oak_sign[rotation=8]{{front_text:{{messages:['\"上一任服主\"','\"villager_42\"','\"\"','\"\"']}}}}"]
    ]
    
    viewer_js = f"""const mineflayer = require('mineflayer');
const {{ Vec3 }} = require('vec3');
const {{ mineflayer: pv }} = require('prismarine-viewer');
const cam = mineflayer.createBot({{host:'localhost',port:25565,username:'camera',version:'1.20.4'}});
cam.once('spawn', () => {{
  console.log('cam spawned');
  pv(cam, {{port: 3007, firstPerson: true, viewDistance: 6}});
  console.log('VIEWER_READY');
  setTimeout(() => {{
    const d = mineflayer.createBot({{host:'localhost',port:25565,username:'director',version:'1.20.4'}});
    d.on('messagestr', s => {{ if(s.toLowerCase().includes('error')||s.includes('找不到')) console.error('CHAT:', s.slice(0,80)); }});
    d.once('spawn', () => {{
      // v0.2: 给 director op 权限 + 先 build scene + tp camera 到 scene 上空, 再喊台词
      const buildCmds = {json.dumps(build_cmds, ensure_ascii=False)};
      const origin = {json.dumps(origin)};
      // camera + director 都已在 ops.json, 直接 build + tp
      // tp camera 到 scene 前方 + 让它 lookAt scene 中心 (firstPerson 跟 entity rotation)
      // 先在 camera 落点放石头让它站住, 再 tp + lookAt
      setTimeout(() => {{
        d.chat(`/setblock ${{origin[0]+10}} ${{origin[1]+7}} ${{origin[2]+12}} stone`);
      }}, 400);
      setTimeout(() => {{
        d.chat(`/tp camera ${{origin[0]+10}} ${{origin[1]+8}} ${{origin[2]+12}}`);
        d.chat(`/effect give camera minecraft:levitation 60 0 true`);
        setTimeout(() => {{
          // v4.4: cam 看 character 中心 (origin+5z), 不再看 build origin
          try {{ cam.lookAt(new Vec3(origin[0], origin[1]+2, origin[2]+5), true); console.log('cam lookAt characters'); }} catch(e) {{ console.error('look err', e.message); }}
        }}, 4500);
      }}, 800);
      // 然后批量 build (每条 50ms 间隔)
      buildCmds.forEach((cmd, i) => {{
        const c = cmd.startsWith('/') ? cmd : '/' + cmd;
        setTimeout(() => {{ d.chat(c); if(i<3) console.log('build', i, c.slice(0,40)); }}, 1000 + i*100);
      }});
      // v0.2.1: build 完后 summon characters
      const charSummons = {json.dumps(char_summons, ensure_ascii=False)};
      const summonStart = 1000 + buildCmds.length*100 + 500;
      charSummons.forEach((s, i) => {{
        setTimeout(() => {{ d.chat(s); console.log('summon', s.slice(0,50)); }}, summonStart + i*200);
      }});
      // build + summon 完后 (5s 缓冲) 再喊台词 + 切镜头
      const lines = {json.dumps(chat_lines, ensure_ascii=False)};
      const buildEnd = 1000 + buildCmds.length*100 + 500 + charSummons.length*200 + 1500;
      // v0.3: 镜头切换 (5 shot 5 个 camera 位置), shot.camera 决定距离/角度
      const cameraMoves = {json.dumps(camera_moves)};
      // v0.6: 1 个固定 wide camera + spectator
      // v4.2 撤回 follow, 改 wide camera fixed (前面验证 paper v0.6 baseline 看到 build/character)
      d.chat(`/gamemode spectator camera`);
      setInterval(() => {{
        d.chat(`/execute at @e[type=villager,limit=1,sort=nearest] run tp camera ~3 ~2 ~3 facing entity @e[type=villager,limit=1,sort=nearest]`);
      }}, 2000);  // 每 2s 重新 tp + facing, 跟随 villager 动作
      cameraMoves.forEach(([t, x, y, z, yaw, pitch]) => {{
        setTimeout(() => {{
          d.chat(`/tp camera ${{x}} ${{y}} ${{z}} ${{yaw}} ${{pitch}}`);
          console.log(`cam fixed @ (${{x.toFixed(1)}},${{y}},${{z.toFixed(1)}}) y${{yaw}} p${{pitch}}`);
        }}, buildEnd + t*1000);
      }});
      // v0.6: 角色动作时间表
      const charActions = {json.dumps(char_actions, ensure_ascii=False)};
      charActions.forEach(([t, cmd]) => {{
        setTimeout(() => {{ d.chat(cmd); console.log(`act t=${{t}} ${{cmd.slice(0,60)}}`); }}, buildEnd + t*1000);
      }});
      lines.forEach(([t, txt]) => {{
        setTimeout(() => {{ d.chat('/tellraw @a {{"text":"' + txt + '","color":"red","bold":true}}'); console.log('[t='+t+'s]', txt); }}, buildEnd + t*1000);
      }});
    }});
    d.on('error', e => console.error('dir err', e.message));
  }}, 6000);
}});
cam.on('error', e => console.error('cam err', e.message));
setTimeout(() => process.exit(0), 120000);
"""
    vjs_p = VF / "minecraft_bot" / f"_vd_{stamp}.js"
    vjs_p.write_text(viewer_js)
    
    # 启 viewer 后台
    vlog = work / "viewer.log"
    vp = subprocess.Popen(["node", str(vjs_p)], stdout=open(vlog, "w"), stderr=subprocess.STDOUT, cwd=str(VF/"minecraft_bot"))
    print(f"[4/6] viewer PID={vp.pid}, waiting ready...")
    # 等 VIEWER_READY
    for _ in range(20):
        time.sleep(1)
        if vlog.exists() and "VIEWER_READY" in vlog.read_text():
            print("  viewer ready")
            break
    
    # 等 director spawn (6s) + build (~3s) + summon (~2s) + tp 渲染 (~2s) = 14s 总
    time.sleep(14)

    # puppeteer headless 录 (不依赖 chrome GUI / 不依赖 user session, 真 headless)
    raw = work / "raw.mp4"
    print(f"[5/6] puppeteer recording 18s → {raw.name}")
    r = subprocess.run(["node", str(VF/"minecraft_bot/puppeteer_recorder.js"), str(raw), "18"],
                       cwd=str(VF/"minecraft_bot"), capture_output=True, text=True, timeout=180)
    print("  pup:", r.stdout.strip().split("\n")[-1] if r.stdout else r.stderr[-200:])

    # 自检: 取一帧验证不是空白/桌面 (色彩多样性 + 文件大小)
    qc_frame = work / "qc_frame.jpg"
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-i", str(raw), "-vframes", "1", "-ss", "5", str(qc_frame)], capture_output=True)
    if not qc_frame.exists() or qc_frame.stat().st_size < 5000:
        print(f"❌ QC fail: frame too small ({qc_frame.stat().st_size if qc_frame.exists() else 0} B), 可能录到空白"); sys.exit(2)
    print(f"  ✓ QC frame: {qc_frame.stat().st_size/1024:.1f} KB")

    # 清理 viewer
    try: vp.terminate()
    except: pass
    
    if not raw.exists() or raw.stat().st_size < 1024*100:
        print(f"❌ raw mp4 too small"); sys.exit(1)
    print(f"  raw: {raw.stat().st_size/1024/1024:.1f} MB")
    
    # 6. postprod
    final = work / "final.mp4"
    print(f"[6/6] postprod → {final.name}")
    subprocess.run(["python3", str(ROOT/"scripts/postprod.py"), str(raw), str(tl_p), str(final)], capture_output=True)
    
    if final.exists():
        print(f"\n✓ DONE: {final} ({final.stat().st_size/1024/1024:.1f} MB)")
        return final
    else:
        print(f"❌ final not generated"); sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
