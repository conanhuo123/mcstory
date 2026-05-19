// gate1_screenshot.js — 关 1 单点验收
// 用法: node gate1_screenshot.js <camX> <camY> <camZ> <lookX> <lookY> <lookZ> <outPath>
// 假设 build 已通过 RCON 完成. 本脚本只 spawn camera bot + 起 viewer + puppeteer 截图.
const net = require('net');
const mineflayer = require('mineflayer');
const { Vec3 } = require('vec3');
const { mineflayer: pv } = require('prismarine-viewer');
const puppeteer = require('puppeteer');

const [,, cx, cy, cz, lx, ly, lz, out] = process.argv;
const CAM = new Vec3(parseFloat(cx), parseFloat(cy), parseFloat(cz));
const LOOK = new Vec3(parseFloat(lx), parseFloat(ly), parseFloat(lz));
const OUT = out;
const VIEWER_PORT = 3025;

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

(async () => {
await rcon.connect();
console.log('RCON connected');

// 先 setworldspawn + forceload chunks, 然后 cam 重连即在那
rcon.cmd(`setworldspawn ${Math.round(CAM.x)} ${Math.round(CAM.y)} ${Math.round(CAM.z)}`);
rcon.cmd(`forceload add ${Math.floor(CAM.x/16)*16} ${Math.floor(CAM.z/16)*16}`);
rcon.cmd(`forceload add ${Math.floor(LOOK.x/16)*16} ${Math.floor(LOOK.z/16)*16}`);
rcon.cmd(`gamerule spawnRadius 0`);
await new Promise(r => setTimeout(r, 1500));

const cam = mineflayer.createBot({ host: 'localhost', port: 25565, username: 'gate1cam', version: '1.20.4' });
cam.on('error', e => { console.error('cam err', e.message); process.exit(1); });
cam.on('forcedMove', () => console.log('FORCED_MOVE to', cam.entity.position));
cam.once('spawn', async () => {
  console.log('cam spawned at', cam.entity.position);
  // 1) RCON server-side gamemode + tp (不依赖 cam chat)
  rcon.cmd(`gamemode spectator gate1cam`);
  await new Promise(r => setTimeout(r, 500));
  rcon.cmd(`tp gate1cam ${CAM.x} ${CAM.y} ${CAM.z}`);
  // 2) 等 server position packet 回 mineflayer
  let synced = false;
  for (let i = 0; i < 20 && !synced; i++) {
    await new Promise(r => setTimeout(r, 500));
    if (Math.abs(cam.entity.position.x - CAM.x) < 3 && Math.abs(cam.entity.position.y - CAM.y) < 3) synced = true;
  }
  console.log('AFTER_TP cam.pos =', cam.entity.position, 'synced=', synced);
  await cam.lookAt(LOOK);
  await new Promise(r => setTimeout(r, 1000));
  // 3) viewer 在 cam 真到目标后再起 (避免 init 时记 spawn 位置)
  pv(cam, { port: VIEWER_PORT, firstPerson: true, viewDistance: 6 });
  console.log('VIEWER_READY on', VIEWER_PORT);
  await new Promise(r => setTimeout(r, 18000));
  // puppeteer 截图
  // puppeteer headed (WebGL 需要), 窗口移屏外避免抢用户焦点
  const browser = await puppeteer.launch({ headless: false, args: [
    '--no-sandbox',
    '--enable-webgl',
    '--ignore-gpu-blocklist',
    '--window-size=1280,720',
    '--window-position=2000,2000',
  ] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
  await page.goto(`http://localhost:${VIEWER_PORT}`, { waitUntil: 'networkidle2', timeout: 30000 });
  // 等 canvas 真正 init 并渲染 (网络 idle 不等于 GL 渲染完)
  await new Promise(r => setTimeout(r, 6000));
  // 强制 canvas fullscreen 走 page CSS, 防止 320x180 默认 size
  await page.evaluate(() => {
    const c = document.querySelector('canvas');
    if (c) { c.style.width = '1280px'; c.style.height = '720px'; c.width = 1280; c.height = 720; }
  });
  await new Promise(r => setTimeout(r, 3000));
  await page.screenshot({ path: OUT, clip: { x: 0, y: 0, width: 1280, height: 720 } });
  console.log('SCREENSHOT_SAVED', OUT);
  await browser.close();
  process.exit(0);
});
})();
