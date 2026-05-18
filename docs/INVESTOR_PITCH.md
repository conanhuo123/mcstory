# mcstory — Investor One-Pager

## 一句话定位
**文字 → MC 可执行导演系统** — entity-level scriptable narrative engine. 用户输入一句故事, 系统生成导演 IR, 调度场景/角色/动作/镜头/道具, 在真实 MC/Fabric 服执行并渲染成片.

## 目标用户 (阶段演进)
- **Y1**: MC 创作者 (YouTuber / TikToker / Twitch streamer 自动产短剧)
- **Y2-3**: 教育内容机构 / 营销 production house (一句 brief → 30s MC 风格短剧)
- **Y4+**: Game studio API (Roblox / Unity / UE 内置 "natural language scene direction" 能力)

## 为什么现在
1. LLM-as-director 技术拐点 (GPT-5 / Claude 4 能稳定输出结构化 IR)
2. AI 视频 (Sora / Pika) 输出 pixel-latent video, 不可编辑; entity-level 空白
3. MC 服务端开放 (mineflayer / Paper / Fabric / ServerReplay), 资产已开源
4. Creator economy 需求: MC 短剧 IP 在 TikTok 月播放百亿, 创作者每片要 8h ReplayMod, 我们做到 30s

## 护城河 (4 库 + 1 闭环, Sora 学不来)
1. **动作语法库** — `walk_to / look_at / use_item / setblock` 等 entity-level token, 跨 GPT 多次 render 复利
2. **镜头库** — wide / medium / closeup / freeze_zoom 等 preset, 跨 sample 复用
3. **场景资产库** — courtroom / village / mine / redstone_door 等 build_cmds, 越多越值钱
4. **道具/角色库** — villager / iron_golem / creeper + 自定义 NBT, 跨剧本同款
5. **自查评分闭环** — frame diff + entity 出现 + 镜头变化 + 故事反转检测, 自动打回 reroll

## 10 轮论证后的终局
**LLM-native scriptable narrative video engine** —
- 自然语言写剧本 (任意长度)
- 输出多 shot 视频 (任意 game/3D engine target)
- 完全可编辑 (改 prompt 视频局部 re-render)
- 数据飞轮: 用户 edit 行为 → train 自己的 edit-able video model → 反向卖给大模型公司

## MVP 进展 (今天 18h 端到端)
- ✅ 10 sample 题库 (4-beat 短剧结构, GPT 自动选 scene/character/twist)
- ✅ 4 scene auto-build (Fabric server 纯命令搭场景)
- ✅ Fabric 1.20.4 + ServerReplay → 10 真 .mcpr 录像生成
- ✅ cli_full.py 一行命令: 一句话 → mp4 + mcpr (双轨)
- ✅ GitHub: https://github.com/conanhuo123/mcstory (public)
- ✅ Landing: https://conanhuo123.github.io/mcstory/

## 下周可验证里程碑
- **D1-2**: .mcpr → mp4 真渲染通 (Linux VM 或 ReplayMod batch)
- **D3-4**: 动作语法库 v0.1 schema 落
- **D5**: 镜头库 v0.1 (扩到 15 preset)
- **D6**: 自查评分闭环 v0.1 (3 项: frame diff / entity / 镜头)
- **D7**: 10 alpha 用户 wait list (Discord MC 群 cold reach)

## 风险 (诚实)
- **PMF 未验证**: 0 付费用户 / 0 LOI
- **技术天花板**: .mcpr → mp4 还需 user GUI 或 Linux VM (上游 ReplayMod issue #982 未解)
- **TAM 模糊**: MC 创作者付费意愿不验证
- **大厂威胁**: Sora 1y 内可能加 MC 风格 prompt
- **scaling 经济**: multi-tenant Fabric server 成本未建模

## 商业 ladder
| Tier | Price | Target |
|---|---|---|
| Free | \$0 | 浏览器 30s 预览 + Record webm |
| Creator | \$5/render | .mcpr 下载 + ReplayMod render guide |
| Pro | \$99/月 | 100 render/月 + API access |
| Studio | \$10K/月 | B2B 定制 scene + 私有部署 |

## 我们卖的不是 MC 视频, 是**可执行导演层**
谁先积累动作语法和自查数据, 谁先有复利.
