#!/usr/bin/env python3
"""cli_gate1.py — 关 1 一键 pipeline
用法: cli_gate1.py "<一句话>" [--no-exec]
默认: 一句话 → GPT JSON → RCON 真执行 → topdown PNG + 白盒验证
--no-exec: 跳过 RCON 真执行, 只 simulate topdown
"""
import sys, os, json, subprocess, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    if len(sys.argv) < 2:
        print("用法: cli_gate1.py '<一句话>' [--no-exec]"); sys.exit(1)
    prompt = sys.argv[1]
    no_exec = '--no-exec' in sys.argv

    ts = time.strftime('%Y%m%d-%H%M%S')
    label = re.sub(r'[^a-zA-Z0-9一-鿿]+', '_', prompt)[:30]
    outdir = os.path.expanduser(f'~/mcstory/outputs/gate1_cli/{ts}_{label}')
    os.makedirs(outdir, exist_ok=True)

    print(f"[gate1] 输入: {prompt}")
    print(f"[gate1] 输出目录: {outdir}")

    # 1. GPT parse
    print("[gate1] 1/4 调 GPT-5.5...")
    import parse
    script = parse.parse_prompt(prompt)
    if not script:
        print("[gate1] FAIL: GPT 没返回 JSON"); sys.exit(1)
    json_path = f'{outdir}/script.json'
    json.dump(script, open(json_path,'w'), ensure_ascii=False, indent=2)
    cmds = script.get('build_cmds', [])
    origin = script.get('scene_origin', [-60,79,-190])
    scene = script.get('scene','?')
    chars = script.get('characters',[])
    print(f"[gate1]   scene={scene} origin={origin} build_cmds={len(cmds)} chars={chars}")

    # 2. topdown simulate (deterministic, 不依赖 server)
    print("[gate1] 2/4 simulate topdown...")
    png = f'{outdir}/topdown.png'
    txt = f'{outdir}/topdown.txt'
    r = subprocess.run(['python3', os.path.expanduser('~/mcstory/scripts/gate1_simulate_topdown.py'),
                        json_path, label, png], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"[gate1]   topdown FAIL: {r.stderr[:200]}")
    else:
        print(f"[gate1]   topdown PNG saved: {png}")

    # 3. RCON 真执行 + 白盒
    if not no_exec:
        print("[gate1] 3/4 RCON 真执行 build_cmds + 白盒抽样...")
        from mcrcon import MCRcon
        try:
            with MCRcon('127.0.0.1', 'mcstory123', port=25575) as rc:
                rc.command("fill -80 78 -210 -40 95 -170 air")
                ok = 0
                for c in cmds:
                    resp = rc.command(c)
                    if 'Successfully' in resp or 'Changed' in resp or 'Set the block' in resp: ok += 1
                print(f"[gate1]   RCON: {ok}/{len(cmds)} executed")
                # 白盒抽样
                wb_ok = wb_total = 0
                probes = []
                for c in cmds:
                    m = re.match(r'(?:/)?fill\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(?:minecraft:)?(\w+)', c)
                    if m:
                        xs=[int(m.group(1)),int(m.group(4))]; ys=[int(m.group(2)),int(m.group(5))]; zs=[int(m.group(3)),int(m.group(6))]
                        probes.append(((xs[0]+xs[1])//2, (ys[0]+ys[1])//2, (zs[0]+zs[1])//2, m.group(7)))
                    m2 = re.match(r'(?:/)?setblock\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(?:minecraft:)?([a-z_]+)', c)
                    if m2: probes.append((int(m2.group(1)),int(m2.group(2)),int(m2.group(3)),m2.group(4)))
                for x,y,z,blk in probes[:8]:
                    out = rc.command(f"execute if block {x} {y} {z} {blk}")
                    if "Test passed" in out: wb_ok += 1
                    wb_total += 1
                print(f"[gate1]   白盒: {wb_ok}/{wb_total} PASS")
                exec_summary = {'exec_ok': ok, 'exec_total': len(cmds), 'wb_ok': wb_ok, 'wb_total': wb_total}
                json.dump(exec_summary, open(f'{outdir}/exec_summary.json','w'), indent=2)
        except Exception as e:
            print(f"[gate1]   RCON 跳过: {e}")
    else:
        print("[gate1] 3/4 (--no-exec) 跳过 RCON 真执行")

    # 4. 输出汇总
    print(f"[gate1] 4/4 DONE\n  json: {json_path}\n  png: {png}\n  txt: {txt}")

if __name__ == '__main__':
    main()
