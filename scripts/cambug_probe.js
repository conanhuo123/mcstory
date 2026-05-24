// cambug_probe.js — Phase 1/3 探针: 验证 H1 "相机只在 bot move 时更新"
// 用法: node cambug_probe.js <camX> <camY> <camZ> <lookX> <lookY> <lookZ> <out1_before> <out2_after>
// 不改 gate1_screenshot.js. 跑两张图: before(原样静止) vs after(连上后强制 emit move)
const net = require('net');
const mineflayer = require('mineflayer');
const { Vec3 } = require('vec3');
const { mineflayer: pv } = require('prismarine-viewer');
const puppeteer = require('puppeteer');

const [,, cx, cy, cz, lx, ly, lz, out1, out2] = process.argv;
const CAM = new Vec3(parseFloat(cx), parseFloat(cy), parseFloat(cz));
const LOOK = new Vec3(parseFloat(lx), parseFloat(ly), parseFloat(lz));
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

function logLook(tag, cam) {
  console.log(`[${tag}] pos=`, cam.entity.position,
    'yaw=', cam.entity.yaw.toFixed(4), 'pitch=', cam.entity.pitch.toFixed(4));
}

(async () => {
await rcon.connect();
console.log('RCON connected');
rcon.cmd(`setworldspawn ${Math.round(CAM.x)} ${Math.round(CAM.y)} ${Math.round(CAM.z)}`);
rcon.cmd(`forceload add ${Math.floor(CAM.x/16)*16} ${Math.floor(CAM.z/16)*16}`);
rcon.cmd(`forceload add ${Math.floor(LOOK.x/16)*16} ${Math.floor(LOOK.z/16)*16}`);
rcon.cmd(`gamerule spawnRadius 0`);
await new Promise(r => setTimeout(r, 1500));

const cam = mineflayer.createBot({ host: 'localhost', port: 25565, username: 'cambugcam', version: '1.20.4' });
cam.on('error', e => { console.error('cam err', e.message); process.exit(1); });
cam.once('spawn', async () => {
  console.log('cam spawned at', cam.entity.position);
  rcon.cmd(`gamemode spectator cambugcam`);
  await new Promise(r => setTimeout(r, 500));
  rcon.cmd(`tp cambugcam ${CAM.x} ${CAM.y} ${CAM.z}`);
  let synced = false;
  for (let i = 0; i < 20 && !synced; i++) {
    await new Promise(r => setTimeout(r, 500));
    if (Math.abs(cam.entity.position.x - CAM.x) < 3 && Math.abs(cam.entity.position.y - CAM.y) < 3) synced = true;
  }
  logLook('AFTER_TP', cam);

  await cam.lookAt(LOOK);
  await new Promise(r => setTimeout(r, 800));
  logLook('AFTER_LOOKAT', cam);
  // 期望: 朝 LOOK 看. 手算期望 yaw/pitch 对照
  const dx = LOOK.x - cam.entity.position.x, dy = LOOK.y - cam.entity.position.y, dz = LOOK.z - cam.entity.position.z;
  const expYaw = Math.atan2(-dx, -dz); // mineflayer yaw 约定
  const expPitch = Math.atan2(dy, Math.sqrt(dx*dx+dz*dz));
  console.log('EXPECT yaw≈', expYaw.toFixed(4), 'pitch≈', expPitch.toFixed(4));

  pv(cam, { port: VIEWER_PORT, firstPerson: true, viewDistance: 8 });
  console.log('VIEWER_READY on', VIEWER_PORT);
  await new Promise(r => setTimeout(r, 8000));

  const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const browser = await puppeteer.launch({ headless: false, executablePath: CHROME, args: [
    '--no-sandbox', '--enable-webgl', '--ignore-gpu-blocklist',
    '--window-size=1280,720', '--window-position=2000,2000',
  ] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
  await page.goto(`http://localhost:${VIEWER_PORT}`, { waitUntil: 'networkidle2', timeout: 30000 });
  await new Promise(r => setTimeout(r, 7000));
  await page.evaluate(() => { const c = document.querySelector('canvas'); if (c) { c.style.width='1280px'; c.style.height='720px'; c.width=1280; c.height=720; } });
  await new Promise(r => setTimeout(r, 2000));

  // 截图 #1: 原样 (bot 静止, 模拟 bug)
  await page.screenshot({ path: out1, clip: { x:0, y:0, width:1280, height:720 } });
  console.log('SHOT1_BEFORE_SAVED', out1);

  // ---- H1 验证: 强制触发 move 事件, 让 server 重推 position(pos/yaw/pitch) ----
  console.log('--- forcing move emit x10 (re-lookAt each) ---');
  for (let i = 0; i < 10; i++) {
    await cam.lookAt(LOOK);
    cam.emit('move');
    await new Promise(r => setTimeout(r, 300));
  }
  logLook('AFTER_FORCE_MOVE', cam);
  await new Promise(r => setTimeout(r, 2000));

  // 截图 #2: 强制 move 后
  await page.screenshot({ path: out2, clip: { x:0, y:0, width:1280, height:720 } });
  console.log('SHOT2_AFTER_SAVED', out2);

  await browser.close();
  process.exit(0);
});
})();
