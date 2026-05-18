#!/bin/bash
# 录屏 → 接 postprod 出 15s 短剧成片
# 用法: bash screenrec.sh [scene_id] [bot_script]
#   1. 老板手动开 MC 客户端登 localhost:25565 (steve 账号), 摄像机调到场景中心
#   2. 跑本脚本, ffmpeg 启动屏幕录像 → 同时 spawn bot 喊台词 → 18s 后停止
set -e
SCENE=${1:-judge_death}
BOT_JS=${2:-~/video_factory/minecraft_bot/single_bot_test.js}
OUT=~/mcstory/outputs/${SCENE}_raw_$(date +%H%M%S).mp4
echo "录屏 → $OUT"
echo "MC 客户端必须开着 + 已登服 + 摄像机调好"
echo "3 秒后开录..."
sleep 3
# avfoundation: 0 = 主屏 (ffmpeg -f avfoundation -list_devices true -i "" 查)
ffmpeg -f avfoundation -framerate 30 -i "0" -t 18 -vf "scale=1080:-2,crop=1080:1920:0:0" -c:v libx264 -preset ultrafast -crf 22 "$OUT" -y &
FFPID=$!
sleep 2  # 录屏先启, bot 后启
cd ~/video_factory/minecraft_bot && node "$BOT_JS" &
BPID=$!
wait $FFPID
kill $BPID 2>/dev/null || true
echo "✓ raw $OUT"
echo "下一步: python3 ~/mcstory/scripts/postprod.py $OUT ~/mcstory/outputs/${SCENE}_timeline.json ~/mcstory/outputs/${SCENE}_final.mp4"
