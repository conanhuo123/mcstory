// orbit_video.js — 关5 端到端: 相机环绕建筑多帧截图 (复用单 session)
// 用法: node orbit_video.js <cx> <cy> <cz> <radius> <frames> <outDir>
// 用修好的相机机制: physicsEnabled=false 钉坐标 + 每帧 emit('move') 推 pos/yaw/pitch
const net = require('net');
const fs = require('fs');
const path = require('path');
const mineflayer = require('mineflayer');
const { Vec3 } = require('vec3');
const { mineflayer: pv } = require('prismarine-viewer');
const puppeteer = require('puppeteer');

const [,, cx, cy, cz, radius, frames, outDir] = process.argv;
const CX = parseFloat(cx), CY = parseFloat(cy), CZ = parseFloat(cz);
const R = parseFloat(radius), N = parseInt(frames);
fs.mkdirSync(outDir, { recursive: true });
const VIEWER_PORT = 3040;
const sleep = ms => new Promise(r => setTimeout(r, ms));

class Rcon {
  constructor(h,p,pw){this.host=h;this.port=p;this.pass=pw;this.id=0;}
  connect(){return new Promise((res,rej)=>{this.sock=net.connect(this.port,this.host,()=>this._send(3,this.pass));this.sock.once('data',()=>res());this.sock.on('data',()=>{});this.sock.on('error',rej);});}
  _send(t,b){const buf=Buffer.alloc(14+Buffer.byteLength(b));buf.writeInt32LE(10+Buffer.byteLength(b),0);buf.writeInt32LE(++this.id,4);buf.writeInt32LE(t,8);buf.write(b,12,'utf8');this.sock.write(buf);}
  cmd(s){this._send(2,s.startsWith('/')?s.slice(1):s);}
}
const rcon = new Rcon('127.0.0.1',25575,'mcstory123');

(async () => {
await rcon.connect(); console.log('RCON connected');
// forceload 环绕区
for (const a of [0, 90, 180, 270]) {
  const px = CX + R*Math.cos(a*Math.PI/180), pz = CZ + R*Math.sin(a*Math.PI/180);
  rcon.cmd(`forceload add ${Math.floor(px/16)*16} ${Math.floor(pz/16)*16}`);
}
const cam = mineflayer.createBot({ host:'localhost', port:25565, username:'orbitcam', version:'1.20.4' });
cam.on('error', e=>{console.error('err',e.message);process.exit(1);});
await new Promise(res => cam.once('spawn', res));
console.log('spawned');
rcon.cmd('gamemode spectator orbitcam');
await sleep(500);
cam.physicsEnabled = false;

const CTR = new Vec3(CX, CY, CZ);
// 起 viewer + browser 一次
pv(cam, { port: VIEWER_PORT, firstPerson: true, viewDistance: 10 });
console.log('VIEWER_READY', VIEWER_PORT);
await sleep(2500);
const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser = await puppeteer.launch({ headless:false, executablePath:CHROME, args:[
  '--no-sandbox','--enable-webgl','--ignore-gpu-blocklist','--window-size=1280,720','--window-position=2000,2000' ]});
const page = await browser.newPage();
await page.setViewport({ width:1280, height:720, deviceScaleFactor:1 });
// domcontentloaded (不用 networkidle2: socket.io 持续推流永不 idle → 会 hang)
await page.goto(`http://localhost:${VIEWER_PORT}`, { waitUntil:'domcontentloaded', timeout:30000 });
await sleep(5000);
await page.evaluate(()=>{const c=document.querySelector('canvas');if(c){c.style.width='1280px';c.style.height='720px';c.width=1280;c.height=720;}});

for (let i=0;i<N;i++){
  const ang = 2*Math.PI*i/N;
  const camx = CX + R*Math.cos(ang), camz = CZ + R*Math.sin(ang), camy = CY + R*0.3;
  rcon.cmd(`tp orbitcam ${camx.toFixed(1)} ${camy.toFixed(1)} ${camz.toFixed(1)}`);
  await sleep(150);
  // 钉坐标 + 朝中心 + emit move (修复核心), 重复几次确保推送
  for (let k=0;k<4;k++){
    cam.entity.position.set(camx, camy, camz);
    await cam.lookAt(CTR);
    cam.entity.position.set(camx, camy, camz);
    cam.emit('move');
    await sleep(120);
  }
  await sleep(i<3 ? 2500 : 900);  // 前几帧多等区块加载
  const fp = path.join(outDir, `frame_${String(i).padStart(3,'0')}.png`);
  await page.screenshot({ path: fp, clip:{x:0,y:0,width:1280,height:720} });
  console.log('FRAME', i, '@', camx.toFixed(0),camy.toFixed(0),camz.toFixed(0));
}
console.log('FRAMES_DONE', N);
await browser.close();
process.exit(0);
})();
