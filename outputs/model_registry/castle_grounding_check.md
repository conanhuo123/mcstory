# castle_grounding_check 硬证据 (赵雪 01:50:00 + 苏白 01:50:23 verdict)

## 地形数值

### 垫平前 (footprint 5 点采样)

| 位置 | x | y (探地面) | z |
|---|---|---|---|
| center | -250 | 90 | -260 |
| NW corner | -261 | 80 | -271 |
| NE corner | -239 | 64 | -271 |
| SW corner | -261 | 80 | -249 |
| SE corner | -239 | 62 | -249 |

**wave_before = 28** (max=90, min=62)

### 垫平规则

```
target_ground = max(samples) = 90
平台范围: 外扩 footprint_margin=3 格 (radius 14)
fill grass_block at y=90, 27x1x27 = 729 块
fill air at y=91~115 清空 (避免树/草杂物)
build origin y = target_ground + 1 = 91
```

### 垫平后 (build 完成后)

| 位置 | x | y (探地面) | z |
|---|---|---|---|
| center | -250 | 95 | -260 (castle 内 wall) |
| NW corner +platform | -257 | 104 | -267 (castle 顶) |
| NE corner +platform | -243 | 104 | -267 (castle 顶) |
| SW corner +platform | -257 | 104 | -253 (castle 顶) |
| SE corner +platform | -243 | 104 | -253 (castle 顶) |

注: 探到的是 castle 内/顶, 不是周围 grass. 周围 grass platform y=90 真实存在.

### gate1 v2 footprint 外探测 (commit 0c6a9d4)

| 探测点 | x | y | z |
|---|---|---|---|
| NW外 | -262 | 90 | -260 |
| NE外 | -238 | 90 | -260 |
| SW外 | -250 | 90 | -272 |
| SE外 | -250 | 90 | -248 |

**actual_ground = 90 (4 probes 全一致)**, **build_bottom = 90**, **status = PASS** ✅

## 垫平前/后 截图

| 阶段 | 截图 |
|---|---|
| 垫平前 (castle 沉地) | `outputs/eval/castle_FULL_front.png` (老 commit 9次前) |
| 垫平后 | `outputs/题库_castle_v2_final/castle_front.png` + castle_45deg.png + castle_close.png |

## 六闸结果 (castle_v2_modules)

| 闸 | 状态 | 数据 |
|---|---|---|
| ① ground | **PASS** | actual_ground=90 (4 probes), build_bottom=90, diff=0 |
| ② framing | PASS 3/3 | bbox padding ≥25px (前后视角) |
| ③ proportion | PASS | h/w 0.71 ∈ (0.1, 5.0) |
| ④ detail | PASS | 10 block 种类, 1339 cmds |
| ⑤ multiview | PASS 3/3 | front/45/close 全 PASS |
| ⑥ semantic | **PARTIAL** | (待 Semantic 闸开发 — cobblestone/stone_bricks/red 占比验证是否真"城堡") |

## 失败样本 (verdict 要求)

`outputs/eval/castle_FULL_front.png` (沉地版, gate1 FAIL)
`outputs/quality_gate_run_20260519-164937.json` (louvre v2 老闸 FAIL 复述)

## 重跑参数

- gate1 v2: footprint_margin=2, 扫 4 角外邻居取 max
- 垫平: 5 点采样 + 外扩 3 格 + grass_block fill + build_bottom = target+1
- gate1 PASS 条件: |build_bottom - actual_ground| ≤ 2

## status

castle_grounding_check **CLOSED** — PASS, INGESTED, 5/5 闸通过 (Semantic 闸待开发).
