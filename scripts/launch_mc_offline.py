#!/usr/bin/env python3
"""launch_mc_offline.py — CLI 启动 Minecraft 1.20.4 客户端 (offline / cracked mode).
paper online-mode=false + enforce-secure-profile=false 允许伪 token.
不需 Mojang OAuth / 2FA.
"""
import os, json, subprocess, sys, glob, platform

MC = os.path.expanduser('~/Library/Application Support/minecraft')
VER = '1.20.4'
manifest = json.load(open(f'{MC}/versions/{VER}/{VER}.json'))

# 严格按 manifest libraries (避免版本冲突), 找不到的 fallback 跳过
cp = []
missing = []
for lib in manifest.get('libraries', []):
    if 'downloads' not in lib: continue
    art = lib['downloads'].get('artifact')
    if art:
        p = f"{MC}/libraries/{art['path']}"
        if os.path.exists(p):
            cp.append(p)
        else:
            # 找同 lib 任一版本作 fallback
            lib_name = art['path'].split('/')[-1].rsplit('-',1)[0]  # e.g. logging-1.1.1 -> logging
            cands = glob.glob(f"{MC}/libraries/**/{lib_name}*.jar", recursive=True)
            if cands:
                cp.append(cands[0])
                print(f"FALLBACK: {art['path']} -> {cands[0].split('libraries/')[-1]}")
            else:
                missing.append(art['path'])
print(f"manifest libs: {len(cp)}, missing: {len(missing)}")
for m in missing[:5]: print(f"  MISSING: {m}")
# 主 jar
cp.append(f"{MC}/versions/{VER}/{VER}.jar")

# natives dir: 老 manifest 用 classifiers, 新 (1.20+) 不用. 但 LWJGL 仍需 native libs.
# LWJGL natives 通常在 libraries 里同 path 加 -natives-macos-arm64.jar
arch = 'arm64' if platform.machine() == 'arm64' else 'x86_64'

# 检查 LWJGL natives jar
lwjgl_natives = glob.glob(f"{MC}/libraries/org/lwjgl/**/*natives-macos*.jar", recursive=True)
print(f"LWJGL natives jars: {len(lwjgl_natives)}")
for j in lwjgl_natives[:5]: print(f"  {j[-80:]}")

# Mac M-series 需要 arm64 natives
arm_natives = [j for j in lwjgl_natives if 'arm64' in j or 'macos-arm64' in j]
intel_natives = [j for j in lwjgl_natives if 'macos' in j and 'arm64' not in j]
print(f"arm64 natives: {len(arm_natives)}, intel natives: {len(intel_natives)}")

# 加 natives jar 到 cp
cp.extend(lwjgl_natives)

# Extract natives 到 tmp/natives_1.20.4 (LWJGL 需要 .dylib/.so 在 java.library.path)
natives_dir = '/tmp/mc_natives_1.20.4'
os.makedirs(natives_dir, exist_ok=True)
import zipfile
extracted = 0
for jar in lwjgl_natives + [j for j in glob.glob(f"{MC}/libraries/**/*natives*.jar", recursive=True) if 'macos' in j or 'osx' in j]:
    try:
        z = zipfile.ZipFile(jar)
        for n in z.namelist():
            if n.endswith('.dylib') or n.endswith('.so'):
                z.extract(n, natives_dir); extracted += 1
    except Exception as e:
        print(f"extract err {jar[-40:]}: {e}")
print(f"extracted natives: {extracted}")

cp_str = ':'.join(cp)
print(f"classpath jars: {len(cp)}")

# 老 Java 8 不行, 1.20.4 需 Java 17+. 用 system java
java_bin = '/opt/homebrew/opt/openjdk@21/bin/java'
if not os.path.exists(java_bin):
    java_bin = subprocess.check_output(['which','java']).decode().strip()
print(f"java: {java_bin}")

# 构造 args
args = [
    java_bin,
    f'-Djava.library.path={natives_dir}',
    f'-Dorg.lwjgl.librarypath={natives_dir}',
    '-Xmx2G',
    '-XstartOnFirstThread',  # macOS 必须
    '-cp', cp_str,
    'net.minecraft.client.main.Main',
    '--version', VER,
    '--gameDir', MC,
    '--assetsDir', f'{MC}/assets',
    '--assetIndex', manifest.get('assetIndex',{}).get('id','12'),
    '--uuid', '00000000-0000-0000-0000-000000000000',
    '--username', 'ClaudeBot',
    '--accessToken', 'FFFFFFFFFFFFFFFF',
    '--userType', 'legacy',
    '--versionType', 'release',
]
print('JAVA CMD (truncated):', ' '.join(args[:8]) + ' ...')

# 写到 shell script 方便手动 retry
sh = '/tmp/launch_mc_offline.sh'
with open(sh, 'w') as f:
    f.write('#!/bin/bash\n')
    f.write(' '.join(f'"{a}"' if ' ' in a else a for a in args))
    f.write('\n')
os.chmod(sh, 0o755)
print(f"shell script saved: {sh}")

# 启动 (background, log to /tmp)
log_path = '/tmp/mc_offline.log'
print(f"launching ... log -> {log_path}")
with open(log_path, 'w') as logf:
    p = subprocess.Popen(args, stdout=logf, stderr=subprocess.STDOUT)
    print(f"java PID: {p.pid}")
