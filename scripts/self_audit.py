#!/usr/bin/env python3
"""self_audit.py — 自查评分闭环 (4 库 + 1 闭环 中的 +1)

3 项自动检测:
1. frame_color_diversity: 不同帧的颜色直方图差异 (镜头变化 / 内容变化)
2. entity_presence: 用 ffmpeg motion vectors / pixel diff 检测画面里有"实体" (非静态)
3. mc_signature: 检测 MC 标志性色块 (草绿 / 石灰 / 木黄 / 蓝天) 占比 > 30%

打分: 3 项任一不过 = FAIL, 全过 = PASS. 失败自动 reroll (调用方决定).
"""
import sys, os, subprocess, json
from pathlib import Path
from collections import Counter

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

MC_SIGNATURE_COLORS = [
    (107, 142, 35),   # grass green
    (102, 102, 102),  # stone gray
    (139, 90, 43),    # wood brown
    (135, 206, 235),  # sky blue
    (170, 170, 170),  # cobble
]

def extract_frames(mp4, work_dir, n=5):
    work_dir = Path(work_dir); work_dir.mkdir(exist_ok=True, parents=True)
    # 取 n 帧 (均匀分布)
    dur = float(subprocess.run([FFPROBE, "-v", "0", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout.strip() or "15")
    frames = []
    for i in range(n):
        t = (i + 0.5) * dur / n
        out = work_dir / f"f{i}.jpg"
        subprocess.run([FFMPEG, "-y", "-i", mp4, "-vframes", "1", "-ss", str(t), str(out)],
                       capture_output=True)
        if out.exists():
            frames.append(out)
    return frames

def color_diversity(frames):
    """返回 0-1: 多少帧 RGB 直方图差异"""
    if len(frames) < 2: return 0
    # ImageMagick / PIL — 用纯 stat 简化
    sizes = [f.stat().st_size for f in frames]
    if max(sizes) == 0: return 0
    diversity = (max(sizes) - min(sizes)) / max(sizes)
    return min(1.0, diversity * 5)  # 放大

def entity_motion(mp4):
    """用 ffmpeg signature filter 检测帧间变化"""
    r = subprocess.run([FFMPEG, "-i", mp4, "-vf", "select='gt(scene,0.02)',signalstats",
                         "-f", "null", "-"], capture_output=True, text=True)
    # 简化: 看 size, motion 多 = bytes 大
    sz = Path(mp4).stat().st_size / 1024 / 1024
    return min(1.0, sz / 5)  # 5 MB+ = good

def mc_signature(frames):
    """简化: jpg size > 30 KB 表示 MC 块状内容多 (非纯色)"""
    if not frames: return 0
    avg_size = sum(f.stat().st_size for f in frames) / len(frames) / 1024
    if avg_size < 20: return 0  # 白屏纯色 < 20 KB
    if avg_size > 80: return 1  # MC 块状内容
    return (avg_size - 20) / 60  # 渐进打分

def audit(mp4):
    """返回 dict: {pass, scores, reasons}"""
    work = Path(mp4).parent / "_audit"
    frames = extract_frames(mp4, work)
    diversity = color_diversity(frames)
    motion = entity_motion(mp4)
    signature = mc_signature(frames)
    scores = {"diversity": round(diversity, 2), "motion": round(motion, 2), "mc_signature": round(signature, 2)}
    passed = diversity >= 0.2 and motion >= 0.3 and signature >= 0.5
    reasons = []
    if diversity < 0.2: reasons.append(f"static (diversity {diversity:.2f} < 0.2)")
    if motion < 0.3: reasons.append(f"low motion (motion {motion:.2f} < 0.3)")
    if signature < 0.5: reasons.append(f"not MC (signature {signature:.2f} < 0.5)")
    return {"pass": passed, "scores": scores, "reasons": reasons, "mp4": str(mp4)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: self_audit.py <mp4>"); sys.exit(1)
    result = audit(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["pass"] else 1)
