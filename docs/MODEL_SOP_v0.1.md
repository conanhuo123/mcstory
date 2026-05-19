# Model SOP v0.1 — 静态模型生产流程

(陆远 17:24 + 赵雪 17:58 verdict 沉淀)

## 5 阶段 pipeline

```
一句话 (用户)
   ↓
① 生成 (StaticEngine.build_from_spec)
   - Reference 拆解: 真实尺寸 lookup (135x27x65m 等)
   - ProportionFrame: 1 块 = 1m 框架
   - ModuleLibrary 组合: 地基/主体/装饰/取景 4 类 19 modules
   - palette 材质分层: main/trim/deco/pillar/roof/floor/centerpiece/accent
   ↓
② 评分 (quality_gate.run_full_audit)
   闸 1 ground_check     — build_bottom 距 paper 真地面 ≤ 2 块
   闸 2 framing          — cluster bbox 4 边 padding ≥ 5% (25px @ 1280w)
   闸 3 proportion       — bbox h/w in (0.1, 5.0)
   闸 4 detail_density   — block 种类 ≥ 5, 总 cmds ≥ 200
   闸 5 multiview        — 3+ 视图至少 2 PASS framing
   ↓
③ 重跑 (低于阈值 自动调参 retry)
   闸 1 FAIL → origin y = real_ground + 1
   闸 2 FAIL → cam distance + 35%, palette 排 false-positive 色
   闸 3 FAIL → scale 调整
   闸 4 FAIL → 加 modules (decor)
   闸 5 FAIL → 加 cam 角度
   max_retry = 3
   ↓
④ 展示 (PASS 才进)
   截 3 视图 (front + 45deg + top)
   生成 EVAL_MOSAIC.png 评分页
   ↓
⑤ 入库 (scene_library.examples 追加)
   schema/scene_library.schema.json 加 examples
   含 reference/scale/modules/palette/score
```

## 强制规则

1. **不合格不展示**: ① 不过, ② 自动 retry, max_retry 后才标 FAIL 进 ⑤
2. **题库复测**: 每个新 module/template 加入后, 跑 louvre + mecha + castle 3 题, 都需 PASS
3. **真实参考**: Reference 必须有真实数据 source (维基百科 / 官网 / 测量)
4. **截图自检**: 不靠肉眼判, 用 connected-component cluster + padding 5% TOL

## 当前状态 (2026-05-19 18:33)

| 阶段 | 实现 | 状态 |
|---|---|---|
| ① 生成 | StaticEngine + Reference + ProportionFrame + ModuleLibrary (4 类 19 mods) | ✅ |
| ② 评分 | quality_gate.py 5 闸 + cli_build_gated.py 集成 | ✅ |
| ③ 重跑 | origin y retry 已通; cam retry + palette tune 调中 | ⚠️ partial |
| ④ 展示 | 三视图 + EVAL_MOSAIC | ✅ |
| ⑤ 入库 | scene_library v0.2 已含 4 mecha; louvre/castle 入库待 ② 全 PASS | ⚠️ blocked |

## 复测题库

| 题 | 现状 | 闸 1 ground | 闸 2 framing | 闸 3 prop | 闸 4 detail | 闸 5 multi |
|---|---|---|---|---|---|---|
| 卢浮宫 (3791 cmds) | v2 retry @ y=94 | ✅ | ⚠️ algo 抓地板 | ✅ | ✅ | ⚠️ |
| 高达 v1 (40 cmds) | @ -100,80,-300 | ⚠️ 浮空 16 | ❌ | ✅ | ⚠️ <200 | ❌ |
| 高达胸像 v2 (263) | @ -130,80,-300 | ⚠️ 浮空 | ⚠️ | ✅ | ✅ | ⚠️ |
| 高达 humanoid v3 (528) | @ -100,80,-340 | ❌ ocean | — | ✅ | ✅ | — |
| 城堡 (84 cmds) | @ -80,80,-260 | ⚠️ 浮空 | ⚠️ | ✅ | ❌ <5 types | ⚠️ |

## 下一跳 (按 verdict)

补 ② framing/multiview FAIL→PASS, 然后跑 ⑤ 入库.
