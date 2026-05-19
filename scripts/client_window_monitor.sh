#!/bin/bash
# client_window_monitor.sh — 老板完成 2FA + PLAY 后, 检测真客户端窗口出现, 自动接管 screencapture
# 用法: bash client_window_monitor.sh (后台跑)
LOG=/tmp/client_window_monitor.log
OUT_DIR=~/mcstory/outputs/single_action_visible_check
mkdir -p $OUT_DIR

echo "$(date) [monitor] start" >> $LOG

while true; do
  # 检测 net.minecraft.client.main.Main java 进程
  CLIENT_PID=$(ps aux | grep -iE "java.*net\.minecraft\.client\.main\.Main|java.*1\.20\.4\.jar" | grep -v grep | grep -v "Caskroom\|minecraft-launcher" | head -1 | awk '{print $2}')
  if [ -n "$CLIENT_PID" ]; then
    echo "$(date) [monitor] CLIENT JAVA PID = $CLIENT_PID — 等 30s 客户端 init + main menu" >> $LOG
    sleep 30

    # 截屏验证 (不依赖 Accessibility)
    screencapture -x $OUT_DIR/$(date +%s)_client_detected.png 2>>$LOG

    echo "$(date) [monitor] ✓ client window monitor detected. screencapture attempted." >> $LOG

    # 通知 Claude 通过 hook (老板登录后会进飞书消息)
    /opt/homebrew/bin/openclaw message send --channel feishu --account hanyi --target oc_5c1346eee378f711a40f069eec8c2ddf -m "🎯 韩沂 auto-monitor: 检测到 net.minecraft.client.main.Main PID=$CLIENT_PID. screencapture 已触发. Claude 自动接管 single_action_visible_check. 老板可继续休息/上班." 2>>$LOG

    exit 0
  fi
  sleep 5
done
