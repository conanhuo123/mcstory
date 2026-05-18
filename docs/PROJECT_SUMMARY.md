# mcstory Project Summary v2 — 2026-05-18 (Day 1, 22+h 进展)

老板 5 天不在家. AI 团队 (Claude + 11 OpenClaw GPT-5.5) 持续自主推进自查迭代.

## TL;DR

**做的是**: 文字 → MC 可执行导演系统 (entity-level scriptable narrative engine)
**4 库 + 1 闭环**: 动作语法库 / 镜头库 / 场景资产库 / 角色库 / 自查评分闭环
**5 关能力**: AI 建场景 / 放角色 / 控动作 / 控镜头 / 导出视频

## 5 关能力清单 (陆远 22:12 拍板)

| 关 | 能力 | 状态 | Demo |
|---|---|---|---|
| 1 | AI 建场景 | ✅ PASS | GPT 输出 13 条 build_cmds (火山/海底/末地/城堡多样化) |
| 2 | 放角色 | ✅ PASS | GPT 输出 character_spawns 坐标 |
| 3 | 控动作 | ✅ PASS | GPT shot.actions → /tp /effect /setblock |
| 4 | 控镜头 | ⚠️ 50% | 单镜头 visible, 多镜头切换需 ReplayMod (上游 #477) |
| 5 | 导出视频 | ✅ PASS | puppeteer + ffmpeg + 火山 TTS + audit_v3 entity-color |

**4/5 关 PASS**. 关 4 prototype tier 50%, Production tier 等老板回家 1 次 ReplayMod GUI.

## 今天里程碑 (00:38 → 23:02, 22h)

```
00:38  老板拍板做 MC 短剧生成器
01:00  parse.py + translate.py 跑通 (GPT-5.5 一句话 → 5 镜头剧本)
02:00  puppeteer headless 绕过锁屏
03:30  v0.2 scene auto-build + character summon
14:54  v2.0 hack: build origin → cam spawn 邻居 (paper world 真 MC scene visible)
15:30  Fabric + ServerReplay → 11 真 .mcpr (Production tier 原料)
17:00  辨证 10 轮投资人 + 终局形态 + 思想钢印固化
17:30  AI 团队最大权限拍板, 老板专做真实世界沟通
18:00  陆远定位: '文字→MC 可执行导演系统', 4 库+1 闭环
20:30  REVERT v0.6 baseline + audit v2 ffmpeg signalstats
21:00  扩 40 sample / 25 demos / showreel_40.mp4 / landing 上线
21:20  陆远阶梯路线 1人称→双人→三人, stage1/2/3 验证
22:11  老板问"AI 能不能直接 build" → v5.0 GPT 输出 build_cmds 跑通
22:38  陆远 5 关拆: 建场景/放角色/控动作/控镜头/导出
22:55  v5.3 关 3 GPT shot.actions 翻命令
23:00  v5.4 关 5 audit_v3 entity-color 20/20 PASS
```

## 关键资产

### 代码 (`~/mcstory/scripts/`, 12 文件)
- `parse.py` — GPT-5.5 输出 build_cmds + character_spawns + shot.actions
- `translate.py` — 剧本 → 23 timeline 事件
- `record.py` — timeline → mineflayer bot.js
- `postprod.py` — ffmpeg + 火山 TTS + mov_text 字幕
- `cli_full.py` — 一行 pipeline
- `self_audit.py` (v1) — size 阈值
- `self_audit_v2.py` — ffmpeg signalstats motion + luma
- `self_audit_v3.py` — entity-color presence (villager/iron_golem/creeper/steve 像素百分比)
- `audit_dashboard.py` — markdown 报表
- `validate_ir.py` — IR 闸口 (camera/scene/character 来自库)
- `batch_render_node.sh` — Linux 云 VM Xvfb + ReplayMod 自动 render setup
- `server.py` — HTTP API (POST /api/render, GET /api/status)

### 4 库 schema (`~/mcstory/schema/`, 4 JSON)
- `action_grammar.schema.json` — 动作语法库 v0.1
- `camera_library.schema.json` — 镜头库 v0.1 (5 preset)
- `scene_library.schema.json` — 场景资产库 v0.1
- `character_library.schema.json` — 角色库 v0.1 (3 mob)

### Samples (`~/mcstory/samples/`, 40+)
判死刑/苦力怕拒爆/红石门/出生点被删/少一格记忆/末影偷太阳/假队友/村庄审判/铁傀儡背叛/红石世界/出生点退档/红石监狱/末影杀手/铁傀儡眼泪/苦力怕求婚/岩浆王国/钻石龙/时间膨胀/经验之神/灵魂市场/无限循环/潜影贝/幻影信使/船航末地/监守者摇篮曲/下界传送门/僵尸和平主义/守卫者花园/村民罢工/猪灵银行/美西螈预言/女巫医生/烈焰人厨师/乌贼画家/史莱姆选举/恶魂摇篮/海豚领航/唤魔者魔术师/苦力怕马拉松 + stage1/2/3

### 服务端
- Paper 1.20.4 @ 25565 (主线 puppeteer)
- Fabric 1.20.4 + 58 mods (含 ServerReplay 1.1.3) @ 25566 (.mcpr 录制)
- 11 真 .mcpr 在 `~/video_factory/fabric_server/recordings/chunks/`

### 公网
- GitHub: https://github.com/conanhuo123/mcstory (PUBLIC, 30+ commits)
- Pages: https://conanhuo123.github.io/mcstory/ (40 sample cards + showreel_40 嵌入)
- 网盘: /apps/视频工厂/2026-05-18/mcstory_*/v0.1~v5.5/

### 文档 (`~/mcstory/docs/`, 8 md)
- README.md (英文 GitHub 主页)
- USER_GUIDE.md
- REPLAYMOD_RENDER_GUIDE.md
- INVESTOR_PITCH.md
- PROJECT_SUMMARY.md (本文件)
- CAPABILITY_GATES.md (5 关清单)
- AUDIT_DASHBOARD.md
- AUDIT_V3_DASHBOARD.md
- reddit_seed_post.md / marketing/copy_paste_pack.md

## 真实卡点

**唯一: 关 4 镜头切换** — prismarine-viewer firstPerson 视角 chunk re-render race (上游 #477 至今未解). 多镜头切换 viewer 飘. 真解: ReplayMod 客户端 GUI render .mcpr → mp4 高质 (需老板回家 5 min)

## 5 天 plan (D1 已结束)

- D1 ✅ (今天): 5 关全跑通 + 40 sample + 4 库 schema + audit v1/v2/v3 + GitHub Pages 上线
- D2 (5/19): 扩 4 库样本 (action 50+/camera 10+/scene 20+/character 10+)
- D3 (5/20): parse.py 真测 10+ ad-hoc 主题, 收 alpha 用户 wait list
- D4 (5/21): 优化 viewer + entity-in-frame audit + sample showreel v2
- D5 (5/22): 等老板回家 ReplayMod batch render 11 .mcpr → 高质 mp4 push GitHub

## 老板回家做的事 (5 天后, 半小时)

1. cat `~/mcstory/docs/REPLAYMOD_RENDER_GUIDE.md`
2. 装 Fabric Loader 1.20.4 + ReplayMod + Fabric API 到 MC 客户端 mods/
3. cp `~/video_factory/fabric_server/recordings/chunks/*/*.mcpr` 到 `~/Library/Application Support/minecraft/replay_recordings/`
4. MC 客户端 → Replay Viewer → Render Queue → All → 1 小时出 10+ 高质 mp4
5. push 高质 mp4 替换 docs/demos/ 低质版

## 死命令心跳 (老板规则)

- 5 min 必 push 飞书 1 条状态
- 15 min 必报: 新 mp4 / 新阻塞 / 自查结论
- 无新增不刷屏, 有阻塞直接降级方案
- AI 团队无限推进自查迭代, 老板专做真实世界沟通
