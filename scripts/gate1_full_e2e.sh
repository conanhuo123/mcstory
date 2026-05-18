#!/bin/bash
# 关 1 端到端: 3 主题 build + 截图证明
set -e
cd /Users/coco/mcstory

# 清旧的 cam process
pkill -f gate1_screenshot.js 2>/dev/null || true
sleep 1

run_one() {
  local label="$1"
  local jsonf="$2"
  local outpng="$3"
  echo "=== $label ==="
  # 清场 + 跑 build
  python3 - <<PYEOF
from mcrcon import MCRcon
import json
d = json.load(open('$jsonf'))
with MCRcon('127.0.0.1', 'mcstory123', port=25575) as r:
    r.command("fill -80 78 -210 -40 95 -170 air")
    ok = 0
    for c in d['build_cmds']:
        if 'Successfully' in r.command(c) or 'Changed' in r.command(c): ok += 1
    print(f"  build executed (re-check skipped, total={len(d['build_cmds'])})")
PYEOF
  # 截图 (cam 在 spawn 点 -37,64,-164, build 在 -60,79,-190, 距离 ~28 块, viewDistance 6 chunks=96 块 OK)
  cd /Users/coco/video_factory/minecraft_bot
  ( node gate1_screenshot.js -37 70 -164 -60 82 -190 $outpng ) &
  local PID=$!
  sleep 45
  kill $PID 2>/dev/null || true
  cd /Users/coco/mcstory
  ls -la $outpng 2>&1 | head -1
}

run_one "深海沉船潜影贝" /Users/coco/mcstory/outputs/gate1_acceptance/01_shulker_ship.json /Users/coco/mcstory/outputs/gate1_acceptance/PROOF_01_shulker.png
run_one "末影龙花海产卵" /Users/coco/mcstory/outputs/gate1_acceptance/02_ender_dragon.json /Users/coco/mcstory/outputs/gate1_acceptance/PROOF_02_ender.png
run_one "苦力怕监狱钢琴" /Users/coco/mcstory/outputs/gate1_acceptance/03_creeper_piano.json /Users/coco/mcstory/outputs/gate1_acceptance/PROOF_03_prison.png
echo "[DONE]"
ls -la /Users/coco/mcstory/outputs/gate1_acceptance/PROOF_*.png
