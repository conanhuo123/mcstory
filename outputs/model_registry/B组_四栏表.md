# B 组 四栏表 (verdict 04:07-04:08 真路径)

| 题 | 三视图路径 | 七闸 | 失败样本 | 重跑参数 |
|---|---|---|---|---|
| **小屋 cottage_v1** | `~/artifacts/B组_三视图/cottage_{front,45deg,top}.png` | ① ground PASS ② framing 待 ③ proportion PASS h/w 1.22 ④ detail PASS 9 blocks ⑤ multiview 待 ⑥ Semantic 待 algo ⑦ 主体轮廓 待 algo | 老 v0 无屋顶 (placeholder) | spruce 双坡屋顶 + oak_stairs 屋檐 + cobblestone 烟囱 + campfire + lantern 内灯 |
| **城堡 castle_v2_modules** | `~/artifacts/B组_三视图/castle_{front,45deg,close}.png` | ① ground PASS (gate1 v2 footprint 外 actual=90, build=90) ② framing 3/3 PASS (commit eec4a2c) ③ proportion PASS h/w 0.71 ④ detail PASS 10 blocks ⑤ multiview PASS 3/3 ⑥ Semantic 待 ⑦ 主体轮廓 待 | 老 v0 沉地 5 块 `outputs/eval/castle_FULL_front.png` | gate1 v2 + 垫平规则 (5 点采样 + 外扩 3 格 grass platform + build_bottom=target+1) |
| **矿洞 mine_v1** | `~/artifacts/B组_三视图/mine_{front,45deg,top}.png` | ① ground PASS ② framing 待 ③ proportion PASS h/w 0.35 ④ detail PASS 13 blocks ⑤ multiview 待 ⑥ Semantic 待 ⑦ 主体轮廓 待 | 老 v0 无矿石 (placeholder) | 5 种 ore (coal/iron/diamond/emerald/gold) + 木支撑 + redstone_torch + rail + 拱门 + 末端宝藏 |

## 闸 ⑥⑦ algo 待开发 (verdict 02:54 周朗):

⑥ Semantic: 用 LLM vision 或 reference image RGB 直方图对比验"是否像 cottage/castle/mine"
⑦ 主体轮廓: 主体 cluster 占画面比例 + 边缘清晰度

algo 凌晨 4 点写不完, 早上推进. 当前 5/7 闸框架已成 (castle), 3/7 PASS (cottage/mine 没截图后跑 gate 2/5).
