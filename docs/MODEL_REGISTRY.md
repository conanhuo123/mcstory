# Model Registry (静态模型库注册表) v1.0
2026-05-19 22:35 — louvre + mecha + castle 3 模板入库

## 题库复测结果

| Template ID | RCON | block_types | ground | framing | proportion | detail | multiview | Status |
|---|---|---|---|---|---|---|---|---|
| louvre_v2_retry | 3563/3791 | 16 | PASS | PASS | PASS | PASS | PASS | INGESTED |
| mecha_humanoid_v3 | 528/528 | 15 | PASS | PASS | PASS | PASS | PASS | INGESTED |
| castle_v2_modules | 1331/1339 | 10 | PARTIAL (paper 地形波动) | PASS | PASS | PASS | PASS | INGESTED_PARTIAL_GROUND |


## 入库字段 (每个模板)

每 `outputs/model_registry/{id}_entry.json` 含:
- template_id / template_script / reference
- replay_cmd (可复测入口)
- quality_gate (5 闸 PASS/FAIL)
- pass_screenshots[] (通过图)
- fail_screenshots[] (失败图)
- retry_params (调参记录)
- improvement_notes[] (仍需提升点)
- baidu_pan (百度网盘路径)
- scene_library_id (scene_library.json 引用)
- commits[] (git commit hash 链)
- status (INGESTED / INGESTED_PARTIAL)

## 可复测入口

```bash
# louvre
python3 scripts/louvre.py
# mecha
python3 scripts/mecha_humanoid_v3.py
# castle (modules combination)
python3 scripts/module_library.py + 组合 in build_castle script
```

## SOP 验证

3 模板均经过完整 SOP 5 阶段:
① 生成 (building_dsl / voxel_dsl / module_library)
② 评分 (quality_gate 5 闸)
③ 重跑 (origin y + cam tune + palette filter)
④ 展示 (EVAL_MOSAIC + 仍需提升点)
⑤ 入库 (本表 + scene_library.json + 百度网盘)

louvre 5/5 PASS, mecha 5/5 PASS, castle 4/5 PASS (ground PARTIAL).

## 下一题候选

- 寺庙 (temple, Reference 已有)
- 摩天楼 (skyscraper, Reference 已有)
- 末影龙基地 (混合 mecha + 末地建筑)
