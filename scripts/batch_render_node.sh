#!/bin/bash
# batch_render_node.sh — 在 Linux 云 VM 上 batch render .mcpr → mp4
# 用法 (老板回家任意时刻 spin DigitalOcean/AWS Ubuntu 22 + 4GB RAM, ssh 上去跑这个):
#   curl -sL https://raw.githubusercontent.com/conanhuo123/mcstory/master/scripts/batch_render_node.sh | bash
#
# 这一个脚本完成: 装依赖 → 装 MC 1.20.4 client + Fabric + ReplayMod + HeadlessMC → batch render
set -euo pipefail

WORK=$HOME/mcstory-render
mkdir -p $WORK && cd $WORK

echo "=== 1. install java 21 + xvfb + ffmpeg ==="
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-21-jdk xvfb ffmpeg curl wget python3 python3-pip

echo "=== 2. download MC 1.20.4 client ==="
mkdir -p mc/versions/1.20.4
cd mc/versions/1.20.4
curl -sL https://piston-data.mojang.com/v1/objects/fd19469fed4a4b4c15b2d5133985f0e3e7816a8a/client.jar -o 1.20.4.jar

echo "=== 3. download fabric installer + install ==="
cd $WORK
wget -q https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.0.1/fabric-installer-1.0.1.jar
java -jar fabric-installer-1.0.1.jar client -mcversion 1.20.4 -dir $WORK/mc -noprofile

echo "=== 4. download mods (Fabric API, Fabric Kotlin, ReplayMod) ==="
mkdir -p mc/mods
cd mc/mods
# Fabric API
URL_API=$(curl -s "https://api.modrinth.com/v2/project/fabric-api/version" | python3 -c "import sys,json;d=json.load(sys.stdin);print(next(f['url'] for v in d if '1.20.4' in v['game_versions'] and 'fabric' in v['loaders'] for f in v['files'] if f.get('primary')))")
curl -sL "$URL_API" -o fabric-api.jar
# ReplayMod
URL_RM=$(curl -s "https://api.modrinth.com/v2/project/replaymod/version" | python3 -c "import sys,json;d=json.load(sys.stdin);
for v in d:
    if '1.20.4' in v.get('game_versions',[]) and 'fabric' in v.get('loaders',[]):
        for f in v.get('files',[]):
            if f.get('primary'): print(f['url']);break
        break")
curl -sL "$URL_RM" -o replaymod.jar
ls -la $WORK/mc/mods/

echo "=== 5. download HeadlessMC ==="
cd $WORK
HMC_URL=$(curl -s https://api.github.com/repos/headlesshq/headlessmc/releases/latest | python3 -c "import sys,json;d=json.load(sys.stdin);print(next(a['browser_download_url'] for a in d['assets'] if 'launcher' in a['name'].lower() and 'specifics' in a['name'].lower()))")
wget -q "$HMC_URL" -O headlessmc.jar

echo "=== 6. setup Xvfb display ==="
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
sleep 2

echo "=== 7. batch render all .mcpr in ./mcpr_input ==="
mkdir -p mcpr_input mp4_output
cp mc/replay_recordings/*.mcpr mcpr_input/ 2>/dev/null || true
echo "Place .mcpr files in $WORK/mcpr_input/ then run:"
echo "  cd $WORK && for f in mcpr_input/*.mcpr; do"
echo "    cp \"\$f\" mc/replay_recordings/"
echo "    java -jar headlessmc.jar launch --version fabric-loader-1.20.4 --command \"replay render \$(basename \$f) --output \$WORK/mp4_output/\$(basename \$f .mcpr).mp4\""
echo "  done"

echo "=== DONE setup. Total install size: $(du -sh $WORK | cut -f1) ==="
echo "Next step: scp ~/video_factory/fabric_server/recordings/chunks/*/*.mcpr root@<VM_IP>:$WORK/mcpr_input/"
echo "Then ssh in, run the loop above. Each render ~1-2 min."
