#!/usr/bin/env python3
"""postprod.py — 录屏 mp4 + timeline → 成片
- 火山 TTS 生成 voiceover
- ffmpeg 烧字幕 + 混 BGM + 拼接
"""
import sys, json, os, subprocess
from pathlib import Path

FFMPEG = "/opt/homebrew/bin/ffmpeg"
TTS = os.path.expanduser("~/video_factory/scripts/volcano_tts.py")

def gen_voiceover(timeline, out_dir):
    """每条 voiceover → mp3, 返回 [(t, end_t, mp3_path)]"""
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for i, ev in enumerate(timeline["timeline"]):
        if ev["type"] == "voiceover":
            mp3 = out_dir / f"vo_{i:02d}.mp3"
            subprocess.run(["python3", TTS, ev["text"], str(mp3)], check=False)
            items.append((ev["t"], ev.get("end_t", ev["t"]+3), str(mp3)))
    return items

def gen_srt(timeline, out_path):
    """字幕事件 → srt"""
    def fmt(t):
        h = int(t//3600); m = int((t%3600)//60); s = t%60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
    lines = []
    idx = 1
    for ev in timeline["timeline"]:
        if ev["type"] == "subtitle":
            lines.append(f"{idx}\n{fmt(ev['t'])} --> {fmt(ev.get('end_t', ev['t']+3))}\n{ev['text']}\n")
            idx += 1
    open(out_path, "w").write("\n".join(lines))
    return out_path

def compose(raw_mp4, timeline_path, out_mp4):
    timeline = json.load(open(timeline_path))
    work = Path(out_mp4).parent / "_postprod_tmp"
    work.mkdir(parents=True, exist_ok=True)
    
    # 1. SRT
    srt = work / "subs.srt"
    gen_srt(timeline, srt)
    print(f"✓ SRT: {srt}")
    
    # 2. Voiceover
    vo_items = gen_voiceover(timeline, work / "vo")
    print(f"✓ Voiceover: {len(vo_items)} 段")
    
    # 3. 拼配音轨 (用 ffmpeg adelay 把每段 mp3 推到对应秒)
    vo_inputs = []
    filters = []
    for i, (t, end_t, mp3) in enumerate(vo_items):
        vo_inputs += ["-i", mp3]
        filters.append(f"[{i+1}:a]adelay={int(t*1000)}|{int(t*1000)}[a{i}]")
    if vo_items:
        mix = "".join(f"[a{i}]" for i in range(len(vo_items)))
        filter_complex = ";".join(filters) + f";{mix}amix=inputs={len(vo_items)}:dropout_transition=0[aout]"
        # 分两步: 1) 合配音轨 + 视频  2) 再 -vf 加字幕 (subtitles filter 单独跑稳)
        mid = str(Path(out_mp4).with_suffix(".novo.mp4"))
        cmd1 = [FFMPEG, "-y", "-i", raw_mp4, *vo_inputs,
               "-filter_complex", filter_complex,
               "-map", "0:v", "-map", "[aout]",
               "-c:v", "copy", "-c:a", "aac", "-shortest", mid]
        print("  step1: mix audio...")
        r = subprocess.run(cmd1, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  step1 err: {r.stderr[-400:]}"); return False
        # step2: 嵌入 mov_text 字幕 (ffmpeg 8.1 没编 libass, 改软字幕)
        cmd = [FFMPEG, "-y", "-i", mid, "-i", str(srt),
               "-map", "0:v", "-map", "0:a", "-map", "1:s",
               "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text", out_mp4]
    else:
        cmd = [FFMPEG, "-y", "-i", raw_mp4, "-vf", f"subtitles={srt}", "-c:a", "copy", out_mp4]
    print("  running ffmpeg...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ffmpeg err: {r.stderr[-500:]}")
        return False
    print(f"✓ 成片: {out_mp4} ({os.path.getsize(out_mp4)/1024/1024:.1f} MB)")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: postprod.py raw_mp4 timeline.json out.mp4"); sys.exit(1)
    compose(sys.argv[1], sys.argv[2], sys.argv[3])
