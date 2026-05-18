# Reddit r/Minecraft seed post — draft v1

**Target sub:** r/Minecraft (primary), r/redstone (secondary), r/MinecraftCommands (technical fit)

**Title options (pick one, A/B in DM tests first):**
1. I built a tool that turns one sentence into a 15-second Minecraft short film
2. One sentence → 15s Minecraft cinematic. Looking for 5 testers.
3. Headless Paper + GPT-5 + prismarine-viewer → automated MC shorts. Demo inside.

**Body (≤ 800 chars, Reddit doesn't reward walls of text):**

---

I've been tinkering with a Mac-based pipeline that turns *one English (or Chinese) sentence* into a full 15-second vertical Minecraft short — scene picked, characters spawned, 5 camera shots cut, subtitles + AI voiceover, exported as mp4.

It's all local: Paper 1.20.4 + mineflayer + prismarine-viewer headless render + ffmpeg + GPT-5 as the director. Per-render cost is ~$0.02 (just the LLM call); no Sora-style $2-a-clip charges.

Five samples shipping right now (judge_death / creeper_refuse / redstone_door / missing_spawn / dying_memory). Each is a 4-beat short drama with a visual twist on shot 5.

I'm looking for **5 testers** who:
- run MC on Mac (Linux soon)
- want to ship short-drama IP weekly
- can give honest feedback on which templates land

DM if interested. Repo + walkthrough video coming next week.

---

**First comment (pin to thread):**
Tech stack: Python 3 / Node 20 / Paper 1.20.4 / Java 21 / mineflayer 4.x / prismarine-viewer 1.33 / ffmpeg 8 (no libass — using mov_text soft subs). Happy to answer technical Qs.

**Caveat / risk notes:**
- Don't claim "world's first" — too dunkable; just say "I built"
- No "AI" in the title (some MC subs auto-filter); use "automated" / "tool"
- Skip the SaaS / monetization hint in the OP; surface only if asked
- Lead with what's *real and shippable today*, not the roadmap

**KPI to track on this post:**
- Upvote ratio after 4h (>80% = land)
- DM count for tester slots (target: 5 valid)
- Comment sentiment (top 10 comments mostly curious/helpful vs. defensive)

**Posting checklist:**
- [ ] README live, link clean
- [ ] One sample mp4 hosted on YouTube unlisted as embedded demo
- [ ] Maintainer DMs open
- [ ] 4-hour window where I can reply (Reddit penalizes silent OPs)
