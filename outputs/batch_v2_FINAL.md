# batch_v2 v2 module 大扩 vs v1 (老板"不够精致"反馈直接测)

跑完 17 min (1018s), 9/10 题 (法国哥特 v2 已单测跳过), 7 PASS + 2 PARTIAL.

## 提升对比

| 题 | v1 cmds | v2 cmds | x | audit |
|---|---|---|---|---|
| kinkaku_pavilion 金阁寺 | 6708 | 16374 | 2.44x | PASS |
| forbidden_palace_hall 太和殿 | 9402 | 39170 | **4.17x** | PASS |
| maya_pyramid 玛雅金字塔 | 11944 | 28054 | 2.35x | PASS |
| viking_longhouse 维京长屋 | 1204 | 2294 | 1.91x | PASS |
| desert_oasis_market 绿洲集市 | 3956 | 15719 | **3.97x** | PARTIAL |
| steampunk_factory 蒸汽朋克 | 3637 | 13766 | **3.78x** | PASS |
| medieval_fortress 哥特要塞 | 9388 | 17527 | 1.87x | PASS |
| suzhou_garden 苏州园林 | 2672 | 11710 | **4.38x** | PASS |
| aurora_log_cabin 北欧木屋 | 942 | 1346 | 1.43x | PARTIAL |

**平均 2.82x 提升**, scene_library 增 9 examples → 总 57.

## v2 改进点 (module_library + nlp_to_building)
- module 8 → 21 (+pyramid_stepped/dome_solid/gothic_double_spire/pagoda_eaves/column_grid/window_grid/rose_window/grand_staircase/...)
- prompt 强制 Foundation 1+Body 2+Decor 2+ 组合
- prompt 题材建议 (希腊神庙 / 哥特 / 中式 / 摩天 / 沙漠)
- scale 偏大 (神庙 40-60 / 塔 35-50 高 / 金字塔 35-55 底)

## 老板拍后续 (优先级)
- L3 humanoid v2 继续推 5 原型 (古装/武将/动物)
- L1.3 puppeteer scrape (chrome-devtools-mcp 突破 Cloudflare)
- 5 关链路真 mp4 端到端 demo
