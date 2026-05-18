# mcstory — One-Sentence → 15s Minecraft Short Film

Type **one sentence**. Get back a **15-second cinematic Minecraft short** — script, scene, characters, camera moves, voiceover, subtitles, mp4 — fully automated.

```bash
python3 scripts/cli_full.py "the creeper refuses to explode, because it's guarding a glowing villager egg"
```

→ `outputs/<slug>_<timestamp>/final.mp4` (≈30 MB, 15s, 1080×1920 vertical, mov_text subs)

Built for short-form creators who can write a logline but can't (or won't) film. v0.1 ships with 5 templates; the pipeline is one Python entrypoint.

---

## What's in v0.1

Five-shot dramatic structure (3 + 3 + 3 + 3 + 3 seconds), validated on 5 golden samples:

| ID | Logline | Twist |
|---|---|---|
| `judge_death` | A villager pleads in his own voice on the execution block | He is the previous server owner |
| `creeper_refuse` | A creeper stands but refuses to detonate | It's guarding a glowing villager egg under its feet |
| `redstone_door` | A player walks through a redstone door at night | The mirror inside shows a villager's face — his own |
| `missing_spawn` | A player wakes; bed gone, map corrupted | The sign reads "you were never born here" |
| `dying_memory` | A villager forgets one memory per morning | He turns into a creeper before the screen cuts |

Each template = JSON with `scene / characters / action / camera / subtitle / twist_visual` fields. Pluggable — copy `samples/judge_death.json`, rewrite 5 shots, run.

## Architecture (5-step pipeline)

```
one sentence
   ↓ parse.py        GPT-5.5 → 5-shot script JSON
   ↓ translate.py    script → 23 timeline events (camera/action/subtitle/voiceover)
   ↓ record.py       timeline → mineflayer bot.js (Node)
   ↓ viewer+ffmpeg   headless Paper + prismarine-viewer + Chrome capture
   ↓ postprod.py     ffmpeg + Volcano TTS mix + mov_text subtitles
final.mp4 (15s, 1080×1920)
```

All five steps are independent scripts in `scripts/`. The wrapper `cli_full.py` chains them end-to-end in ~60 seconds per render.

## Quick start (Mac + ffmpeg + Java 21 + Node 20)

```bash
# 1. boot Paper 1.20.4 once
cd ~/video_factory/mc_server && \
  /opt/homebrew/opt/openjdk@21/bin/java -Xms2G -Xmx4G -jar paper.jar nogui &

# 2. one-line render
python3 scripts/cli_full.py samples/judge_death.json
# or with a free-form prompt:
python3 scripts/cli_full.py "末影人偷走太阳, 铁傀儡拒绝出手"
```

Output lands in `outputs/<slug>_<stamp>/final.mp4`.

## Why this exists

YouTube Shorts / TikTok / 小红书 reward IP creators who ship daily. Most can't film.

AI video generators (Sora, Runway, Jimeng) cost $0.30–$2 per 15-second clip and only do **one-shot continuous footage** — not multi-shot narrative with reversal.

A Minecraft server is fully programmable. Every scene, every actor, every camera move is a command. Wrap a GPT-5 director on top and you get:

- per-render cost near $0 (server is local; GPT is the only paid call ≈ $0.02 / script)
- multi-shot narrative control (5 cuts, scripted twist)
- consistent IP look (your scenes, your characters, your style)

## Roadmap

- **v0.1** (now): 5 templates, single-server, single-camera, Chinese TTS via Volcano
- **v0.2**: WorldEdit schematic auto-build, multi-bot character actors, English TTS via ElevenLabs
- **v0.3**: Web UI (paste prompt → preview → export), pay-per-render
- **v1.0**: text-to-movie — chain 60s episodes into 10-minute MC films

## Status

- **2026-05-18**: 5-sample library shipping, all hit the 15s / vertical / subtitles QC gate
- Looking for **5 beta testers** who run Minecraft locally and ship short-drama IP. DM maintainer.

## License

Source-available, non-commercial for v0.1. v0.2+ will be SaaS.
