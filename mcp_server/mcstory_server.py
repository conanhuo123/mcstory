#!/usr/bin/env python3
"""mcstory MCP server — 把 voxel_dsl/quality_gate/RCON/scene_library 封 MCP tool
给 openclaw agents (GPT-5.5) + Claude Code 共用. 5 tool, stdio transport.

Tools:
  generate_scene(prompt, origin=None)
    一句话 → GPT-5.5 spec → voxel_dsl 真建 → RCON, 返 scene_id + bbox + cmds_total + origin_adjusted
  audit_quality(scene_id)
    跑 quality_gate gate1/3/4 on 已建 scene, 返 PASS/FAIL detail
  run_rcon(cmd)
    任意 RCON 命令 (safe-list: list/tp/op/gamemode/time/weather/setblock/fill/give/say/title/execute)
  screenshot(scene_id, view='45sw')
    prismarine-viewer + puppeteer 45° SW 截图, 返 PNG path
  scene_library_query(filter='', tag='')
    查 scene_library.schema.json 已入库 examples, 支持 tag/id 过滤
"""
import sys, os, json, subprocess, time, asyncio
from pathlib import Path

# 确保 scripts/ 在 path
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
SCHEMA = Path(__file__).resolve().parent.parent / "schema"
OUTPUTS = Path(__file__).resolve().parent.parent / "outputs"
sys.path.insert(0, str(SCRIPTS))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# --- 现成 mcstory 工具 ---
from nlp_to_building import end_to_end as nlp_build
from quality_gate import gate1_ground_check, gate3_bbox_proportion, gate4_detail_density
from mcrcon import MCRcon

RCON_HOST = '127.0.0.1'; RCON_PORT = 25575; RCON_PASS = 'mcstory123'
SAFE_RCON_PREFIXES = ('list','tp ','teleport ','op ','gamemode ','time ','weather ',
                      'setblock ','fill ','give ','say ','title ','execute ',
                      'kill ','clear ','effect ','summon ','playsound ')

server = Server("mcstory")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="generate_scene",
             description="一句话→GPT-5.5 spec→voxel_dsl 真建→RCON. 返 scene_id+bbox+cmds_total+origin (含垫平后 y).",
             inputSchema={"type":"object","properties":{
                 "prompt":{"type":"string","description":"中文场景描述 (eg '建唐代红色 3 层木塔')"},
                 "origin":{"type":"array","items":{"type":"number"},"description":"[x,y,z] 默认 (-600,80,-300)"},
             },"required":["prompt"]}),
        Tool(name="audit_quality",
             description="跑 gate1(ground)/gate3(proportion)/gate4(detail) on 已建 scene. 输入 nlp_*.json 路径或 scene_id.",
             inputSchema={"type":"object","properties":{
                 "scene_ref":{"type":"string","description":"scene_id 或 outputs/nlp_*.json 路径"},
             },"required":["scene_ref"]}),
        Tool(name="run_rcon",
             description=f"任意 RCON 命令. Safe-list: {', '.join(SAFE_RCON_PREFIXES)}.",
             inputSchema={"type":"object","properties":{
                 "cmd":{"type":"string","description":"RCON 命令 (不带 / 前缀)"},
             },"required":["cmd"]}),
        Tool(name="screenshot",
             description="prismarine-viewer + puppeteer 拍 45° SW 视角. 返 PNG 绝对路径.",
             inputSchema={"type":"object","properties":{
                 "origin":{"type":"array","items":{"type":"number"},"description":"目标中心 [x,y,z]"},
                 "view":{"type":"string","enum":["45sw","front","top"],"default":"45sw"},
                 "name":{"type":"string","description":"输出文件名 (无扩展)"},
             },"required":["origin","name"]}),
        Tool(name="scene_library_query",
             description="查 scene_library.schema.json. 可按 id 子串 / tag 过滤. 不传则返全部 id 列表.",
             inputSchema={"type":"object","properties":{
                 "id_substr":{"type":"string","description":"id 子串过滤"},
                 "tag":{"type":"string","description":"tag 过滤"},
             }}),
    ]

@server.call_tool()
async def call_tool(name, arguments):
    try:
        if name == "generate_scene":
            prompt = arguments["prompt"]
            origin = tuple(arguments.get("origin", [-600, 80, -300]))
            result = nlp_build(prompt, origin=origin)
            if not result:
                return [TextContent(type="text", text=json.dumps({"error":"NLP failed","prompt":prompt}, ensure_ascii=False))]
            return [TextContent(type="text", text=json.dumps({
                "scene_id": result['spec']['id'],
                "name": result['spec']['name'],
                "origin_adjusted": result['origin'],
                "bbox": result['bbox'],
                "cmds_total": result['cmds_total'],
                "rcon_ok": result['rcon_ok'],
                "rcon_success_rate": round(100*result['rcon_ok']/max(1,result['cmds_total']), 1),
                "preset_base": result['spec']['preset_base'],
                "tags": result['spec'].get('tags', []),
                "design_note": result['spec'].get('design_note',''),
                "saved_to": f"outputs/nlp_{result['spec']['id']}_{result['ts']}.json",
            }, ensure_ascii=False))]

        elif name == "audit_quality":
            ref = arguments["scene_ref"]
            if not ref.endswith('.json'):
                # treat as scene_id, find latest matching
                import glob
                matches = sorted(glob.glob(str(OUTPUTS / f"nlp_{ref}_*.json")))
                if not matches:
                    return [TextContent(type="text", text=json.dumps({"error":f"scene {ref} not found"}, ensure_ascii=False))]
                ref = matches[-1]
            d = json.load(open(ref))
            ox, oy, oz = d['origin']
            L, H, W = d['bbox']
            bbox = (ox - L//2, oy, oz - W//2, ox + L//2, oy + H, oz + W//2)
            with MCRcon(RCON_HOST, RCON_PASS, port=RCON_PORT) as r:
                g1 = gate1_ground_check([ox,oy,oz], bbox, r)
            g3 = gate3_bbox_proportion(bbox, target_ratio=(0.2, 10.0))
            palette = d.get('palette_resolved', {})
            unique = len(set(palette.values()))
            return [TextContent(type="text", text=json.dumps({
                "scene_ref": ref.split('/')[-1],
                "origin": [ox,oy,oz],
                "bbox": bbox,
                "gate1_ground": g1,
                "gate3_proportion": g3,
                "gate4_palette_diversity": {"unique_blocks": unique, "blocks": sorted(set(palette.values()))[:10]},
                "overall": "PASS" if g1['status']=="PASS" and g3['status']=="PASS" else "FAIL_PARTIAL",
            }, ensure_ascii=False))]

        elif name == "run_rcon":
            cmd = arguments["cmd"].lstrip('/')
            if not any(cmd.startswith(p) for p in SAFE_RCON_PREFIXES):
                return [TextContent(type="text", text=json.dumps({"error":"cmd not in safe-list","cmd":cmd[:50]}, ensure_ascii=False))]
            with MCRcon(RCON_HOST, RCON_PASS, port=RCON_PORT) as r:
                resp = r.command(cmd)
            return [TextContent(type="text", text=json.dumps({"cmd":cmd, "response":resp[:500]}, ensure_ascii=False))]

        elif name == "screenshot":
            origin = arguments["origin"]
            view = arguments.get("view", "45sw")
            name_ = arguments["name"]
            out_path = OUTPUTS / "mcp_shots" / f"{name_}.png"
            out_path.parent.mkdir(exist_ok=True)
            cx, cy, cz = origin
            if view == "45sw":
                cam = [cx-25, cy+15, cz-25]; look = [cx, cy+5, cz]
            elif view == "front":
                cam = [cx, cy+10, cz-30]; look = [cx, cy+5, cz]
            else:  # top
                cam = [cx, cy+40, cz]; look = [cx, cy, cz]
            proc = subprocess.run(["node", str(SCRIPTS / "gate1_screenshot.js"),
                                   *[str(int(c)) for c in cam], *[str(int(l)) for l in look], str(out_path)],
                                  capture_output=True, text=True, timeout=120)
            saved = "SCREENSHOT_SAVED" in proc.stdout
            return [TextContent(type="text", text=json.dumps({
                "saved": saved, "path": str(out_path) if saved else None,
                "size_kb": round(out_path.stat().st_size/1024,1) if out_path.exists() else 0,
                "stdout_tail": proc.stdout[-300:],
            }, ensure_ascii=False))]

        elif name == "scene_library_query":
            sl = json.load(open(SCHEMA / "scene_library.schema.json"))
            examples = sl.get('examples', [])
            id_sub = (arguments.get("id_substr") or "").lower()
            tag = (arguments.get("tag") or "").lower()
            results = []
            for s in examples:
                if id_sub and id_sub not in s['id'].lower(): continue
                if tag and tag not in [t.lower() for t in s.get('tags', [])]: continue
                results.append({
                    "id": s['id'], "name": s.get('name',''), "origin": s.get('origin'),
                    "tags": s.get('tags', [])[:5], "preset_base": s.get('preset_base'),
                })
            return [TextContent(type="text", text=json.dumps({
                "total_in_library": len(examples), "matched": len(results),
                "results": results[:30],
            }, ensure_ascii=False))]

        else:
            return [TextContent(type="text", text=json.dumps({"error":f"unknown tool {name}"}))]
    except Exception as e:
        import traceback
        return [TextContent(type="text", text=json.dumps({"error":str(e),"tb":traceback.format_exc()[-500:]}, ensure_ascii=False))]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
