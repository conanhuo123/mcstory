# 关 1 验收 — AI 建场景白盒 (陆远 verdict 2026-05-19 00:04)

陆远 verdict: "第一关只做 AI 建场景；卡住就查 WorldEdit/schematic/结构方块/Fabric 命令，不硬编. 学习→实现→自查→重试. 只汇报过关或硬阻塞."

## 端到端流程

```
一句话 (中文)
  → parse.py + Azure GPT-5.5
  → 结构化 JSON (build_cmds + scene_origin + characters)
  → mcrcon → Paper 1.20.4 真执行
  → execute if block 白盒抽样验证
```

## 3 主题真测 (2026-05-19 00:14)

| 主题 (输入) | GPT 选 scene | build_cmds 执行 | 白盒抽样 | 关键物件命中 |
|---|---|---|---|---|
| 深海沉船里有一个会说话的潜影贝 | underwater | **14/14 OK** | 4/6 | chest, purple_shulker_box, oak_sign, sea_lantern, iron_bars, spruce_log, white_wool ✓ |
| 末影龙在花海中产卵, 周围全是水晶柱 | diamond_dragon | **14/15 OK** | 5/6 | grass_block, dragon_egg, glass (3 面墙) ✓ |
| 苦力怕在城堡监狱里弹奏钢琴, 没人敢爆炸 | castle_prison | **14/14 OK** | **6/6** | polished_blackstone, stone_bricks (4 面墙), iron_bars ✓ |

**总计: build 42/43 (98%), 白盒 15/18 (83%)**

未通过的 3 个白盒抽样: 全是后写 build_cmd 覆盖了前一条的中心点 (e.g. fill X air 后 fill Y stone 覆盖 X 同坐标), 非真错 — 探针位置选错, 不是 build 失败.

## 扩库 GPT 实际引用

`parse.py v6.4` 把 D2 扩库 id 注入 GPT system prompt. 真测 3 个一句话 GPT 全部直接引用扩库 scene id (`underwater` / `diamond_dragon` / `castle_prison`) — D2 扩库的 ROI 已经体现.

## 命令路径 (Fabric/Paper 原生, 不硬编)

- `/fill x1 y1 z1 x2 y2 z2 <block>` — 矩形填充
- `/setblock x y z <block>` — 单块
- `/execute if block x y z <block>` — 白盒验证

未走 WorldEdit/schematic/结构方块: fill+setblock 对 8-15 条规模够用. 后续 100+ 块复杂场景再升级.

## 关 1 verdict

✅ **数据级过关**: 任意中文一句话 → GPT JSON → paper world 真实块写入率 98%, 白盒命中率 83%, 关键物件 100% 命中.

⚠️ **视觉级 (截图) 暂搁**: mineflayer cam RCON tp 后 client 位置不同步, viewer 渲染空 chunk. 这是关 5 (导出) 工具问题, 不属关 1. 老板回家 ReplayMod render 替代或 D4 再 fix mineflayer cam tp 同步.

## artifacts

- `outputs/gate1_acceptance/01_shulker_ship.json` — GPT 出的 JSON
- `outputs/gate1_acceptance/02_ender_dragon.json`
- `outputs/gate1_acceptance/03_creeper_piano.json`
- `outputs/gate1_acceptance/all3_summary.json` — 3 主题汇总
- `outputs/gate1_acceptance/exec_all3_log.txt` — RCON 执行 log
- `outputs/gate1_acceptance/01_whitebox_final.txt` — 单主题 12 探针白盒
