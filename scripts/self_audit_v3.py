#!/usr/bin/env python3
"""self_audit_v3 — entity-color presence detection (检测 villager/iron_golem/creeper 在画面)"""
import sys, subprocess, json, os, re
from pathlib import Path

def extract_frames(mp4, n=5):
    work = Path(mp4).parent / "_audit3"
    work.mkdir(exist_ok=True)
    dur = float(subprocess.run(["/opt/homebrew/bin/ffprobe","-v","0","-show_entries","format=duration",
                                 "-of","csv=p=0", mp4], capture_output=True, text=True).stdout.strip() or "15")
    frames = []
    for i in range(n):
        t = (i+0.5) * dur / n
        out = work / f"f{i}.png"
        subprocess.run(["/opt/homebrew/bin/ffmpeg","-y","-i",mp4,"-vframes","1","-ss",str(t),"-vf","scale=128:-1", str(out)],
                       capture_output=True)
        if out.exists(): frames.append(out)
    return frames

ENTITY_COLORS = {
    "villager": [(139, 90, 60), (160, 110, 80), (190, 140, 90)],  # 棕色 villager
    "iron_golem": [(220, 220, 200), (240, 240, 220)],              # 白色 iron_golem
    "creeper": [(80, 160, 80)],                                    # 绿色 creeper
    "steve": [(40, 70, 180), (80, 110, 200)],                      # 蓝衣 steve
}

def color_presence(frame_paths, target_rgb, tol=40):
    """检测 target 颜色像素占比"""
    if not frame_paths: return 0
    # 用 ffmpeg geq 提取色范围占比 — 简化: 用 PIL/cv2 计 hist
    try:
        from PIL import Image
        hits = 0; total = 0
        for fp in frame_paths:
            im = Image.open(fp).convert("RGB")
            data = im.getdata()
            for px in data:
                total += 1
                for r,g,b in target_rgb:
                    if abs(px[0]-r) < tol and abs(px[1]-g) < tol and abs(px[2]-b) < tol:
                        hits += 1; break
        return hits / total if total else 0
    except Exception as e:
        return 0

def audit(mp4):
    frames = extract_frames(mp4)
    results = {}
    for name, colors in ENTITY_COLORS.items():
        p = color_presence(frames, colors)
        results[name] = round(p * 100, 2)  # 百分比
    # 任一 entity > 0.5% 算 PASS
    passed = max(results.values()) > 0.5
    return {"pass": passed, "entity_presence_pct": results, "mp4": str(mp4)}

if __name__ == "__main__":
    if len(sys.argv) < 2: print("Usage: self_audit_v3.py <mp4>"); sys.exit(1)
    print(json.dumps(audit(sys.argv[1]), indent=2))
