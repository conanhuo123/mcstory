// gate3_visual_lowhead.js — 关 3 视觉级"村民低头": cam 看 villager, 截 before/after PNG
const net = require('net');
const mineflayer = require('mineflayer');
const { Vec3 } = require('vec3');
const { mineflayer: pv } = require('prismarine-viewer');
const puppeteer = require('puppeteer');

// 牢笼 origin = (-40, 79, -240). villager 在 (-40, 81, -240). cam 从 (-37, 82, -240) 看 villager.
const CAM = new Vec3(-37, 82, -240);
const LOOK = new Vec3(-40, 81, -240);
const OUT_BEFORE = '/Users/coco/mcstory/outputs/gate1_judge_death_min/lowhead_before.png';
const OUT_AFTER = '/Users/coco/mcstory/outputs/gate1_judge_death_min/lowhead_after.png';
const VIEWER_PORT = 3026;

class Rcon {
  constructor(host, port, pass) { this.host = host; this.port = port; this.pass = pass; this.id = 0; }
  connect() { return new Promise((res, rej) => {
    this.sock = net.connect(this.port, this.host, () => this._send(3, this.pass));
    this.sock.once('data', () => res());
    this.sock.on('data', () => {}); this.sock.on('error', rej);
  });}
  _send(t, b) { const buf = Buffer.alloc(14 + Buffer.byteLength(b));
    buf.writeInt32LE(10 + Buffer.byteLength(b), 0); buf.writeInt32LE(++this.id, 4);
    buf.writeInt32LE(t, 8); buf.write(b, 12, 'utf8'); this.sock.write(buf); }
  cmd(s) { this._send(2, s.startsWith('/') ? s.slice(1) : s); }
}
const rcon = new Rcon('127.0.0.1', 25575, 'mcstory123');

async function screenshot(path) {
  const browser = await puppeteer.launch({ headless: false, args: [
    '--no-sandbox', '--enable-webgl', '--ignore-gpu-blocklist',
    '--window-size=1280,720', '--window-position=2000,2000',
    '--disable-cache', '--disable-application-cache',
  ]});
  const page = await browser.newPage();
  await page.setCacheEnabled(false);
  await page.setViewport({ width: 1280, height: 720 });
  await page.goto(`http://localhost:${VIEWER_PORT}`, { waitUntil: 'networkidle2', timeout: 30000 });
  await new Promise(r => setTimeout(r, 7000));
  await page.screenshot({ path });
  await browser.close();
  console.log('SCREENSHOT', path);
}

(async () => {
  await rcon.connect();
  console.log('RCON connected');
  // setworldspawn 牢笼前 + forceload
  rcon.cmd(`setworldspawn ${CAM.x} ${CAM.y} ${CAM.z}`);
  rcon.cmd(`forceload add ${Math.floor(CAM.x/16)*16} ${Math.floor(CAM.z/16)*16}`);
  rcon.cmd(`gamerule spawnRadius 0`);
  await new Promise(r => setTimeout(r, 1500));
  // 重置 villager pitch=0
  rcon.cmd(`tp @e[type=villager,name="继任者",limit=1] ~ ~ ~ 0 0`);
  await new Promise(r => setTimeout(r, 800));

  // 用唯一 username 避免 player.dat 缓存
  const uniq = 'lhview' + Date.now().toString().slice(-6);
  const cam = mineflayer.createBot({ host: 'localhost', port: 25565, username: uniq, version: '1.20.4' });
  cam.on('error', e => { console.error('cam err', e.message); process.exit(1); });
  cam.once('spawn', async () => {
    console.log('cam spawned at', cam.entity.position);
    rcon.cmd(`gamemode spectator ${uniq}`);
    await new Promise(r => setTimeout(r, 800));
    // RCON tp cam 到 牢笼旁 — 现在 paper enforce-secure-profile=false, mineflayer 真 player, tp 生效
    rcon.cmd(`tp ${uniq} ${CAM.x} ${CAM.y} ${CAM.z}`);
    // 等 server 发 position packet + mineflayer entity.position 同步
    for (let i = 0; i < 20; i++) {
      await new Promise(r => setTimeout(r, 400));
      if (Math.abs(cam.entity.position.x - CAM.x) < 3) break;
    }
    console.log('AFTER TP cam.pos =', cam.entity.position);
    await cam.lookAt(LOOK);
    await new Promise(r => setTimeout(r, 800));
    pv(cam, { port: VIEWER_PORT, firstPerson: true, viewDistance: 6 });
    console.log('VIEWER_READY');
    await new Promise(r => setTimeout(r, 8000));

    // 截 before (pitch=0)
    await screenshot(OUT_BEFORE);

    // 触发动作: pitch → 45 + cam 微小 tp 强制 viewer 刷新 entity render
    rcon.cmd(`tp @e[type=villager,name="继任者",limit=1] ~ ~ ~ 0 45`);
    await new Promise(r => setTimeout(r, 800));
    rcon.cmd(`tp ${uniq} ${CAM.x + 0.5} ${CAM.y} ${CAM.z}`);
    await new Promise(r => setTimeout(r, 800));
    rcon.cmd(`tp ${uniq} ${CAM.x} ${CAM.y} ${CAM.z}`);
    await new Promise(r => setTimeout(r, 1200));
    await cam.lookAt(LOOK);
    await new Promise(r => setTimeout(r, 800));

    // 截 after (pitch=45)
    await screenshot(OUT_AFTER);
    console.log('DONE');
    process.exit(0);
  });
})();
