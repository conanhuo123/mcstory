#!/usr/bin/env python3
"""cli_door_anomaly.py — 一人称任务流样片 (simple_pov_task v1) 渲染 + 自查闭环

开门 -> 看到异常 -> 靠近 -> 触发事件 -> 逃跑/反转。
单机位第一人称, 15s, 30fps, 1920x1080, 烧录中文字幕。自查不过自动重渲一次。
输出: outputs/simple_pov_<timestamp>/final.mp4
"""
import sys, os, json, subprocess, time, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
VF = Path.home() / "video_factory"
BOT_DIR = VF / "minecraft_bot"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"
VIEWER_JS = ROOT / "scripts" / "door_anomaly_pov_viewer.js"
RECORDER_JS = ROOT / "scripts" / "pov_recorder.js"
GO_FILE = "/tmp/_pov_rec_go"
REC_DUR = 15.5          # 录制真实秒数
FINAL_DUR = 15          # 成片裁到 15s
FONT_SRC = "/System/Library/Fonts/STHeiti Medium.ttc"

# 5 节拍字幕 (起, 止, 文本)
BEATS = [
    (0.0, 3.0,  "推开这扇门"),
    (3.2, 6.0,  "里面有人  背对着我"),
    (6.2, 9.3,  "我慢慢走近"),
    (9.5, 11.8, "它猛地转过头"),
    (12.0, 15.0, "回头——出口没了"),
]


def kill_viewer():
    subprocess.run(["pkill", "-f", "_door_pov_viewer.js"], capture_output=True)
    subprocess.run(["pkill", "-f", "_pov_recorder.js"], capture_output=True)
    time.sleep(1.5)


def render(work: Path):
    """跑一次渲染, 返回 raw.mp4 路径 (失败 raise)"""
    kill_viewer()
    try:
        os.remove(GO_FILE)
    except OSError:
        pass

    run_viewer = BOT_DIR / "_door_pov_viewer.js"
    run_rec = BOT_DIR / "_pov_recorder.js"
    shutil.copy(VIEWER_JS, run_viewer)
    shutil.copy(RECORDER_JS, run_rec)

    vlog = work / "viewer.log"
    vp = subprocess.Popen(["node", str(run_viewer)], stdout=open(vlog, "w"),
                          stderr=subprocess.STDOUT, cwd=str(BOT_DIR))
    print(f"[1/4] viewer PID={vp.pid}, 等 SCENE_READY ...")
    ready = False
    for _ in range(90):
        time.sleep(0.5)
        if vlog.exists() and "SCENE_READY" in vlog.read_text(errors="ignore"):
            ready = True
            break
        if vp.poll() is not None:
            raise RuntimeError("viewer 进程提前退出, 见 viewer.log")
    if not ready:
        vp.terminate()
        raise RuntimeError("viewer 未就绪 (无 SCENE_READY)")
    print("  场景就绪")

    raw = work / "raw.mp4"
    print(f"[2/4] puppeteer 录制 {REC_DUR}s -> raw.mp4 (含 settle, 录制器写 GO 触发时间轴)")
    rlog = work / "recorder.log"
    r = subprocess.run(["node", str(run_rec), str(raw), str(REC_DUR)],
                       cwd=str(BOT_DIR), capture_output=True, text=True, timeout=240)
    rlog.write_text((r.stdout or "") + "\n--- stderr ---\n" + (r.stderr or ""))
    print("  ", (r.stdout or r.stderr).strip().split("\n")[-1][:140])
    try:
        vp.terminate()
    except Exception:
        pass
    if not raw.exists() or raw.stat().st_size < 1024 * 80:
        raise RuntimeError("raw.mp4 过小/缺失, 见 recorder.log")
    return raw


def make_sub_png(text: str, path: Path):
    """用 Pillow 把一句中文字幕渲染成 1920x1080 透明 PNG (白字黑描边, 底部居中)"""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1920, 1080
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_SRC, 62, index=0)
    bbox = d.textbbox((0, 0), text, font=font, stroke_width=7)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (W - tw) / 2 - bbox[0]
    y = H - 200 - bbox[1]
    d.text((x, y), text, font=font, fill=(255, 255, 255, 255),
           stroke_width=7, stroke_fill=(0, 0, 0, 235))
    img.save(path)


def transcode(raw: Path, work: Path):
    """裁到 15s + 30fps + 叠加中文字幕 PNG -> final.mp4"""
    pngs = []
    for i, (a, b, text) in enumerate(BEATS):
        p = work / f"sub_{i}.png"
        make_sub_png(text, p)
        pngs.append(p)

    inputs = ["-i", str(raw)]
    for p in pngs:
        inputs += ["-i", str(p)]

    # filter_complex: 基底 30fps/1080p, 逐句 overlay (enable 时间窗)
    parts = ["[0:v]fps=30,scale=1920:1080[base]"]
    prev = "base"
    for i, (a, b, _) in enumerate(BEATS):
        nxt = f"v{i}"
        parts.append(f"[{prev}][{i+1}:v]overlay=0:0:enable='between(t,{a},{b})'[{nxt}]")
        prev = nxt
    fc = ";".join(parts)

    final = work / "final.mp4"
    print("[3/4] 转码 15s/30fps + 叠字幕 -> final.mp4")
    r = subprocess.run([FFMPEG, "-y", *inputs, "-t", str(FINAL_DUR),
                        "-filter_complex", fc, "-map", f"[{prev}]",
                        "-c:v", "libx264", "-preset", "medium",
                        "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(final)],
                       capture_output=True, text=True)
    if not final.exists():
        raise RuntimeError("final.mp4 生成失败: " + r.stderr[-400:])
    return final


def selfcheck(final: Path, work: Path):
    """自查: ffprobe fps/分辨率/时长 + preview_motion_check + 抽帧 sheet"""
    rep = {"final": str(final)}
    info = subprocess.run([FFPROBE, "-v", "0", "-select_streams", "v:0", "-show_entries",
                           "stream=r_frame_rate,width,height", "-of", "json", str(final)],
                          capture_output=True, text=True).stdout
    st = json.loads(info)["streams"][0]
    fps = st["r_frame_rate"]
    dur = subprocess.run([FFPROBE, "-v", "0", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(final)], capture_output=True, text=True).stdout.strip()
    rep["fps"] = fps
    rep["resolution"] = f"{st['width']}x{st['height']}"
    rep["duration"] = dur
    rep["fps_ok"] = (fps == "30/1")
    rep["res_ok"] = (st["width"] == 1920 and st["height"] == 1080)
    rep["duration_ok"] = 14.4 <= float(dur or 0) <= 16.0

    # preview_motion_check: 抽 12 帧, 判非空白 + 有运动
    fdir = work / "_frames"
    if fdir.exists():
        shutil.rmtree(fdir)
    fdir.mkdir()
    d = float(dur or 15)
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

    # 抽帧 sheet (5x4)
    sheet = work / "frame_sheet.jpg"
    subprocess.run([FFMPEG, "-y", "-i", str(final), "-vf",
                    "fps=20/15,scale=420:-1,tile=5x4", "-frames:v", "1", str(sheet)],
                   capture_output=True)
    rep["frame_sheet"] = str(sheet) if sheet.exists() else "(失败)"

    # 关键节拍单帧 (供人工四项检查)
    keys = {"t01_door_closed": 1.0, "t05_anomaly": 5.0, "t08_approach": 8.0,
            "t10_trigger": 10.2, "t13_twist": 13.5}
    kdir = work / "_keyframes"
    kdir.mkdir(exist_ok=True)
    rep["keyframes"] = {}
    for name, t in keys.items():
        kp = kdir / f"{name}.jpg"
        subprocess.run([FFMPEG, "-y", "-ss", str(t), "-i", str(final), "-vframes", "1", str(kp)],
                       capture_output=True)
        rep["keyframes"][name] = str(kp) if kp.exists() else "(失败)"

    rep["auto_pass"] = (rep["fps_ok"] and rep["res_ok"] and rep["duration_ok"]
                        and rep["motion_check"] == "PASS")
    return rep["auto_pass"], rep


def write_report(work: Path, rep: dict, attempts: int):
    md = work / "selfcheck_report.md"
    fails = []
    if not rep["fps_ok"]:
        fails.append(f"fps={rep['fps']} (需 30/1)")
    if not rep["res_ok"]:
        fails.append(f"分辨率={rep['resolution']} (需 1920x1080)")
    if not rep["duration_ok"]:
        fails.append(f"时长={rep['duration']}s (需 ~15s)")
    if rep["motion_check"] != "PASS":
        fails.append(f"motion_check FAIL ({rep['motion_detail']})")

    lines = [
        "# door_anomaly 一人称任务流样片 — 自查报告",
        "",
        f"- 渲染次数: {attempts}",
        f"- 成片: `{rep['final']}`",
        "",
        "## 机器检查 (ffprobe / preview_motion_check)",
        "",
        "| 项 | 值 | 结论 |",
        "|---|---|---|",
        f"| 帧率 | {rep['fps']} | {'OK' if rep['fps_ok'] else 'FAIL — 需 30/1'} |",
        f"| 分辨率 | {rep['resolution']} | {'OK' if rep['res_ok'] else 'FAIL — 需 1920x1080'} |",
        f"| 时长 | {rep['duration']}s | {'OK' if rep['duration_ok'] else 'FAIL — 需 ~15s'} |",
        f"| preview_motion_check | {rep['motion_check']} | {rep['motion_detail']} |",
        "",
        f"抽帧 sheet: `{rep['frame_sheet']}`",
        "",
        "## 人工规则四项检查 (依据关键帧)",
        "",
        "| 项 | 结论 | 依据 |",
        "|---|---|---|",
        f"| 主视角清楚 | {rep.get('r_view','-')} | {rep.get('r_view_d','-')} |",
        f"| 动作目标清楚 | {rep.get('r_goal','-')} | {rep.get('r_goal_d','-')} |",
        f"| 触发事件清楚 | {rep.get('r_trigger','-')} | {rep.get('r_trigger_d','-')} |",
        f"| 反转清楚 | {rep.get('r_twist','-')} | {rep.get('r_twist_d','-')} |",
        "",
        "关键帧:",
    ]
    for name, p in rep.get("keyframes", {}).items():
        lines.append(f"- {name}: `{p}`")
    lines += [
        "",
        "## 结论",
        "",
        f"- 机器检查: {'PASS' if rep['auto_pass'] else 'FAIL'}",
        f"- 失败项: {('; '.join(fails)) if fails else '无'}",
        f"- 最终结论: {rep.get('final_verdict','(待人工四项填写)')}",
        "",
    ]
    md.write_text("\n".join(lines))
    return md


def main():
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    work = ROOT / "outputs" / f"simple_pov_{ts}"
    work.mkdir(parents=True, exist_ok=True)
    print(f"=== door_anomaly 一人称任务流样片 @ {ts} ===\n输出目录: {work}")

    attempt = 0
    rep = None
    while attempt < 2:
        attempt += 1
        print(f"\n--- 渲染尝试 {attempt}/2 ---")
        try:
            raw = render(work)
            final = transcode(raw, work)
        except Exception as e:
            print(f"  渲染异常: {e}")
            if attempt >= 2:
                print("自查结论: FAIL — 渲染两次均异常")
                sys.exit(1)
            continue
        print("[4/4] 自查 ...")
        ok, rep = selfcheck(final, work)
        for k in ("fps", "resolution", "duration", "motion_check"):
            print(f"  {k}: {rep[k]}")
        if ok:
            break
        print("  机器自查未过, 自动重渲 ...")

    md = write_report(work, rep, attempt)
    print("\n" + "=" * 52)
    print(f"final.mp4 : {work / 'final.mp4'}")
    print(f"机器自查  : {'PASS' if rep and rep['auto_pass'] else 'FAIL'}")
    print(f"自查报告  : {md}")
    print(f"关键帧目录: {work / '_keyframes'}")
    # 退出码: 机器检查通过 0, 否则 2 (人工四项另行判定)
    sys.exit(0 if (rep and rep["auto_pass"]) else 2)


if __name__ == "__main__":
    main()
