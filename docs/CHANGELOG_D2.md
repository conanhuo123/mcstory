# D2 CHANGELOG (2026-05-18 / 老板 5/18-5/22 不在家)

D2 主线: 扩 4 库样本 + 让 parse.py 通知 GPT 用上扩库

## 4 库扩样统计

| 库 | D1 baseline | D2 末 | D2 目标 | 达成 |
|---|---|---|---|---|
| action_grammar | 3 | **53** | 50+ | ✅ |
| camera_library | 5 | **15** | 10+ | ✅ |
| scene_library | 0 | **20** | 20+ | ✅ |
| character_library | 3 | **10** | 10+ | ✅ |

## D2 commit 链

- `ce2ce98` v6.0 — action 3→18 (villager_run / iron_golem_attack / creeper_explode / setblock_diamond_block / summon_lightning / reveal_sign 等)
- `dbf4fe1` v6.1 — scene 0→20 (courtroom / volcano / underwater / end_island / castle_prison / redstone_lab / lava_kingdom / diamond_dragon / warden_lullaby / piglin_bank / phantom_post / witch_clinic / ender_realm / shulker_void / creeper_wedding / time_dilation / soul_market / nether_portal / village_square / spawn_point)
- `bb2cf9f` v6.2 — camera 5→15 + character 3→10
  - cameras: low_angle_hero / high_angle_top / over_shoulder / dutch_tilt / dolly_in / pan_left / orbit_360 / god_view / pov_first_person / bullet_time
  - characters: enderman / wolf / warden / piglin / witch / phantom / shulker
- `6d47cb1` v6.3 — action 18→53 收口 (villager 微动作 20 个 + steve emote 5 个 + setblock/weather/time/firework/music_disc 工具)

## parse.py v6.4

`parse.py` 实时加载 4 库 schema.examples 把 id list 注入 GPT system prompt. GPT 调用扩库时直接引用 id, 无需重新发明.

## 真实评估

- ✅ 4 库 4 项目标全过.
- ⚠️ 扩库仅 schema example, 未做 GPT 真测 — D3 跑 10+ ad-hoc 主题验证 GPT 实际引用率.
- ⚠️ 25 个新 action 多数靠 particle 模拟 (cry/laugh/anger/heal/freeze/burn) — 视觉效果待 audit_v3 真测.
