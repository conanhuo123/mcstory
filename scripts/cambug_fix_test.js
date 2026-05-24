// cambug_fix_test.js — 验证双根因修复:
//   (A) bot.physicsEnabled=false + 钉死 entity.position → 停止坠落
//   (B) puppeteer 连上后 emit('move') → 相机就位+朝向
// 用法: node cambug_fix_test.js <camX> <camY> <camZ> <lookX> <lookY> <lookZ> <out>
const net = require('net');
const mineflayer = require('mineflayer');
const { Vec3 } = require('vec3');
const { mineflayer: pv } = require('prismarine-viewer');
const puppeteer = require('puppeteer');

const [,, cx, cy, cz, lx, ly, lz, out] = process.argv;
const CAM = new Vec3(parseFloat(cx), parseFloat(cy), parseFloat(cz));
const LOOK = new Vec3(parseFloat(lx), parseFloat(ly), parseFloat(lz));
const VIEWER_PORT = 3027;

class Rcon {
  constructor(h,p,pw){this.host=h;this.port=p;this.pass=pw;this.id=0;}
  connect(){return new Promise((res,rej)=>{this.sock=net.connect(this.port,this.host,()=>this._send(3,this.pass));this.sock.once('data',()=>res());this.sock.on('data',()=>{});this.sock.on('error',rej);});}
  _send(t,b){const buf=Buffer.alloc(14+Buffer.byteLength(b));buf.writeInt32LE(10+Buffer.byteLength(b),0);buf.writeInt32LE(++this.id,4);buf.writeInt32LE(t,8);buf.write(b,12,'utf8');this.sock.write(buf);}
  cmd(s){this._send(2,s.startsWith('/')?s.slice(1):s);}
}
const rcon = new Rcon('127.0.0.1',25575,'mcstory123');
const sleep = ms => new Promise(r=>setTimeout(r,ms));
const L = (t,c)=>console.log(`[${t}] pos=`,c.entity.position,'yaw=',c.entity.yaw.toFixed(3),'pitch=',c.entity.pitch.toFixed(3));

(async () => {
await rcon.connect(); console.log('RCON connected');
rcon.cmd(`forceload add ${Math.floor(CAM.x/16)*16} ${Math.floor(CAM.z/16)*16}`);
rcon.cmd(`forceload add ${Math.floor(LOOK.x/16)*16} ${Math.floor(LOOK.z/16)*16}`);
await sleep(1200);

const cam = mineflayer.createBot({ host:'localhost', port:25565, username:'camfix', version:'1.20.4' });
cam.on('error', e=>{console.error('err',e.message);process.exit(1);});
cam.once('spawn', async () => {
  console.log('spawned at', cam.entity.position);
  rcon.cmd(`gamemode spectator camfix`);
  await sleep(400);
  rcon.cmd(`tp camfix ${CAM.x} ${CAM.y} ${CAM.z}`);
  await sleep(800);

  // (A) 关物理 + 钉死本地坐标 (viewer 读这个)
  cam.physicsEnabled = false;
  cam.entity.position.set(CAM.x, CAM.y, CAM.z);
  await cam.lookAt(LOOK);
  L('AFTER_FIX_SETUP', cam);

  pv(cam, { port: VIEWER_PORT, firstPerson: true, viewDistance: 8 });
  console.log('VIEWER_READY', VIEWER_PORT);
  await sleep(7000);

  const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const browser = await puppeteer.launch({ headless:false, executablePath:CHROME, args:[
    '--no-sandbox','--enable-webgl','--ignore-gpu-blocklist','--window-size=1280,720','--window-position=2000,2000' ]});
  const page = await browser.newPage();
  await page.setViewport({ width:1280, height:720, deviceScaleFactor:1 });
  await page.goto(`http://localhost:${VIEWER_PORT}`, { waitUntil:'networkidle2', timeout:30000 });
  await sleep(6000);
  await page.evaluate(()=>{const c=document.querySelector('canvas');if(c){c.style.width='1280px';c.style.height='720px';c.width=1280;c.height=720;}});

  // (B) 连上后: 重钉坐标+朝向, emit move 把正确 position 推给已连 socket
  for (let i=0;i<6;i++){
    cam.entity.position.set(CAM.x, CAM.y, CAM.z);
    await cam.lookAt(LOOK);
    cam.entity.position.set(CAM.x, CAM.y, CAM.z); // lookAt 可能微调, 再钉
    cam.emit('move');
    await sleep(300);
  }
  L('BEFORE_SHOT', cam);
  await sleep(1500);
  await page.screenshot({ path: out, clip:{x:0,y:0,width:1280,height:720} });
  console.log('SHOT_SAVED', out);
  await browser.close();
  process.exit(0);
});
})();
