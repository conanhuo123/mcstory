#!/usr/bin/env python3
"""cli_full_fixed.py — cli_full.py 的修正版 (韩沂 2026-05-18)
修复: 空镜/纯色帧 — 相机拉近 + 取消阶梯移动(固定机位) + 成片加缓推镜头.
Usage:
  python3 cli_full_fixed.py samples/death_sentence.json
"""
import sys, os, json, subprocess, time, math
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
VF = Path.home() / "video_factory"
FFMPEG = "/opt/homebrew/bin/ffmpeg"


def run(cmd, cwd=None, timeout=120):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    if r.returncode != 0:
        print(f"❌ {' '.join(map(str,cmd))[:80]}: {r.stderr[-300:]}"); sys.exit(1)
    return r.stdout


def to_timeline(inp, work):
    if inp.endswith(".json") and Path(inp).exists():
        script_p = Path(inp)
        target = work / "script.json"
        target.write_text(script_p.read_text())
        return target
    else:
        out = run(["python3", str(ROOT/"scripts/parse.py"), inp])
        target = work / "script.json"
        target.write_text(out)
        return target


def main(inp):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    sample_id = Path(inp).stem if inp.endswith(".json") else "adhoc"
    work = ROOT / "outputs" / f"{sample_id}_{stamp}"
    work.mkdir(parents=True, exist_ok=True)
    print(f"=== mcstory fixed pipeline: {sample_id} @ {stamp} ===")

    script_p = to_timeline(inp, work)
    print(f"[1/6] script: {script_p}")

    tl_p = work / "timeline.json"
    run(["python3", str(ROOT/"scripts/translate.py"), str(script_p), str(tl_p)])
    print(f"[2/6] timeline: {tl_p}")

    run(["python3", str(ROOT/"scripts/record.py"), str(tl_p)])
    print(f"[3/6] bot.js: {work/'bot.js'}")

    timeline = json.loads(tl_p.read_text())
    chat_lines = [(ev["t"], ev["text"]) for ev in timeline["timeline"]
                  if ev["type"] in ("tellraw", "subtitle")]
    chat_lines = sorted(set(chat_lines), key=lambda x: x[0])[:10]

    sc = json.loads(script_p.read_text())
    scene_id = sc.get("scene", "courtroom")
    builds = json.loads((ROOT/"templates/scenes/builds.json").read_text()).get("builds", {})
    scene_build = builds.get(scene_id, {})
    build_cmds = [b["cmd"] for b in scene_build.get("blocks", []) if "cmd" in b]
    origin = scene_build.get("origin", [-60, 80, -190])

    NBT = '{NoAI:1b,Silent:1b,PersistenceRequired:1b,Invulnerable:1b}'
    SUMMON_MAP = {
        "villager": f"/summon villager <X> <Y> <Z> {NBT}",
        "iron_golem": f"/summon iron_golem <X> <Y> <Z> {NBT}",
        "creeper": f"/summon creeper <X> <Y> <Z> {NBT}",
        "steve": None,
    }
    char_summons = []
    chars = sc.get("characters", [])
    for i, ch in enumerate(chars):
        tmpl = SUMMON_MAP.get(ch)
        if tmpl:
            x, y, z = origin[0] + (i-1)*2, origin[1] + 1, origin[2] + 2
            char_summons.append(tmpl.replace("<X>", str(x)).replace("<Y>", str(y)).replace("<Z>", str(z)))

    # --- FIX: 相机拉近, 3/4 视角, 场景填满约半屏 (旧版 [6,30,8] 太远 → 空镜) ---
    CAM_POS = [origin[0] + 7, origin[1] + 8, origin[2] + 9]
    CAM_LOOK = [origin[0], origin[1] + 1, origin[2]]
    cx, cy, cz = CAM_POS
    lx, ly, lz = CAM_LOOK
    dx, dy, dz = lx - cx, ly - cy, lz - cz
    yaw = round(math.degrees(math.atan2(-dx, dz)), 1)
    pitch = round(math.degrees(math.atan2(-dy, math.sqrt(dx*dx + dz*dz))), 1)
    print(f"  cam @ ({cx},{cy},{cz}) yaw={yaw} pitch={pitch} → look ({lx},{ly},{lz})")

    char_actions = []
    if "villager" in chars:
        vx, vy, vz = origin[0]-1, origin[1]+1, origin[2]+2
        cx2, cy2, cz2 = origin[0], origin[1]+1, origin[2]
        char_actions += [
            [3, f"/tp @e[type=villager,limit=1,sort=nearest,x={vx},y={vy},z={vz}] {cx2} {cy2} {cz2}"],
            [6, f"/tp @e[type=villager,limit=1,sort=nearest,x={cx2},y={cy2},z={cz2}] {cx2} {cy2} {cz2} 0 -30"],
            [9, f"/effect give @e[type=villager,limit=1,sort=nearest,x={cx2},y={cy2},z={cz2}] glowing 5 0 true"],
        ]
    sign_x, sign_y, sign_z = origin[0]+4, origin[1]+1, origin[2]-2
    char_actions += [
        [12, f"/setblock {sign_x} {sign_y} {sign_z} oak_sign[rotation=8]{{front_text:{{messages:['\"上一任服主\"','\"villager_42\"','\"\"','\"\"']}}}}"]
    ]

    viewer_js = f"""const mineflayer = require('mineflayer');
const {{ Vec3 }} = require('vec3');
const {{ mineflayer: pv }} = require('prismarine-viewer');
const {{ pathfinder }} = require('mineflayer-pathfinder');
const cam = mineflayer.createBot({{host:'localhost',port:25565,username:'camera',version:'1.20.4'}});
cam.loadPlugin(pathfinder);
const ORIGIN = {json.dumps(origin)};
const CAMP = [{cx}, {cy}, {cz}];
function aimCam() {{
  try {{
    // FIX: physics 已禁用, 直接钉死机位 — 防 mineflayer 物理把相机往上漂
    cam.entity.position.x = CAMP[0];
    cam.entity.position.y = CAMP[1];
    cam.entity.position.z = CAMP[2];
    cam.entity.velocity = new Vec3(0, 0, 0);
    const dx = {lx} - CAMP[0], dy = {ly} - CAMP[1], dz = {lz} - CAMP[2];
    const yaw = Math.atan2(-dx, dz);
    const pitch = Math.atan2(-dy, Math.sqrt(dx*dx + dz*dz));
    cam.look(yaw, pitch, true);
    // FIX: 触发 prismarine-viewer worldView.updatePosition → 加载场景 chunks (否则全屏天空)
    cam.emit('move');
    console.log(`aimCam pinned @ (${{CAMP[0]}},${{CAMP[1]}},${{CAMP[2]}}) yaw=${{(yaw*180/Math.PI).toFixed(0)}} pitch=${{(pitch*180/Math.PI).toFixed(0)}}`);
  }} catch(e) {{ console.error('aimCam', e.message); }}
}}
cam.once('spawn', () => {{
  console.log('cam spawned at', cam.entity.position);
  // FIX: 关闭 mineflayer 物理 — 相机不再被模拟重力/漂移影响, 机位绝对固定
  cam.physicsEnabled = false;
  // viewer 延后启动: 等 director op + tp cam 到机位, chunks 已在场景周围
  setTimeout(() => {{
    setTimeout(() => {{
      pv(cam, {{port: 3007, firstPerson: true, viewDistance: 8}});
      console.log('VIEWER_READY (cam now at', cam.entity.position, ')');
    }}, 4000);
  }}, 9000);
  // FIX: 持续钉死机位 — 每 500ms 重置位置+朝向, 全程稳定无空镜
  setTimeout(() => {{ setInterval(aimCam, 500); }}, 2500);
  setTimeout(() => {{
    const d = mineflayer.createBot({{host:'localhost',port:25565,username:'director',version:'1.20.4'}});
    d.on('messagestr', s => {{ if(s.toLowerCase().includes('error')||s.includes('找不到')) console.error('CHAT:', s.slice(0,80)); }});
    d.once('spawn', () => {{
      const buildCmds = {json.dumps(build_cmds, ensure_ascii=False)};
      d.chat('/time set noon');
      d.chat('/weather clear');
      d.chat('/gamerule doDaylightCycle false');
      d.chat('/gamerule doWeatherCycle false');
      d.chat('/gamerule doMobSpawning false');
      d.chat('/gamerule mobGriefing false');
      d.chat('/difficulty peaceful');
      // FIX: spectator 机位 — 无重力不下坠, 无需石台/levitation, 机位绝对固定
      d.chat('/gamemode spectator camera');
      // FIX: viewer init 前先把 cam tp 到最终机位 (固定, 不再移动 → chunks 不卸载, 全程有画面)
      d.chat(`/tp camera ${{CAMP[0]}} ${{CAMP[1]}} ${{CAMP[2]}} {yaw} {pitch}`);
      console.log('director tp cam to FIXED rig', CAMP);
      d.chat(`/setworldspawn ${{CAMP[0]}} ${{CAMP[1]}} ${{CAMP[2]}}`);
      const ccx = Math.floor(ORIGIN[0]/16), ccz = Math.floor(ORIGIN[2]/16);
      d.chat(`/replay start chunks around ${{ccx}} ${{ccz}} radius 3`);
      console.log('ServerReplay start: around', ccx, ccz, 'r=3');
      setTimeout(() => {{ d.chat(`/replay stop chunks all`); console.log('ServerReplay stop'); }}, 35000);
      // spectator 不下坠, 仅需重 tp 锁定机位
      setTimeout(() => {{
        d.chat(`/tp camera ${{CAMP[0]}} ${{CAMP[1]}} ${{CAMP[2]}} {yaw} {pitch}`);
        setTimeout(aimCam, 4500);
      }}, 800);
      buildCmds.forEach((cmd, i) => {{
        const c = cmd.startsWith('/') ? cmd : '/' + cmd;
        setTimeout(() => {{ d.chat(c); if(i<3) console.log('build', i, c.slice(0,40)); }}, 1000 + i*100);
      }});
      const charSummons = {json.dumps(char_summons, ensure_ascii=False)};
      const summonStart = 1000 + buildCmds.length*100 + 500;
      charSummons.forEach((s, i) => {{
        setTimeout(() => {{ d.chat(s); console.log('summon', s.slice(0,50)); }}, summonStart + i*200);
      }});
      const lines = {json.dumps(chat_lines, ensure_ascii=False)};
      const buildEnd = 1000 + buildCmds.length*100 + 500 + charSummons.length*200 + 1500;
      // FIX: 不再阶梯移动相机. 仅在 buildEnd 重新锁定机位 + 校正朝向 (修正 build/levitation 漂移)
      setTimeout(() => {{
        d.chat(`/tp camera ${{CAMP[0]}} ${{CAMP[1]}} ${{CAMP[2]}} {yaw} {pitch}`);
        try {{
          cam.entity.position.x = CAMP[0]; cam.entity.position.y = CAMP[1]; cam.entity.position.z = CAMP[2];
          cam.emit('move');
        }} catch(e) {{}}
        setTimeout(aimCam, 300);
        console.log('cam locked at FIXED rig', CAMP);
      }}, buildEnd);
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

    vlog = work / "viewer.log"
    vp = subprocess.Popen(["node", str(vjs_p)], stdout=open(vlog, "w"), stderr=subprocess.STDOUT, cwd=str(VF/"minecraft_bot"))
    print(f"[4/6] viewer PID={vp.pid}, waiting ready...")
    for _ in range(25):
        time.sleep(1)
        if vlog.exists() and "VIEWER_READY" in vlog.read_text():
            print("  viewer ready")
            break

    time.sleep(25)

    raw = work / "raw.mp4"
    print(f"[5/6] puppeteer recording 18s → {raw.name}")
    r = subprocess.run(["node", str(VF/"minecraft_bot/puppeteer_recorder.js"), str(raw), "18"],
                       cwd=str(VF/"minecraft_bot"), capture_output=True, text=True, timeout=180)
    print("  pup:", r.stdout.strip().split("\n")[-1] if r.stdout else r.stderr[-200:])

    qc_frame = work / "qc_frame.jpg"
    subprocess.run([FFMPEG, "-y", "-i", str(raw), "-vframes", "1", "-ss", "5", str(qc_frame)], capture_output=True)
    if not qc_frame.exists() or qc_frame.stat().st_size < 5000:
        print(f"❌ QC fail: frame too small"); sys.exit(2)
    print(f"  ✓ QC frame: {qc_frame.stat().st_size/1024:.1f} KB")

    try: vp.terminate()
    except: pass

    if not raw.exists() or raw.stat().st_size < 1024*100:
        print(f"❌ raw mp4 too small"); sys.exit(1)
    print(f"  raw: {raw.stat().st_size/1024/1024:.1f} MB")

    # FIX: 固定机位 → 用后期缓推(Ken Burns)制造镜头变化, 1.0x→1.18x 匀速推进
    raw_kb = work / "raw_kb.mp4"
    print(f"  Ken Burns 缓推 → {raw_kb.name}")
    kb = subprocess.run([FFMPEG, "-y", "-i", str(raw),
        "-vf", "crop=w='iw-iw*0.16*min(t/15,1)':h='ih-ih*0.16*min(t/15,1)':x='(iw-ow)/2':y='(ih-oh)/2',scale=1920:1080:flags=bicubic",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        str(raw_kb)], capture_output=True, text=True)
    src_for_post = raw_kb if (kb.returncode == 0 and raw_kb.exists() and raw_kb.stat().st_size > 1024*100) else raw
    if src_for_post is raw:
        print(f"  ⚠ Ken Burns 失败, 用原始 raw: {kb.stderr[-200:]}")

    final = work / "final.mp4"
    print(f"[6/6] postprod → {final.name}")
    subprocess.run(["python3", str(ROOT/"scripts/postprod.py"), str(src_for_post), str(tl_p), str(final)], capture_output=True)

    if final.exists():
        print(f"\n✓ DONE: {final} ({final.stat().st_size/1024/1024:.1f} MB)")
        return final
    else:
        print(f"❌ final not generated"); sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
