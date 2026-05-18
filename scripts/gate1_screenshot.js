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

const cam = mineflayer.createBot({ host: 'localhost', port: 25565, username: 'gate1cam', version: '1.20.4' });
cam.on('error', e => { console.error('cam err', e.message); process.exit(1); });
cam.once('spawn', async () => {
  console.log('cam spawned at', cam.entity.position);
  // RCON tp + gamemode spectator + chunks force-loaded
  rcon.cmd(`gamemode spectator gate1cam`);
  rcon.cmd(`tp gate1cam ${CAM.x} ${CAM.y} ${CAM.z}`);
  await new Promise(r => setTimeout(r, 2500));
  console.log('after tp cam.pos =', cam.entity.position);
  await cam.lookAt(LOOK);
  await new Promise(r => setTimeout(r, 1000));
  pv(cam, { port: VIEWER_PORT, firstPerson: true, viewDistance: 8 });
  console.log('VIEWER_READY on', VIEWER_PORT);
  await new Promise(r => setTimeout(r, 15000));
  // puppeteer 截图
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox','--disable-gpu'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720 });
  await page.goto(`http://localhost:${VIEWER_PORT}`, { waitUntil: 'networkidle2', timeout: 30000 });
  await new Promise(r => setTimeout(r, 4000));
  await page.screenshot({ path: OUT });
  console.log('SCREENSHOT_SAVED', OUT);
  await browser.close();
  process.exit(0);
});
})();
