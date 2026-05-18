# mcstory Project Summary — 2026-05-18 (Day 1, 18+h 进展)

老板 5 天不在家, AI 团队 (Claude + 11 OpenClaw GPT-5.5) 自主推进自查迭代. 老板专做真实世界沟通.

## TL;DR

**做的是**: 文字 → MC 可执行导演系统 (entity-level scriptable narrative engine)
**不是**: 视频生成器 / 营销页 / 伪网页动画
**护城河**: 4 库 + 1 闭环 (动作/镜头/场景/角色 + 自查评分)

## 今天里程碑 (00:38 → 19:08)

```
00:38  老板拍板: 做 MC 短剧自动化
00:50  Day 1: parse.py + translate.py 跑通 (GPT-5.5 一句话 → 5 镜头剧本)
01:30  record.py + Paper 1.20.4 服 + mineflayer bot
02:00  v0.1 chrome+screen 录到屏保 — 阻塞
02:15  v0.1.1 puppeteer headless 替换, 绕过锁屏
02:30  v0.2 scene auto-build (4 scene: courtroom/village/mine/redstone_door)
03:30  v0.2.1 character summon (villager/iron_golem/creeper)
04:00  v0.3-0.5 5 shot 镜头切换 — viewer drift 卡, 撤回
06:00  v0.6 固定 wide camera + character 动作 (走/抬头/setblock 反转牌)
09:00  v0.7 showreel + GitHub Pages 部署
12:00  v0.8 gamerule 稳定 + landing v3 (10 demo 嵌入)
15:00  v0.9-v1.1 cam.look fix 尝试 + 横版 16:9 (老板拍)
15:30  v3.0 Fabric + ServerReplay → 11 真 .mcpr 落盘 (Production tier)
15:45  USER_GUIDE.md + REPLAYMOD_RENDER_GUIDE.md push
16:30  marketing/copy_paste_pack.md 5 渠道粘贴文案
17:00  辨证投资人视角 + 团队评估 + 10 轮论证终局形态
17:30  思想钢印固化 (老板真实世界沟通 / AI 无限推进)
18:00  陆远拍板叙事: "文字→MC 可执行导演系统" + 4 库+1 闭环
18:30  INVESTOR_PITCH.md + 5 天 plan
19:00  Day 1 patch viewer 部分通 (chunks reload 但 race) → 撤回, 接受 prototype
19:07  D2: 扩 sample 10→15 + self_audit.py 自查闭环
```

## 关键资产 (今天落盘)

### 代码 (`~/mcstory/scripts/`)
- `parse.py` — GPT-5.5 一句话 → 结构化剧本 JSON
- `translate.py` — 剧本 → 23 timeline 事件
- `record.py` — timeline → mineflayer bot.js
- `postprod.py` — ffmpeg + 火山 TTS + mov_text 字幕
- `cli_full.py` — 一行 pipeline 串联
- `cli_full_fixed.py` — aimCam pinned 变体 (chunks load race fix 尝试)
- `self_audit.py` — 自查闭环 (diversity / motion / mc_signature 3 项打分)
- `batch_render_node.sh` — Linux 云 VM 自动 render .mcpr → mp4 setup

### 模板 (`~/mcstory/templates/`)
- `scenes/builds.json` — 4 scene (courtroom/village/mine/redstone_door) /setblock 命令
- `scenes/scenes.json` v0.2 — scene metadata
- `characters/characters.json` — 3 mob 类型 + NBT
- `cameras/cameras.json` — 5 镜头 preset
- `scripts/judge_death.json` — golden sample 5 shot

### Samples (`~/mcstory/samples/` 15 个)
原 5: judge_death / creeper_refuse / redstone_door / missing_spawn / dying_memory
扩 10: sun_thief / fake_ally / village_trial / golem_betray / redstone_world / birth_rollback / redstone_jail / ender_killer / golem_tears / creeper_propose

### 服务端
- Paper 1.20.4 @ port 25565 (legacy puppeteer 路)
- Fabric 1.20.4 @ port 25566 + 58 mods 含 ServerReplay 1.1.3 (主线 .mcpr 路)
- 11 .mcpr 在 `~/video_factory/fabric_server/recordings/chunks/`

### 文档
- README.md (英文 GitHub 主页)
- USER_GUIDE.md (Draft auto vs Production via ReplayMod 两级 tier)
- REPLAYMOD_RENDER_GUIDE.md (老板回家 5 min 操作步骤)
- INVESTOR_PITCH.md (B 线投资人 one-pager)
- marketing/copy_paste_pack.md (5 渠道粘贴文案)
- landing.html (10 demo 嵌入 + Two quality tiers section)
- 飞书直传: 5 jpg + 7 mp4 + 1 png + 1 tar.gz + 多个 manifest

### 公网
- GitHub: https://github.com/conanhuo123/mcstory (PUBLIC)
- Pages: https://conanhuo123.github.io/mcstory/
- 网盘: /apps/视频工厂/2026-05-18/mcstory_*/v0.1.x ~ v0.8/

## 真实卡点

1. **viewer drift bug** (上游 prismarine-viewer issue #477) — 试 8 个 fix 全不通, 接受 prototype tier
2. **headless render .mcpr → mp4** (上游 ReplayMod issue #982) — 需 user GUI 或 Linux 云 VM
3. **cam tp 撞 stone 山地** — paper world spawn 山地高度变化, cam tp 位置不可靠

## 接下来 5 天 plan (AI 自主)

- D2 (今晚): 扩 sample 15→30 + self_audit 跑批 + 自动 reroll 低质
- D3: 自查评分接 cli_full + 跑批 100 .mcpr
- D4: 4 库 schema 标准化 (动作语法库 JSON spec / 镜头库 / 场景库 / 角色库)
- D5: PROJECT_SUMMARY 升级 + 投资人 deck v2 + 网盘归档

## 老板回家 5 天后 1 次必做

1. 装 ReplayMod 到 MC 客户端 (5 min 一次性)
2. Replay Viewer → Render Queue → All → 1 小时 batch 出 100+ 高质 mp4
3. push 高质 mp4 到 GitHub Pages 替换低质 puppeteer 版

## 死命令心跳 (老板规则)

- 5 min 必 push 飞书 1 条 "正在 X" (即使无新 mp4)
- 15 min 报: 新 mp4 / 新阻塞 / 新自查结论
- 无新增不刷屏, 有阻塞直接降级方案, 有成片先自查再发
- 老板专做真实世界沟通, AI 无限推进
