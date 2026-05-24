#!/usr/bin/env python3
"""batch_nlp_v1.py — 自驱 batch 跑 N 个 NLP 建筑 + audit + screenshot + commit
每题: generate_scene → audit (gate1/3) → screenshot (45° SW) → 入 scene_library → 飞书发图
全 PASS 后批量 commit + push.
"""
import sys, os, json, time, subprocess
sys.path.insert(0, '/Users/coco/mcstory/scripts')
sys.path.insert(0, '/Users/coco/mcstory/mcp_server')
from nlp_to_building import end_to_end
from quality_gate import gate1_ground_check, gate3_bbox_proportion
from mcrcon import MCRcon

ROOT = '/Users/coco/mcstory'
SCRIPTS = f'{ROOT}/scripts'
SCHEMA = f'{ROOT}/schema/scene_library.schema.json'
OUTBOUND = '/Users/coco/.openclaw/media/outbound'

# 10 题 batch v1 — 跨文化跨风格
BATCH_V1 = [
    ("french_gothic_cathedral",   "建一座中世纪法国哥特教堂, 双塔尖顶, 玫瑰花窗"),
    ("kinkaku_pavilion",          "建一座日本金阁寺, 三层金色阁楼, 中央池塘"),
    ("forbidden_palace_hall",     "建一座北京故宫太和殿, 红柱黄琉璃瓦, 龙脊"),
    ("maya_pyramid",              "建一座玛雅金字塔, 9 层阶梯, 顶部石祭坛"),
    ("viking_longhouse",          "建一座维京长屋, 木质曲顶, 中央火坑, 烟囱"),
    ("desert_oasis_market",       "建一片沙漠绿洲, 中央水井, 帐篷集市, 棕榈树"),
    ("steampunk_factory",         "建一座蒸汽朋克工厂, 黄铜管道, 蒸汽机, 大齿轮"),
    ("medieval_fortress",         "建一座哥特石头要塞, 四角塔楼, 吊桥, 护城河"),
    ("suzhou_garden",             "建一座苏州园林, 假山, 池塘, 月洞门, 红墙"),
    ("aurora_log_cabin",          "建一座北欧极光木屋, 雪地, 烟囱, 玻璃天窗"),
]

def feishu_send(msg, media=None):
    cmd = ['/opt/homebrew/bin/openclaw','message','send','--channel','feishu','--account','hanyi',
           '--target','oc_5c1346eee378f711a40f069eec8c2ddf','-m', msg]
    if media: cmd += ['--media', media]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return '✅ Sent' in (r.stdout + r.stderr)
    except: return False

def screenshot(origin, name):
    """45° SW 拍"""
    out = f'{ROOT}/outputs/batch_v1_shots/{name}.png'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cx, cy, cz = origin
    cam = (cx-30, cy+18, cz-30); look = (cx, cy+8, cz)
    args = ['node', f'{SCRIPTS}/gate1_screenshot.js'] + \
           [str(int(c)) for c in cam] + [str(int(l)) for l in look] + [out]
    proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
    return out if 'SCREENSHOT_SAVED' in proc.stdout else None

def audit(scene_data):
    """gate1+gate3"""
    ox, oy, oz = scene_data['origin']
    L, H, W = scene_data['bbox']
    bbox = (ox-L//2, oy, oz-W//2, ox+L//2, oy+H, oz+W//2)
    with MCRcon('127.0.0.1','mcstory123',port=25575) as r:
        g1 = gate1_ground_check([ox,oy,oz], bbox, r)
    g3 = gate3_bbox_proportion(bbox, target_ratio=(0.1, 15.0))
    return {'gate1': g1, 'gate3': g3, 'overall': 'PASS' if g1['status']=='PASS' and g3['status']=='PASS' else 'PARTIAL'}

def add_to_library(scene_data, audit_result):
    sl = json.load(open(SCHEMA))
    existing = {s['id'] for s in sl['examples']}
    sid = scene_data['spec']['id']
    if sid in existing:
        # bump version
        i = 1
        while f"{sid}_b{i}" in existing: i += 1
        sid = f"{sid}_b{i}"
    sl['examples'].append({
        'id': sid, 'name': scene_data['spec']['name'],
        'origin': scene_data['origin'], 'bbox': scene_data['bbox'],
        'preset_base': scene_data['spec']['preset_base'],
        'real_dim_m': scene_data['spec']['real_dim_m'],
        'tags': scene_data['spec'].get('tags', []) + ['batch_v1','nlp_generated'],
        'design_note': scene_data['spec'].get('design_note',''),
        'cmds_total': scene_data['cmds_total'],
        'rcon_ok': scene_data['rcon_ok'],
        'quality_gate': {
            'ground': audit_result['gate1']['status'],
            'proportion': audit_result['gate3']['status'],
            'overall': audit_result['overall'],
        },
        'template': 'nlp_to_building',
        'source': f"outputs/nlp_{sid.split('_b')[0]}_*.json",
    })
    json.dump(sl, open(SCHEMA, 'w'), indent=2, ensure_ascii=False)
    return len(sl['examples']), sid

def main():
    # x 坐标分布: -800 起步, 每题 +50 间距, y=80 (auto adj), z=-450 (新区, 避开锁版 10 题)
    results = []
    t0 = time.time()
    print(f"=== batch_v1: {len(BATCH_V1)} prompts ===\n")
    for i, (name_hint, prompt) in enumerate(BATCH_V1):
        ox = -800 + i*50; oy = 80; oz = -450
        print(f"\n[{i+1}/{len(BATCH_V1)}] {name_hint} @ ({ox},{oy},{oz})")
        print(f"  prompt: {prompt}")
        try:
            res = end_to_end(prompt, origin=(ox, oy, oz))
            if not res:
                print("  ❌ NLP failed, skip"); results.append({'name':name_hint,'status':'NLP_FAIL'}); continue
            aud = audit(res)
            print(f"  audit: gate1={aud['gate1']['status']} gate3={aud['gate3']['status']} overall={aud['overall']}")
            shot = screenshot(res['origin'], f"{i+1:02d}_{name_hint}")
            print(f"  shot: {shot}")
            lib_size, sid = add_to_library(res, aud)
            print(f"  入库: {sid} (lib={lib_size})")
            # 飞书发图
            if shot:
                # 拷 outbound
                dest = f'{OUTBOUND}/batch_v1_{i+1:02d}_{name_hint}.png'
                subprocess.run(['cp', shot, dest], check=False)
                feishu_send(
                    f"🏗️ batch_v1 {i+1}/10: {res['spec']['name']} ({sid})\n  prompt: {prompt}\n  {res['cmds_total']} blocks @ {res['origin']}, {aud['overall']}",
                    media=dest)
            results.append({'idx':i+1,'name':name_hint,'sid':sid,'cmds':res['cmds_total'],
                            'audit':aud['overall'],'origin':res['origin'],'shot':bool(shot)})
        except Exception as e:
            import traceback
            print(f"  ❌ {e}\n{traceback.format_exc()[-500:]}")
            results.append({'name':name_hint,'status':f'EXCEPTION:{e}'})

    dt = time.time() - t0
    print(f"\n=== batch_v1 done in {dt:.0f}s ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    # save summary
    summary_p = f'{ROOT}/outputs/batch_v1_summary_{time.strftime("%Y%m%d-%H%M%S")}.json'
    json.dump({'duration_s':dt, 'results':results}, open(summary_p,'w'), ensure_ascii=False, indent=2)
    print(f"summary → {summary_p}")
    return results

if __name__ == '__main__':
    main()
