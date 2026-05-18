#!/bin/bash
# 10 个 ad-hoc 主题广度真测 — 验证 GPT 扩库引用率 + topdown
set -e
cd /Users/coco/mcstory
mkdir -p outputs/gate1_batch10

PROMPTS=(
  "末影杀手潜入下界堡垒偷走猪灵的金条"
  "村民在城堡监狱里组织一场红石音乐会"
  "钻石龙从虚空升起守护一座末地祭坛"
  "苦力怕在花海中向铁傀儡求婚"
  "潜影贝在海底沉船里写日记"
  "唤魔者在女巫医院里召唤幻影信使"
  "守卫者在监守者摇篮里弹竖琴"
  "猪灵银行被监守者抢劫"
  "美西螈在末影领域预言世界末日"
  "幻影邮局向时间膨胀场寄一封信"
)

# 并行 3 路启 parse.py
for i in {0..9}; do
  idx=$(printf "%02d" $i)
  echo "[$idx] ${PROMPTS[$i]}"
  python3 scripts/parse.py "${PROMPTS[$i]}" > outputs/gate1_batch10/${idx}.json 2>&1 &
  if [ $((($i + 1) % 3)) -eq 0 ]; then wait; fi
done
wait
echo "[ALL parse DONE]"

# 统计 + topdown
python3 - << 'PYEOF'
import json, os, re
from glob import glob

actions_lib = set(a['id'] for a in json.load(open('schema/action_grammar.schema.json'))['examples'])
cameras_lib = set(c['id'] for c in json.load(open('schema/camera_library.schema.json'))['examples'])
scenes_lib = set(s['id'] for s in json.load(open('schema/scene_library.schema.json'))['examples'])
chars_lib = set(c['id'] for c in json.load(open('schema/character_library.schema.json'))['examples'])

results = []
files = sorted(glob('outputs/gate1_batch10/[0-9]*.json'))
for fn in files:
    try:
        d = json.load(open(fn))
    except Exception as e:
        print(f"  ERR {fn}: {e}")
        continue
    scene = d.get('scene')
    chars = d.get('characters', [])
    cmds = d.get('build_cmds', [])
    shots = d.get('shots', [])
    # 引用率
    scene_match = scene in scenes_lib
    chars_match = sum(1 for c in chars if c in chars_lib)
    action_refs = []
    camera_refs = []
    for s in shots:
        if s.get('camera') in cameras_lib: camera_refs.append(s['camera'])
        for a in (s.get('actions') or []):
            aid = a.get('action_id') or a.get('action','')
            if aid in actions_lib: action_refs.append(aid)
    results.append({
        'file': os.path.basename(fn),
        'scene': scene, 'scene_in_lib': scene_match,
        'chars': chars, 'chars_in_lib': chars_match,
        'build_cmds_count': len(cmds),
        'shots': len(shots),
        'camera_refs': len(camera_refs),
        'action_refs': len(action_refs),
    })

print(f"\n{'='*100}")
print(f"{'#':<4}{'scene':<20}{'scene√':<8}{'chars(in/total)':<20}{'#cmds':<8}{'#shots':<8}{'cam√':<8}{'act√'}")
print('-'*100)
for r in results:
    print(f"{r['file']:<4}{(r['scene'] or 'None')[:18]:<20}{'✓' if r['scene_in_lib'] else '✗':<8}"
          f"{r['chars_in_lib']}/{len(r['chars'])}{'':<13}"
          f"{r['build_cmds_count']:<8}{r['shots']:<8}{r['camera_refs']:<8}{r['action_refs']}")

# 汇总
ok_scene = sum(1 for r in results if r['scene_in_lib'])
total_chars = sum(len(r['chars']) for r in results)
ok_chars = sum(r['chars_in_lib'] for r in results)
total_cmds = sum(r['build_cmds_count'] for r in results)
total_cam = sum(r['camera_refs'] for r in results)
total_act = sum(r['action_refs'] for r in results)
print('-'*100)
print(f"广度 {len(results)} 样本 | scene 引扩库: {ok_scene}/{len(results)} | char 引扩库: {ok_chars}/{total_chars}")
print(f"GPT 共出 {total_cmds} 条 build_cmds | 镜头引扩库: {total_cam} | 动作引扩库: {total_act}")

# topdown 渲染
import subprocess
for fn in files:
    label = os.path.basename(fn).replace('.json','')
    out = f'outputs/gate1_batch10/TOPDOWN_{label}.png'
    try:
        subprocess.run(['python3','scripts/gate1_simulate_topdown.py', fn, label, out],
                       capture_output=True, timeout=15)
    except Exception as e:
        print(f"topdown ERR {label}: {e}")

png_count = len([f for f in os.listdir('outputs/gate1_batch10') if f.startswith('TOPDOWN') and f.endswith('.png')])
print(f"topdown PNG 生成: {png_count}/{len(results)}")

import json as J
J.dump(results, open('outputs/gate1_batch10/batch10_summary.json','w'), ensure_ascii=False, indent=2)
PYEOF
echo "[DONE]"
ls outputs/gate1_batch10/ | head -25
