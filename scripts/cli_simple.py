#!/usr/bin/env python3
"""cli_simple.py — death_sentence 极简样片渲染 + 自查闭环
固定机位第三人称, 三步动作, 3 句字幕, 输出 30fps. 自查不过自动重渲一次.
"""
import sys, os, json, subprocess, time, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
VF = Path.home() / "video_factory"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"
VIEWER_JS = ROOT / "scripts" / "simple_pov_viewer.js"
REC_DUR = 19


VIEWER_PORT = 3017  # 独立端口, 不与批量管线(3007)冲突


def kill_viewer():
    # 仅清理本管线自己的进程, 不动批量管线
    subprocess.run(["pkill", "-f", "_simple_pov_viewer.js"], capture_output=True)
    subprocess.run(["pkill", "-f", "_simple_recorder.js"], capture_output=True)
    time.sleep(1.5)


def make_recorder():
    """基于 puppeteer_recorder.js 生成指向独立端口的录制器"""
    src = (VF / "minecraft_bot" / "puppeteer_recorder.js").read_text()
    src = src.replace("localhost:3007", f"localhost:{VIEWER_PORT}")
    rec = VF / "minecraft_bot" / "_simple_recorder.js"
    rec.write_text(src)
    return rec


def render(work: Path):
    """跑一次渲染, 返回 final.mp4 路径 (失败 raise)"""
    kill_viewer()
    # viewer 需在 minecraft_bot 目录下解析 node_modules
    run_js = VF / "minecraft_bot" / "_simple_pov_viewer.js"
    shutil.copy(VIEWER_JS, run_js)
    recorder = make_recorder()
    vlog = work / "viewer.log"
    vp = subprocess.Popen(["node", str(run_js)], stdout=open(vlog, "w"),
                          stderr=subprocess.STDOUT, cwd=str(VF / "minecraft_bot"))
    print(f"[1/4] viewer PID={vp.pid}, 等 SCENE_READY ...")
    ready = False
    for _ in range(80):
        time.sleep(0.5)
        if vlog.exists() and "SCENE_READY" in vlog.read_text(errors="ignore"):
            ready = True
            break
    if not ready:
        vp.terminate()
        raise RuntimeError("viewer 未就绪 (无 SCENE_READY)")
    print("  场景就绪")

    raw = work / "raw.mp4"
    print(f"[2/4] puppeteer 录制 {REC_DUR}s -> raw.mp4")
    r = subprocess.run(["node", str(recorder), str(raw), str(REC_DUR)],
                       cwd=str(VF / "minecraft_bot"), capture_output=True, text=True, timeout=200)
    print("  ", (r.stdout or r.stderr).strip().split("\n")[-1][:120])
    try:
        vp.terminate()
    except Exception:
        pass
    if not raw.exists() or raw.stat().st_size < 1024 * 100:
        raise RuntimeError("raw.mp4 过小/缺失")

    final = work / "final.mp4"
    print("[3/4] 转码 30fps -> final.mp4")
    subprocess.run([FFMPEG, "-y", "-i", str(raw), "-r", "30", "-c:v", "libx264",
                    "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(final)],
                   capture_output=True)
    if not final.exists():
        raise RuntimeError("final.mp4 生成失败")
    return final


def selfcheck(final: Path, work: Path):
    """自查: ffprobe fps + preview_motion_check + 抽帧 sheet. 返回 (pass, report)"""
    rep = {"final": str(final)}
    # 1. ffprobe fps
    fps = subprocess.run([FFPROBE, "-v", "0", "-select_streams", "v:0", "-show_entries",
                          "stream=r_frame_rate", "-of", "csv=p=0", str(final)],
                         capture_output=True, text=True).stdout.strip()
    dur = subprocess.run([FFPROBE, "-v", "0", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(final)], capture_output=True, text=True).stdout.strip()
    rep["fps"] = fps
    rep["duration"] = dur
    rep["fps_ok"] = (fps == "30/1")
    rep["duration_ok"] = 15.0 <= float(dur or 0) <= 20.5

    # 2. preview_motion_check: 抽 12 帧, 判非空白 + 有运动
    fdir = work / "_frames"
    if fdir.exists():
        shutil.rmtree(fdir)
    fdir.mkdir()
    d = float(dur or 19)
    sizes = []
    for i in range(12):
        t = (i + 0.5) * d / 12
        fp = fdir / f"f{i:02d}.jpg"
        subprocess.run([FFMPEG, "-y", "-ss", str(t), "-i", str(final), "-vframes", "1", str(fp)],
                       capture_output=True)
        if fp.exists():
            sizes.append(fp.stat().st_size)
    avg_kb = (sum(sizes) / len(sizes) / 1024) if sizes else 0
    spread = ((max(sizes) - min(sizes)) / max(sizes)) if sizes and max(sizes) else 0
    rep["frame_avg_kb"] = round(avg_kb, 1)
    rep["frame_spread"] = round(spread, 3)
    not_blank = avg_kb > 18
    has_motion = spread > 0.04
    rep["motion_check"] = "PASS" if (not_blank and has_motion) else "FAIL"
    rep["motion_detail"] = f"not_blank={not_blank}(avg {avg_kb:.1f}KB) has_motion={has_motion}(spread {spread:.3f})"

    # 3. 抽帧 sheet (5x4 拼图)
    sheet = work / "frame_sheet.jpg"
    subprocess.run([FFMPEG, "-y", "-i", str(final), "-vf",
                    "fps=1,scale=420:-1,tile=5x4", "-frames:v", "1", str(sheet)],
                   capture_output=True)
    rep["frame_sheet"] = str(sheet) if sheet.exists() else "(失败)"

    rep["pass"] = rep["fps_ok"] and rep["duration_ok"] and rep["motion_check"] == "PASS"

    report_p = work / "selfcheck_report.json"
    report_p.write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    txt = work / "selfcheck_report.txt"
    txt.write_text(
        f"=== death_sentence 极简样片 自查报告 ===\n"
        f"final      : {final}\n"
        f"fps        : {fps}  ({'OK' if rep['fps_ok'] else 'FAIL — 需 30/1'})\n"
        f"duration   : {dur}s  ({'OK' if rep['duration_ok'] else 'FAIL — 需 15~20s'})\n"
        f"motion_chk : {rep['motion_check']}  [{rep['motion_detail']}]\n"
        f"frame_sheet: {rep['frame_sheet']}\n"
        f"结论       : {'PASS — 通过' if rep['pass'] else 'FAIL — 需重渲'}\n"
    )
    return rep["pass"], rep


def main():
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    work = ROOT / "outputs" / f"death_sentence_simple_pov_{ts}"
    work.mkdir(parents=True, exist_ok=True)
    print(f"=== death_sentence 极简样片 @ {ts} ===\n输出目录: {work}")

    attempt = 0
    rep = None
    while attempt < 2:
        attempt += 1
        print(f"\n--- 渲染尝试 {attempt}/2 ---")
        try:
            final = render(work)
        except Exception as e:
            print(f"  渲染异常: {e}")
            if attempt >= 2:
                print("自查结论: FAIL — 渲染两次均异常"); sys.exit(1)
            continue
        print("[4/4] 自查 ...")
        ok, rep = selfcheck(final, work)
        for k in ("fps", "duration", "motion_check", "motion_detail"):
            print(f"  {k}: {rep[k]}")
        if ok:
            break
        print("  自查未过, 自动重渲 ...")

    print("\n" + "=" * 48)
    print(f"final.mp4 : {work / 'final.mp4'}")
    print(f"自查结论  : {'PASS — 通过验收' if rep and rep['pass'] else 'FAIL — 未通过'}")
    print(f"自查报告  : {work / 'selfcheck_report.txt'}")
    print(f"抽帧 sheet: {work / 'frame_sheet.jpg'}")


if __name__ == "__main__":
    main()
