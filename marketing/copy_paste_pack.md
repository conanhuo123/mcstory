# mcstory Marketing Copy-Paste Pack

老板回来 5 min 操作: 复制对应平台文案 → 粘贴 → 发. 完成 5 渠道种子触达.

---

## 1. Reddit — r/Minecraft (主目标)

**Title** (pick 1):
- I built a tool: one sentence → 15s Minecraft short film (draft auto, production via ReplayMod)
- Automated Minecraft short film pipeline (Mac, free): one sentence in, mp4 out
- Open source: text → MC short drama, with optional ReplayMod production tier

**Body** (≤ 800 chars):

I've been building a Mac-based pipeline that turns one English (or Chinese) sentence into a 15-second vertical Minecraft short. It picks a scene, spawns characters, generates 5 camera shots, writes subtitles, adds AI voiceover, exports mp4.

Two tiers:
- **Draft** (built-in, 60s, $0.02): puppeteer + prismarine-viewer for quick sanity check
- **Production** (5min, free): you open MC + ReplayMod, mcstory drives the bot, ReplayMod records cinematic 1080p

Stack: Python + Node + Paper 1.20.4 + mineflayer + GPT-5.5 director. Per-render cost ~$0.02 (just the LLM call).

10 templates shipping: judge_death / creeper_refuse / redstone_door / missing_spawn / dying_memory / sun_thief / fake_ally / village_trial / golem_betray / redstone_world.

Live demo (10 mp4s on the page): https://conanhuo123.github.io/mcstory/
Repo: https://github.com/conanhuo123/mcstory

Looking for 5 beta testers who ship MC short-drama IP. DM me.

**First comment** (pin):
Why two tiers? The headless renderer has a [known issue](https://github.com/PrismarineJS/prismarine-viewer/issues/477) where camera jump-cuts don't reload chunks. That's why production-grade videos go through your own MC client + ReplayMod. Drafts are for fast scripted-concept iteration.

---

## 2. Twitter / X (480 chars)

```
i built mcstory: one english sentence → 15s minecraft short film 🎬

→ GPT-5 picks scene/characters/5 shots
→ mineflayer spawns NPCs + builds set
→ TTS voiceover + burned subtitles
→ $0.02 per render

10 templates shipping. live demos:
https://conanhuo123.github.io/mcstory/

looking for 5 mac beta testers
```

---

## 3. Hacker News — Show HN

**Title**: Show HN: mcstory – one sentence → 15s Minecraft short film, draft auto + ReplayMod production

**Body**:
mcstory is a Mac pipeline that turns one English (or Chinese) sentence into a 15-second vertical Minecraft drama. GPT-5.5 acts as director: picks scene, spawns characters, writes 5 shots with twists, generates subtitles, adds Volcano TTS voiceover, exports mp4.

There are two tiers because headless MC rendering has limits:
- Draft (60s, $0.02): puppeteer + prismarine-viewer, fully automated. Quality is rough — for scripted-concept iteration.
- Production (5min, free): you open your own MC client + ReplayMod, mcstory drives the bot, ReplayMod records. Add Iris shaders for cinematic look.

Stack: Python 3 + Node 20 + Paper 1.20.4 + mineflayer 4 + prismarine-viewer + ffmpeg + GPT-5.5 via Azure.

Why? AI video generators (Sora, Runway) cost $0.30–$2 per 15s clip and only do one-shot continuous footage — no multi-shot narrative. A Minecraft server is fully programmable, so wrap a GPT director on top and you get multi-shot narrative at near-zero cost.

Source-available, MIT license for v0.1. Demo + 10 sample mp4s: https://conanhuo123.github.io/mcstory/
Repo: https://github.com/conanhuo123/mcstory

Looking for 5 beta testers; feedback on which templates land and which feel like filler.

---

## 4. 即刻 (Chinese — JikePost)

```
做了一个工具叫 mcstory:
一句话(中文/英文) → 15 秒 MC 短剧 mp4
GPT-5 当导演自动选场景/角色/5 镜头/反转, mineflayer 控 NPC + 搭场景, 火山 TTS 配音, ffmpeg 烧字幕.

10 个模板, $0.02 一片 (GPT 调用费, 服务器是本机).
高清成片接 ReplayMod (半自动), 草稿全自动.

Demo (10 个 mp4 嵌在页面): https://conanhuo123.github.io/mcstory/
Repo: https://github.com/conanhuo123/mcstory

招 5 个 MC 短剧创作者 beta, DM 我.
```

---

## 5. 微信朋友圈 / WeChat

```
[图: mcstory landing page 截图]

业余项目: 一句话 → 15s Minecraft 短剧

GPT-5 当导演自动写剧本/选场景/搭画面, AI 配音 + 字幕, $0.02/片.
草稿全自动 60s 出, 高清需自己开 MC + ReplayMod (5 min).

10 个模板试玩: https://conanhuo123.github.io/mcstory/
代码: https://github.com/conanhuo123/mcstory

找几个 Mac 上玩 MC + 想做短剧账号的人测试, 评论或私信我.
```

---

## 老板回来操作步骤 (5 min)

1. 打开 https://conanhuo123.github.io/mcstory/ 自己看 5 秒确认页面 OK
2. Reddit: 登录 r/Minecraft → New Post → 复制上方 Title + Body 粘贴 → 选最稳 title
3. Twitter: 登录 → 粘贴上方 480 字
4. Hacker News: 登录 → Submit → 粘贴 title + body, 选 Show HN 类型
5. 即刻: 登录 App → 新动态 → 粘贴 + 自动选 hashtag
6. 朋友圈: 截 landing page 截图 + 粘贴上方文案

发完坐 4 小时, 看 DM/comment, 把响应数 + 评论关键词反馈给 Claude, Claude 帮整理 next iteration.

## 失败指标 (老板自查)
- Reddit 4h upvote ratio < 70% → title 太强或太弱, 换
- Twitter 4h 0 like 0 retweet → tag 不对或时间错
- HN 滑出首页前 (4h 内 < 30 points) → body 太长或卖点不清
- 即刻 0 评论 → 不够本地化, 改方言
- 朋友圈 0 反馈 → 个人圈非 target audience, 不指标
