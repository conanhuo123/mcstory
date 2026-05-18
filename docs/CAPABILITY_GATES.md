# mcstory 5 关能力清单 (陆远 22:12 拍板)

按底层能力拆解, 不再用"成片"掩盖能力缺口. 5 关逐个过, 每关单独 demo + audit.

## 关 1 — AI 建场景 (Build) ✅ PASS (v5.0, 22:17)

**能力**: 一句话 → GPT-5.5 输出 build_cmds (fill/setblock 序列) → MC server 真执行

**Demo**: `outputs/adhoc_20260518-221330/`
- 输入: "末影龙在火山口产卵, 小末影龙破壳追逐玩家"
- GPT 生成 13 条 build_cmds:
  ```
  fill -68 79 -198 -52 79 -182 minecraft:basalt
  fill -66 80 -196 -54 82 -184 minecraft:blackstone
  fill -63 80 -193 -57 80 -187 minecraft:lava
  fill -62 81 -192 -58 81 -188 minecraft:magma_block
  fill -61 82 -191 -59 82 -189 minecraft:obsidian
  setblock -60 83 -190 minecraft:dragon_egg
  ...
  ```
- 实际执行: paper log 全 "Successfully filled" + "Changed block at"

**自检 PASS 标准**: 任意一句话 → GPT 输出 ≥5 条有效 fill/setblock + 全部 execute success

## 关 2 — 放角色 (Spawn) ✅ PASS

**能力**: GPT 输出 characters list → cli_full /summon 到 build 旁 (origin+5z) → viewer 可见

**Demo**: stage3_trio 帧 — 看到 iron_golem 完整身体 + villager
- summon cmds: `/summon villager -55 80 -174 {NoAI:1b,Silent:1b,...}`
- cmd 后 paper log "Summoned new Villager"
- viewer frame 验证 entity 在画面 (左下角 villager 头 / 中央 iron_golem)

**自检 PASS 标准**: GPT 输出 N 角色 → summon N 个 entity → viewer 至少 1 个 visible

## 关 3 — 控动作 (Action) ✅ PASS

**能力**: GPT 输出 shot actions → cli_full 翻成 /tp /effect 命令 → MC entity 响应

**Demo**: stage3_trio timeline
- 3s villager 走台中央: `/tp @e[type=villager,...] {origin} {origin+0} {origin+0}`
- 6s villager 抬头: `/tp ... 0 -30` (yaw=0 pitch=-30)
- 9s villager glowing: `/effect give @e[type=villager,...] glowing 5 0 true`
- 12s setblock 反转牌
- paper log 全 success

**自检 PASS 标准**: 每 shot 至少 1 个 action → server 执行 → 帧间状态可比 (但 motion 阈值难)

## 关 4 — 控镜头 (Camera) ⚠️ PARTIAL

**能力**: GPT 输出 camera type → cli_full tp camera bot → viewer firstPerson 跟随

**Demo**: stage3 cam @ (-49,82,-171), yaw=143 pitch=17 look at characters

**未通过**:
- ❌ 多镜头切换 viewer drift (上游 prismarine-viewer #477)
- ❌ Production-quality camera path (smooth pan/zoom) 需 ReplayMod
- ✅ 单 fixed camera 视角对 character 可见

**自检 PASS 标准**: 5 shot 5 个 camera position 全 visible + 镜头切换无 chunk reload race

**真正解**: Production tier (ReplayMod 客户端 GUI render), 5 天后老板回家 1 次操作

## 关 5 — 导出视频 (Export) ✅ PASS

**能力**: viewer 渲染 + puppeteer 录 + ffmpeg 烧字幕 + 火山 TTS 配音 + mov_text → final.mp4

**Demo**: 任意 outputs/*/final.mp4 (50+MB 真 MC 画面 + 字幕 + 配音)
- 125+ mp4 已生成
- audit_v2 motion+luma 双指标
- auto_deliver 飞书+网盘归档

**自检 PASS 标准**: cli_full 一行 → final.mp4 + QC pass (1080×1920 / 15s / 字幕)

---

## 当前关卡得分

| 关 | 能力 | 状态 | 卡点 |
|---|---|---|---|
| 1 | AI 建场景 | ✅ PASS | 无 |
| 2 | 放角色 | ✅ PASS | 无 |
| 3 | 控动作 | ✅ PASS | 无 |
| 4 | 控镜头 | ⚠️ 50% | 多镜头切换需 ReplayMod |
| 5 | 导出视频 | ✅ PASS | 无 |

**4/5 关 PASS**. 第 4 关 prototype tier 50% (单镜头 visible, 多镜头切换需 user GUI Production tier).

## 接下来按关推进

- **D2 明天**: 关 1 增强 (GPT 生成更多样化 scene, fill_cmds < 100 块限制内), 关 2 增强 (action library 扩 villager 走/挥手/坐下)
- **D3**: 关 3 增强 (timeline 翻 7-9 action 不止 3 个)
- **D4-5**: 关 4 fix prototype 视角 + 关 5 升级 audit v3 (entity-in-frame 检测)
- **5 天后**: 老板回家做关 4 Production tier (ReplayMod batch render)
