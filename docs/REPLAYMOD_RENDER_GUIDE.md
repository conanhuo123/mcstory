# ReplayMod Render Guide — 老板回家 5 分钟出 10 片

mcstory 已自动生成 10 个 `.mcpr` 文件 (真 ServerReplay 录制). 你只需 5 分钟操作就能把它们渲染成高质量 mp4.

## 一次性 setup (5 min)

### 1. 装 Fabric Loader 到你的 MC 客户端

打开 https://fabricmc.net/use/installer/ 下载 installer:
```bash
java -jar fabric-installer-1.0.1.jar client
# 选 1.20.4 → Install
```

### 2. 装 ReplayMod + Fabric API

下载放到 `~/Library/Application Support/minecraft/mods/`:
- ReplayMod: https://www.replaymod.com/download/  → 选 1.20.4 Fabric
- Fabric API: https://modrinth.com/mod/fabric-api → 选 1.20.4

### 3. 复制 .mcpr 到 ReplayMod 目录

```bash
mkdir -p ~/Library/Application\ Support/minecraft/replay_recordings/
cp ~/video_factory/fabric_server/recordings/chunks/*/*.mcpr \
   ~/Library/Application\ Support/minecraft/replay_recordings/
```

## 渲染 (3 min/片)

### 4. 启 MC 客户端

打开 Minecraft Launcher → 选 "fabric-loader-0.16.9-1.20.4" → Play

### 5. 打开 Replay Viewer

主菜单 → Replay Viewer (ReplayMod 加的菜单项) → 选 mcstory_*.mcpr 列表的第一个 → Open

### 6. 设摄像机 keyframe + 渲染

ReplayMod 进入回放:
- `Space` 暂停
- 滑右下时间轴到 0:00 → `K` 设第一个 keyframe (Time + Position)
- 滑到 0:05 → 移摄像机 → `K`
- 重复直到 0:30
- 工具栏 → 三脚架 icon → Render Settings
- Quality: 1080p / 60fps / MP4 / H.264
- Render → 等 ~30s/片

### 7. 输出 mp4 在

`~/Library/Application Support/minecraft/replay_videos/<replay_name>/`

## Batch Render (10 片一次性)

ReplayMod 有 batch render 模式: Settings → Rendering → "Render Queue". 把 10 个 .mcpr 加入队列 → Render All → 30 min 后回来 10 个 mp4 全好.

## 当前 .mcpr 清单

```
~/video_factory/fabric_server/recordings/chunks/
├── Chunks (-7, -14) to (-1, -8)/2026-05-18--15-30-05.mcpr   (judge_death)
├── Chunks (-7, -14) to (-1, -8)/2026-05-18--XX-XX-XX.mcpr   (creeper_refuse)
├── ... (其余 8 个, 跑批中)
```

## Render 后干嘛

把 10 个 mp4 拖到 `~/mcstory/docs/demos/` 替换 puppeteer 低质量版, push GitHub Pages 自动更新.

## 自动化路径 (老板回家后我自动跑)

```bash
cp ~/Library/Application\ Support/minecraft/replay_videos/*/*.mp4 ~/mcstory/docs/demos/
cd ~/mcstory && git add docs/demos/ && git commit -m "v3.0 ReplayMod-rendered demos" && git push
```

GitHub Pages 1-2 min 后 https://conanhuo123.github.io/mcstory/ 显示真高质量 demo.
