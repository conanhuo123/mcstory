# MC 短剧 15s POC 录制链路 v0.1

时间: 2026-05-18 01:28
状态: Day 4 端到端验证完成, 接下来串录像 → 出 mp4 链接

## 已验证 (✓)
1. `parse.py` 一句话 → GPT-5.5 5 镜头剧本 JSON
2. `translate.py` 剧本 JSON → 23 timeline 事件
3. `record.py` timeline → mineflayer bot.js + server_cmds.txt
4. **Paper 1.20.4** 本机服 (port 25565, online_mode=false) 启动 1.9s
5. **mineflayer bot** 自动连服 + 按时序触发 /tellraw (server log 时间戳精确到秒)
   - 实测: steve_director 18s 内顺序喊出 5 句《判死刑》台词, 干净退出

## 待办 (Day 5)
1. **录屏方案 (3 选 1)**
   - A: macOS `ffmpeg avfoundation` 录全屏 (需 MC 客户端开着+ alt-tab)
   - B: **ReplayMod** (MC 客户端 mod, 服内 tick-perfect 重放; 可不开客户端纯服端录像)
   - C: `prismarine-viewer` 起 headless 浏览器 + Puppeteer 录 canvas
   - **当前推荐 B** — 服端可控, 不依赖客户端窗口, 输出 .mcpr 再 export mp4
2. **多 bot 同步** — 当前单 bot (steve_director 喊话) ok; 多 bot (steve+villager+iron_golem 演) 卡在 Paper connection-throttle. record.py 已加 6s 错开 + 50s hard timeout, 待重测
3. **postprod 拼接** — 录屏 mp4 + timeline → 烧字幕 + 火山 TTS 配音 + BGM. `postprod.py` 已落, 待接录屏
4. **可点链接** — 走 ~/video_factory/scripts/auto_deliver.py 自动百度网盘归档 + 飞书直传 (整套已用过, 直接复用)

## 验收口径 (按沈砚/苏白/林凡 2026-05-18 verdict)
- 15s 内观众能否倒推出"胖橘法官判死刑"剧本 → 倒推不出 = 工具链失败
- death_sentence.json 6 字段: scene/characters/action/camera/subtitle/twist_visual
- 红线: 不加群众、不加支线、每句 ≤12 字
- twist_visual 只在第 5 镜头出现, 旧牌显名必须入画 (不靠字幕解释)

## 文件清单
```
~/mcstory/
├── scripts/{parse,translate,record,postprod,cli}.py    ✓
├── templates/scenes/scenes.json v0.2 (4 场景含红石门)   ✓
├── templates/characters/characters.json                ✓
├── templates/cameras/cameras.json (5 镜头预设)         ✓
├── templates/scripts/judge_death.json                  ✓
├── samples/death_sentence.json (5 shot 全字段)         ✓
├── docs/poc_15s_plan.md (本文档)                       ✓
└── outputs/judge_death_timeline.json + bot.js          ✓
```

## 下一里程碑 (Day 5-6)
- D5: ReplayMod 录像 → 出原始 30s mp4
- D5: postprod 接入 → 出 15s 字幕配音终片
- D6: auto_deliver → 飞书可点链接 → 收 5 个海外测试者
