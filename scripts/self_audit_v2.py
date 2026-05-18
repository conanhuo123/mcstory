#!/usr/bin/env python3
"""self_audit v2: ffmpeg signalstats 真测 frame-to-frame variance"""
import sys, subprocess, json, re
from pathlib import Path

def signal_motion(mp4):
    """用 ffmpeg select=gt(scene,0.03) 检测 scene cut, 高 = motion 多"""
    r = subprocess.run(["/opt/homebrew/bin/ffmpeg","-i",mp4,"-vf",
                        "select='gt(scene,0.02)',metadata=print",
                        "-an","-f","null","-"], capture_output=True, text=True, timeout=60)
    scene_cuts = r.stderr.count("scene_score=")
    return min(1.0, scene_cuts / 5)

def signal_yavg_diversity(mp4):
    """signalstats YAVG (luminance avg) 帧间 std → motion proxy"""
    r = subprocess.run(["/opt/homebrew/bin/ffmpeg","-i",mp4,"-vf",
                        "signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                        "-an","-f","null","-"], capture_output=True, text=True, timeout=60)
    vals = [float(m.group(1)) for m in re.finditer(r"YAVG=([\d.]+)", r.stderr)]
    if len(vals) < 2: return 0
    mean = sum(vals)/len(vals)
    std = (sum((v-mean)**2 for v in vals) / len(vals)) ** 0.5
    return min(1.0, std / 5)  # std=5+ 算高 motion

if __name__ == "__main__":
    mp4 = sys.argv[1]
    motion = signal_motion(mp4)
    luma_div = signal_yavg_diversity(mp4)
    print(json.dumps({"motion_signal": motion, "luma_diversity": luma_div, "pass": motion > 0.3 or luma_div > 0.3}, indent=2))
