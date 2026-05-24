#!/usr/bin/env python3
# one_line_to_mp4.py — 产品脊柱: 一句话 → studio建 → 环绕运镜 → mp4
# 用法: python3 one_line_to_mp4.py "<中文一句话>" [cx cz]
# 串: studio_build.py (清平整地台+L2 nlp_to_building 真建) → orbit_video.js (环绕多帧) → ffmpeg mp4
import sys, os, subprocess, json, glob, time, math

prompt = sys.argv[1]
cx = int(sys.argv[2]) if len(sys.argv) > 2 else -800
cz = int(sys.argv[3]) if len(sys.argv) > 3 else -800
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
VENV = os.path.join(ROOT, '.venv/bin/python')
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ts = time.strftime('%H%M%S')

print(f"[1/3] studio build @ {cx},{cz}: {prompt}", flush=True)
before = set(glob.glob('outputs/nlp_*.json'))
r = subprocess.run([VENV, 'scripts/studio_build.py', prompt, str(cx), str(cz)],
                   capture_output=True, text=True, timeout=300)
print(r.stdout[-400:], flush=True)
if 'STUDIO_BUILD_DONE' not in r.stdout:
    print("BUILD FAILED:", r.stderr[-300:], flush=True); sys.exit(1)

# 找本次新建的 nlp json
after = set(glob.glob('outputs/nlp_*.json'))
new = sorted(after - before, key=os.path.getmtime)
if not new:
    new = sorted(after, key=os.path.getmtime)
d = json.load(open(new[-1]))
ox, oy, oz = d['origin']; w, h, dd = d['bbox']
ccx, ccy, ccz = ox + w/2, oy + h*0.5, oz + dd/2
radius = max(w, dd) * 0.9 + 18
print(f"[2/3] orbit: center({ccx:.0f},{ccy:.0f},{ccz:.0f}) r={radius:.0f} bbox {w}x{h}x{dd}", flush=True)

outdir = f"outputs/auto_{d.get('id','build')}_{ts}"
r2 = subprocess.run(['node', 'scripts/orbit_video.js',
                     f"{ccx:.0f}", f"{ccy:.0f}", f"{ccz:.0f}", f"{radius:.0f}", "36", outdir],
                    capture_output=True, text=True, env=dict(os.environ, CHROME_PATH=CHROME), timeout=400)
print(r2.stdout[-300:], flush=True)
if 'FRAMES_DONE' not in r2.stdout:
    print("ORBIT FAILED:", r2.stderr[-300:], flush=True); sys.exit(1)

print(f"[3/3] ffmpeg → mp4", flush=True)
mp4 = f"{outdir}/video.mp4"
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','12','-i',f"{outdir}/frame_%03d.png",
                '-c:v','libx264','-pix_fmt','yuv420p','-vf','scale=1280:720', mp4], check=True)
print(f"PIPELINE_DONE mp4={mp4} size={os.path.getsize(mp4)//1024}KB", flush=True)
