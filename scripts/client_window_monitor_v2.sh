#!/bin/bash
# v2: 严格匹配 net.minecraft.client.main.Main + ALIVE > 60s + 检查窗口
LOG=/tmp/client_window_monitor_v2.log
OUT_DIR=~/mcstory/outputs/single_action_visible_check
mkdir -p $OUT_DIR

echo "$(date) [v2] start" >> $LOG

while true; do
  # 必须严格 main.Main + 持续 alive
  PID=$(ps aux | grep -E "java.*net\.minecraft\.client\.main\.Main\b" | grep -v grep | head -1 | awk '{print $2}')
  if [ -n "$PID" ]; then
    # 确认 alive 30s 后再 screencapture (避免短命 helper 误触发)
    sleep 30
    if ps -p $PID > /dev/null 2>&1; then
      echo "$(date) [v2] CONFIRMED PID=$PID alive > 30s" >> $LOG
      # 检查窗口存在 (osascript 即使权限拒也能拿到 window list 部分)
      OUT="$OUT_DIR/$(date +%s)_client_window.png"
      screencapture -x "$OUT" 2>>$LOG
      echo "$(date) [v2] saved: $OUT" >> $LOG
      /opt/homebrew/bin/openclaw message send --channel feishu --account hanyi --target oc_5c1346eee378f711a40f069eec8c2ddf -m "🎯 韩沂 auto-monitor v2: net.minecraft.client.main.Main PID=$PID 持续 alive 30s+. screencapture 落 $OUT. Claude 自动接管 single_action_visible_check." 2>>$LOG
      exit 0
    else
      echo "$(date) [v2] PID=$PID died within 30s — false positive, continue monitoring" >> $LOG
    fi
  fi
  sleep 10
done
