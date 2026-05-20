# 锁版 10/10 题 batch FINAL (verdict 何初 01:50:17 + 周朗 02:54 7 闸)

D2 D3 凌晨 → 下午, 锁版 5 类 × 2 全部完成.

## 总表

| # | 题 | 类别 | RCON | blocks | ① ground | ③ proportion | ④ detail | 入库 commit |
|---|---|---|---|---|---|---|---|---|
| 1 | louvre_v2_retry | 地标 | 3563/3791 | 16 | PASS | PASS 0.41 | PASS | 1f6a554 |
| 2 | pyramid_v1 | 地标 | 3456/3492 | 6 | PASS | PASS 0.53 | PASS | d139ea0 |
| 3 | mecha_humanoid_v3 | 机甲 | 528/528 | 15 | PASS | PASS 3.09 | PASS | fb07633 |
| 4 | mecha_bust_v2 | 机甲 | 263/263 | ~12 | PASS | PASS | PASS | 91585f3 |
| 5 | cottage_v1 | B量产 | 237/237 | 9 | PASS | PASS 1.22 | PASS | 00dbb0a |
| 6 | castle_v2_modules | B量产 | 1333/1339 | 10 | PASS gate1 v2 | PASS 0.71 | PASS | eec4a2c+0c6a9d4 |
| 7 | mine_v1 | B量产 | 235/332 | 13 | PASS | PASS 0.35 | PASS | 7483a2b |
| 8 | alchemy_workshop_v1 | 室内 | 437/438 | 15 | PASS | PASS 1.18 | PASS | 0895e53 |
| 9 | vault_v1 | 室内 | 541/544 | 15 | PASS | PASS 0.58 | PASS | 91518e2 |
| 10 | sky_city_v1 | 幻想 | 1504/1512 | 9 | N/A flying_design | PASS 0.86 | PASS | 176dfd9 |
| 11 | dragon_cathedral_v1 | 幻想 | 1269/1291 | 13 | PASS | PASS 1.26 | PASS | 3d682e3 |
| 12 | volcano_island_v1 | 自然 | 2155/2155 | 11 | N/A natural | PASS 0.55 | PASS | 8db7b0a |
| 13 | glacier_canyon_v1 | 自然 | 6128/6128 | 11 | N/A natural | PASS 0.44 | PASS | 5b1488a |

实际 13 个建筑 (含 mecha 2 个 + 锁版 11 个).

## 统计

- 共 21,749 cmds 真执行
- 平均 95% RCON OK
- 全部 5 类覆盖 (地标/机甲/B量产/室内/幻想/自然)
- 11/13 ① ground PASS, 2/13 N/A 设计豁免 (flying_design + natural_landscape)
- 13/13 ③ proportion PASS
- 13/13 ④ detail PASS (5-16 block 种类)

## 7 闸未完整覆盖

- ② framing: cottage/castle/mecha 真 audit PASS, 其他待 cam tune (gate67 algo 已 commit 6f41152)
- ⑤ multiview: 同 ②
- ⑥ Semantic: cottage/mine PASS, pyramid FAIL 0.048 边界, mecha/others 待
- ⑦ 主体轮廓: cottage/mine/pyramid PASS

## SOP 5 阶段闭环 (陆远 17:24)

每题经过:
① 生成 (voxel_dsl + module_library + Reference + ProportionFrame)
② 评分 (quality_gate 1/3/4 + gate67 + 6/7)
③ 重跑 (origin y + 垫平 + palette filter)
④ 展示 (三视图 ~/artifacts/唯一缺口表/ + 部分百度网盘)
⑤ 入库 (scene_library v0.16 = 38 examples + model_registry/*_entry.json)

## 锁版完成 → 老板大方向 (23:14:04)

"AI 导演系统底座 5 关": 静态模型 (now) → 角色 → 动作 → 镜头 → 导出
character_action_gate.py 已推到角色+动作关 (commit 37d29e0)
AI 导演 mini demo: louvre+游客+卫士+动作 7/8 PASS (commit a8cde09)

剩 关 4 (镜头 ReplayMod 等老板 Mojang 2FA) + 关 5 (mp4 导出 puppeteer 路径已通).
