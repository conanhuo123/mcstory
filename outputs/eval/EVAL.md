# 评分表 (验证页) — 2026-05-19 11:48

| 截图 | 取景完整 | 细节可辨 | 轮廓脱方块 | 修复动作 |
|---|---|---|---|---|
| bust_v2_FULL_45deg.png | PASS | PASS | FAIL_TOO_BIG_OR_SMALL | 调高 cam 高度 +2 块 (obj_ratio=0.993) |
| bust_v2_FULL_front.png | PASS | PASS | FAIL_TOO_BIG_OR_SMALL | 调高 cam 高度 +2 块 (obj_ratio=0.994) |
| castle_FULL_45deg.png | PASS | PASS | FAIL_TOO_BIG_OR_SMALL | 调高 cam 高度 +2 块 (obj_ratio=0.879) |
| castle_FULL_front.png | PASS | PASS | FAIL_TOO_BIG_OR_SMALL | 调高 cam 高度 +2 块 (obj_ratio=0.911) |
| gundam_v1_FULL_45deg.png | PASS | PASS | FAIL_TOO_BIG_OR_SMALL | 调高 cam 高度 +2 块 (obj_ratio=0.94) |
| gundam_v1_FULL_front.png | PASS | PASS | FAIL_TOO_BIG_OR_SMALL | 调高 cam 高度 +2 块 (obj_ratio=0.887) |

## 三项提升点 / 仍缺点

### 高达 v1 (40 cmds, 简单参数化)
- 提升点: 真 MC RCON 搭建, 蓝lapis胸+白quartz腿+黄V天线, 12块高
- 仍缺点: 单层装甲, 无 V-fin 细节, 无武器挂载结构

### 胸像 v2 (263 cmds, voxel DSL + mirror 镜像)
- 提升点: 6.5x cmds 升级, 分层装甲 (主装甲+装饰+散热口), 镜像对称双肩 3x3, V-fin 3层, 双眼亮 glowstone, 颈环 deepslate
- 仍缺点: 只有上半身 (bust ≠ full body, 缺腿), cam framing 还未在 frame_audit 自动调整

### 城堡 (84 cmds)
- 提升点: 4角塔+旗杆+主门+城垛+窗户; 3 palette 切换 (medieval_gray/sandstone/dark_brick)
- 仍缺点: 室内空 (无家具/楼梯/王座), 塔顶过简 (无尖顶/瓦片纹理)

## 下一步技术升级 (按苏白/周朗 11:44 verdict)

1. mecha_full_body: 用 voxel_tech_lib.Rig humanoid + Proportions.gundam_7head 生成 24 块高全身
2. frame_audit 整合: 截图后自动验, FAIL 触发 cam 重定位 retry
3. 关节连接: 用 Joint.ball 连接 shoulder/elbow/hip/knee, 让 mech 视觉脱'方块拼接感'
