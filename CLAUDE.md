# mcstory — 一句话 → MC 可执行短片 系统

## 项目目标

用户一句中文 → mcstory 自动: 解析剧本 → 建场景 → 配角色 → 编动作 → 拍镜头 → 出 mp4.

5 关链路:
1. **静态模型** ✅ (NLP→DSL 已通)
2. **角色** ✅ humanoid v2 + mc 自带 mob 混合
3. **动作** ⚠️ (ArmorStand pose + mob AI 编排, 部分)
4. **镜头** ✅ headless 截图 cam bug 已修 (physicsEnabled=false + emit move); ReplayMod 高质量 render 作 fallback (老板 Mojang 通了)
5. **导出** ✅ (puppeteer + ffmpeg)

## 工作目录

- 主项目: `/Users/coco/mcstory/`
- 关联视频项目: `/Users/coco/video_factory/` (paper server + 共享 paper world data)
- paper server: 跑在 video_factory/mc_server, RCON `127.0.0.1:25575` pass `mcstory123`, online-mode=false, enforce-secure-profile=false

## 关键工具栈

### Python (.venv/bin/python)
- `scripts/voxel_dsl.py` — VoxelBuilder (mirror_axis, set/box/sphere/line, auto_framing, FrameAudit)
- `scripts/voxel_tech_lib.py` — Rig + Proportions + Joint + MountPoint (含 monkey_staff/web_shooter/spear/magic_orb 武器)
- `scripts/module_library.py` — Foundation/Body/Decor/Framing 4 类 21+ module
- `scripts/building_dsl.py` — Reference (louvre/temple/skyscraper preset) + ProportionFrame + StructureTemplate
- `scripts/quality_gate.py` — 5 闸 (gate1 ground v2 footprint 外探 + gate2 framing + gate3 proportion + gate4 detail + gate5 multiview)
- `scripts/gate67_semantic_outline.py` — Semantic palette + 主体轮廓 cluster
- `scripts/character_action_gate.py` — 角色+动作 5 闸 (spawn/placement/pose/animation/visible_change)
- `scripts/nlp_to_building.py` — **L2 一句话→GPT-5.5 spec→voxel_dsl 真建** (+ 垫平规则)
- `scripts/nlp_to_character.py` — v1 humanoid 22 高
- `scripts/nlp_to_character_v2.py` — **v2 35 高 + 面部五官 + 胸前 emblem + cape + 武器 v2 + pose**
- `scripts/structure_lookup.py` — **L1.1 mc 内置 50+ structure NLP→/place structure**
- `scripts/nbt_importer.py` — **L1.2 minecolonies 598 nbt 库 import+route+place**
- `scripts/battle_animator.py` — 角色 pose 循环切换 (旧版)
- `scripts/batch_nlp_v1.py` / `batch_nlp_v2.py` — batch 量产 pipeline
- `scripts/parse.py` — Azure GPT-5.5 一句话→30s 剧本 JSON (4 拍式: 3+15+8+4)
- `scripts/cli.py` — 旧 mcstory 入口
- `scripts/cli_build_gated.py` — build + 5 闸 + retry 完整 pipeline

### Node (puppeteer + mineflayer + prismarine-viewer)
- `scripts/gate1_screenshot.js` — mineflayer cam + prismarine-viewer + puppeteer 截图 (cam bug 待修)

### MCP Server (mcp_server/mcstory_server.py)
- 5 tool: `generate_scene` / `audit_quality` / `run_rcon` / `screenshot` / `scene_library_query`
- `.mcp.json` 项目级配置, .venv 隔离
- 启动需 claude 重启 + 进 mcstory 目录

## NLP→建筑 4 层架构 (老板"产品级"路径)

| 层 | 用什么 | 触发场景 | 实施状态 |
|---|---|---|---|
| **L1.1** | mc 内置 50+ structure | 标准结构 (mansion/金字塔/村庄) | ✅ structure_lookup.py |
| **L1.2** | minecolonies 598 .nbt (paper world/generated) | 中世纪村庄精模 | ✅ nbt_importer.py (505 已 import) |
| **L1.3** | puppeteer scrape minecraft-schematics | 长尾 (Cloudflare 阻 curl) | ❌ 待做 (chrome-devtools-mcp 已装) |
| **L2** | voxel_dsl + module_library + NLP→spec | 半结构 (中式塔/科幻) | ✅ nlp_to_building.py |
| **L3** | humanoid rig + palette + weapon | 角色 (孙悟空/蛛侠) | ✅ nlp_to_character_v2.py |
| **L4** | GPT-5.5 freestyle voxel | 极端长尾 | ❌ 待做 |

## scene_library v0.17 (40+ examples 增长中)
- 路径: `schema/scene_library.schema.json`
- 含: 锁版 10 题 (5 类×2: 地标/机甲/B 量产/室内/幻想/自然) + batch_v1 10 题 + batch_v2 v2 重跑

## paper world 已 placed 重要建筑/角色

| 区域 | 内容 |
|---|---|
| z=-300 | 老希腊神庙/唐塔/摩天楼 (NLP→building 首批) |
| z=-450 | batch_v1 10 题跨文化跨风格 (-800→-350) |
| z=-650 | batch_v2 v2 改进版 9 题 |
| z=-800 | 孙悟空 vs 蛛侠 v1/v2 (humanoid demo) |
| z=-1000 | minecolonies 11 真精模 (6 style townhall+barracks) |
| z=-300 区 | mc 内置 4 Mojang 精模 (-1100→-1500 mansion/desert_pyramid/jungle_pyramid/end_city) |
| -1500 | 紫禁城 + 哥斯拉(ender_dragon)+ 金刚(iron_golem) 大战场 |

## openclaw 协作 (老板"合作"铁律)

- openclaw 12 GPT-5.5 agents (沈砚/苏白/陆远/叶迟/周朗/陈砺/季野/林凡/谢宁/赵雪/何初 + 韩沂)
- 现状: GPT 评论员, 无真 tool — 我 (Claude) 工程实施
- 路径: mcstory MCP server 已建 (5 tool), 老板 openclaw 接 MCP 仍需开发
- 退化方案: openclaw GPT 在飞书发指令, 我接 → 执行 → 飞书回报 (现在的模式)
- 飞书: `oc_5c1346eee378f711a40f069eec8c2ddf` (主群)

## 命令快速参考

```bash
# 一句话建筑 (L2)
.venv/bin/python scripts/nlp_to_building.py "建一座中世纪法国哥特教堂" -800 80 -550

# 一句话角色 v2 (L3)
.venv/bin/python scripts/nlp_to_character_v2.py "孙悟空, 金箍棒高举" -600 80 -900

# mc 内置 structure (L1.1)
.venv/bin/python scripts/structure_lookup.py "建一座林地豪宅" -1100 100 -300

# minecolonies nbt (L1.2)
.venv/bin/python scripts/nbt_importer.py place darkoak_townhall_townhall5 -800 80 -1000

# batch 量产 10 题
.venv/bin/python scripts/batch_nlp_v2.py

# RCON 任意命令
.venv/bin/python -c "from mcrcon import MCRcon
with MCRcon('127.0.0.1','mcstory123',port=25575) as r: print(r.command('list'))"

# 飞书 send
/opt/homebrew/bin/openclaw message send --channel feishu --account hanyi --target oc_5c1346eee378f711a40f069eec8c2ddf -m "..."
```

## 已知未解决问题 (优先级)

1. ~~**prismarine-viewer cam bug**~~ ✅ 已修 (2026-05-24): 双根因 — (A) mineflayer 本地物理给相机 bot 施加重力, server spectator 拦不住本地 entity.position 下坠, viewer 读的就是它 → 相机坠地拍草地; (B) prismarine-viewer 相机只在 bot 'move' 事件经 botPosition() 推 'position'(pos/yaw/pitch), puppeteer 连上后 bot 静止 → 相机停默认朝向. 修法: gate1_screenshot.js 加 `physicsEnabled=false`+钉死坐标 + 连上后 `emit('move')` 重推. 验证: 对夹具截图建筑清晰入画 (outputs/gate1_verify_*.png). 探针: scripts/cambug_probe.js / cambug_fix_test.js
2. **gate1 ground NLP 流水线** — batch 偶尔 PARTIAL, 需垫平规则更稳
3. **outputs/nlp_*.json 命名 overlap** — id 不带时间戳重建覆盖
4. **5 关链路真 mp4 端到端没跑过** — 关 5 puppeteer 通了但无声
5. **角色库稀** — 5 原型 (古装文人/武将/动物/...) 没做
6. **动作库稀** — pose 7 类, 实测 2 个

## 心跳模式 SOP

- 老板 30min 静默心跳: `ScheduleWakeup` 续, 只在过关/硬阻塞 push 飞书
- monitor v2 后台轮询 (`scripts/client_window_monitor_v2.sh`)
- 默认 wakeup 间隔 1800s
- 老板 ping = 测桥 + 测我活, 简短回报

## 老板沟通铁律 (memory feedback)

- 全流程无需老板确认, 直接自主完成导出
- Claude+OpenClaw 无限推进自查迭代
- 老板专做真实世界沟通 (customer dev / 融资 / GUI)
- 老板 mc 客户端: `mcstory-fabric-1.20.4` (Fabric 1.20.4), 玩家名 `conanhuo`
- 飞书消息: openclaw 转发, 老板=Claude, 下属=openclaw

## 字符标识

- §6§l 金色加粗 (boss)
- §c§l 红色加粗 (敌对)
- §2§l 绿色 (友军 / 哥斯拉)
- §8§l 黑色 (金刚 / 暗系)
- §a§l 浅绿 (成功)
- §e 黄 (提示)

## 测试坐标

paper world 空 chunk 区: x ∈ [-2000, -100], z ∈ [-2000, -100], y ≈ 70-100 真实地形
