# B 组三题对照 (赵雪/周朗 02:52-02:54 verdict)

| 题 | RCON | block_types | ground | proportion | detail | 状态 |
|---|---|---|---|---|---|---|
| 小屋 cottage_v1 | 237/237 100% | 9 | PASS | PASS 1.22 | PASS | INGESTED |
| 城堡 castle_v2_modules | 1333/1339 99.5% | 10 | PASS (gate1 v2) | PASS 0.71 | PASS | INGESTED |
| 矿洞 mine_v1 | 235/332 70.8% | 13 | PASS | PASS 0.35 | PASS | INGESTED |

## 失败样本 (verdict 要求)

| 题 | 失败样本 | 重跑参数 |
|---|---|---|
| cottage | 老 v0: 4 墙无屋顶 — single layer | spruce 屋顶 2 坡 + oak_stairs 屋檐 + 烟囱 |
| castle | 老 v1: 84 cmds, 无垫平 → 沉地 5 块 | gate1 v2 footprint 外探测 + 垫平规则 5 点采样 + 外扩 3 格 grass platform |
| mine | 老 v0: 无矿石 + 单 cobblestone | 5 种 ore + 木支撑 + redstone_torch + rail + diamond/emerald 末端宝藏 |

## 类别覆盖

B 组 (量产验证 — 周朗 01:50:05 排序): cottage + castle + mine ✅ 3/3
