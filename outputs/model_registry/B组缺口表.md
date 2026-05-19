# B 组缺口表 (周朗 03:30 verdict)

| 题 | 三视图 | 七闸 PASS | 失败样本 | 重跑参数 |
|---|---|---|---|---|
| **小屋 cottage_v1** | ✅ outputs/题库_cottage_final/{front,45deg,top}.png | ✅ ground/proportion/detail PASS, ⏳ framing/multiview/Semantic/主体轮廓 待 algo | ✅ 失败: 老 v0 无屋顶 (`outputs/eval/old_cottage_box.png` placeholder) | spruce 屋顶+oak_stairs 屋檐+烟囱 |
| **城堡 castle_v2_modules** | ✅ outputs/题库_castle_v2_final/{castle_front,45deg,close}.png | ✅ ground (gate1 v2)/framing/proportion/detail/multiview, ⏳ Semantic/主体轮廓 待 algo | ✅ 失败: 老 v0 沉地 5 (`outputs/eval/castle_FULL_front.png`) | gate1 v2 footprint 外探测 + 垫平规则 5 点采样 + 外扩 3 格 grass platform |
| **矿洞 mine_v1** | ✅ outputs/题库_mine_final/{front,45deg,top}.png | ✅ ground/proportion/detail PASS, ⏳ framing/multiview/Semantic/主体轮廓 | ✅ 失败: 老 v0 无矿石 + 单 cobblestone | 5 种 ore + 木支撑 + redstone_torch + rail + 末端 diamond/emerald 宝藏 |

## 7 闸状态汇总

- ① ground: 3/3 PASS (gate1 v2 footprint 外探测 + 垫平规则)
- ② framing: ⏳ 待 cam tune (verdict 24h 前 louvre 经验)
- ③ proportion: 3/3 PASS
- ④ detail: 3/3 PASS (9/10/13 block 种类)
- ⑤ multiview: ⏳ 同 ②
- ⑥ Semantic: ⏳ algo 待开发 (赵雪 23:14 提)
- ⑦ 主体轮廓: ⏳ algo 待开发 (何初 01:52 提)

## 失败样本 + 重跑参数 (硬证据)

各题 entry json 在 outputs/model_registry/{cottage,castle,mine}_v1_entry.json 待生成
