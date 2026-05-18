# mcstory User Guide — How to Make High-Quality MC Shorts

## What mcstory gives you

For one English (or Chinese) sentence input, mcstory produces:

1. **`script.json`** — 5-shot structured screenplay (GPT-5.5 director)
2. **`timeline.json`** — 23 timeline events (camera/action/subtitle/voiceover)
3. **`bot.js`** — mineflayer Node.js bot that builds the scene + summons characters + executes timeline
4. **`server_cmds.txt`** — raw Minecraft commands (`/fill`, `/setblock`, `/tellraw`, `/summon`)
5. **`final.mp4`** — automated draft preview (headless render, low-quality)
6. **`subs.srt`** + **`vo/*.mp3`** — burnable subtitles + Volcano TTS voiceover tracks

The **draft mp4** is a quick visual sanity check. For shipping-quality video, use your own MC client + ReplayMod.

## Quality tiers

| Tier | Tool | Quality | Time | Cost |
|---|---|---|---|---|
| **Draft** (built-in) | puppeteer + prismarine-viewer | Low (no shaders, no smooth camera) | 60s | $0.02 |
| **Production** (recommended) | Your MC client + ReplayMod | High (shaders, smooth cinematic) | 5min (semi-manual) | Free |

## Production workflow (5 min)

```bash
# 1. Generate script + bot.js + scene commands
python3 scripts/cli_full.py "your one-sentence idea"
# → outputs/<slug>_<stamp>/

# 2. Boot your Paper 1.20.4 server
java -Xms2G -Xmx4G -jar paper.jar nogui

# 3. Open your Minecraft client → Multiplayer → join localhost:25565
#    Install ReplayMod (one-time): mods/ folder + Fabric loader

# 4. In your MC client, run the bot:
node outputs/<slug>_<stamp>/bot.js
# This builds the scene, summons NPCs, fires tellraw lines on schedule.

# 5. Start ReplayMod recording (F6 → Record)
#    Sit back. Watch the 30-second drama play out.
#    Stop recording (F6 again).

# 6. ReplayMod → Render → MP4 1080p 60fps
#    Optional: add shaders (Iris / Sodium) for cinematic quality.

# 7. Run postprod to add subtitles + Volcano TTS:
python3 scripts/postprod.py recording.mp4 outputs/<slug>_<stamp>/timeline.json final.mp4
```

## Why not full automation?

`prismarine-viewer` (the headless renderer we use for drafts) has a [known limitation](https://github.com/PrismarineJS/prismarine-viewer/issues/477) where the camera cannot teleport to arbitrary positions while keeping chunks rendered. The renderer is designed to follow a bot's movement smoothly, not jump cuts.

Full headless high-quality recording requires `node-canvas-webgl`, which [no longer builds on Apple Silicon](https://github.com/Automattic/node-canvas/issues/2365).

The honest path is: **mcstory does the script + scaffolding work, you do the final render in your own MC client.**

## v1.0 ships

- 10 sample templates (in `samples/`)
- 4 scene auto-builders (courtroom / village / mine / redstone_door)
- 3 character types (steve / villager / iron_golem / creeper)
- One-line CLI from sentence → mp4 draft (~60s)
- GitHub Pages landing with all 10 demo videos: https://conanhuo123.github.io/mcstory/
