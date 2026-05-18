const net = require('net');
const mineflayer = require('mineflayer');
const { Vec3 } = require('vec3');
const { mineflayer: pv } = require('prismarine-viewer');
const puppeteer = require('puppeteer');

class Rcon {
  constructor(h,p,pa){this.host=h;this.port=p;this.pass=pa;this.id=0;}
  connect(){return new Promise(r=>{this.sock=net.connect(this.port,this.host,()=>this._s(3,this.pass));this.sock.once('data',()=>r());this.sock.on('data',()=>{});});}
  _s(t,b){const buf=Buffer.alloc(14+Buffer.byteLength(b));buf.writeInt32LE(10+Buffer.byteLength(b),0);buf.writeInt32LE(++this.id,4);buf.writeInt32LE(t,8);buf.write(b,12,'utf8');this.sock.write(buf);}
  cmd(s){this._s(2,s.startsWith('/')?s.slice(1):s);}
}
async function ss(out, port) {
  const b = await puppeteer.launch({headless:false, args:['--no-sandbox','--enable-webgl','--ignore-gpu-blocklist','--window-size=1280,720','--window-position=2000,2000','--disable-cache']});
  const p = await b.newPage();
  await p.setCacheEnabled(false);
  await p.setViewport({width:1280,height:720});
  await p.goto(`http://localhost:${port}`, {waitUntil:'networkidle2', timeout:30000});
  await new Promise(r => setTimeout(r, 10000));
  await p.screenshot({path: out});
  await b.close();
  console.log('SS', out);
}
(async () => {
  const r = new Rcon('127.0.0.1', 25575, 'mcstory123'); await r.connect();
  // 确保 villager 存在
  r.cmd(`kill @e[type=villager]`);
  await new Promise(rr => setTimeout(rr, 500));
  r.cmd(`summon villager -40 81 -240 {NoAI:1b,Silent:1b,PersistenceRequired:1b,Invulnerable:1b,CustomName:'{"text":"继任者"}',CustomNameVisible:1b,Rotation:[0.0f,0.0f]}`);
  await new Promise(rr => setTimeout(rr, 500));

  const u = 'tpc' + Date.now().toString().slice(-5);
  const cam = mineflayer.createBot({host:'localhost',port:25565,username:u,version:'1.20.4'});
  cam.once('spawn', async () => {
    console.log('spawn', cam.entity.position);
    r.cmd(`gamemode spectator ${u}`);
    await new Promise(rr => setTimeout(rr, 800));
    r.cmd(`tp ${u} -36 82 -240`);
    for (let i=0; i<20; i++) {
      await new Promise(rr => setTimeout(rr, 400));
      if (Math.abs(cam.entity.position.x+36) < 2) break;
    }
    console.log('cam.pos =', cam.entity.position);
    await cam.lookAt(new Vec3(-40, 81, -240));
    await new Promise(rr => setTimeout(rr, 1500));
    // 关键: firstPerson=false (第三人称, viewer 渲染所有 entity)
    pv(cam, {port: 3027, firstPerson: false, viewDistance: 6});
    console.log('VIEWER 3027');
    await new Promise(rr => setTimeout(rr, 16000));  // 给 entity texture load 更多时间
    await ss('/Users/coco/mcstory/outputs/gate1_judge_death_min/v_thirdperson_before.png', 3027);
    // villager pitch=45
    r.cmd(`tp @e[type=villager,name="继任者",limit=1] -40 81 -240 0 45`);
    await new Promise(rr => setTimeout(rr, 1500));
    // cam 微动
    r.cmd(`tp ${u} -36.2 82 -240`);
    await new Promise(rr => setTimeout(rr, 800));
    r.cmd(`tp ${u} -36 82 -240`);
    await new Promise(rr => setTimeout(rr, 1500));
    await cam.lookAt(new Vec3(-40, 81, -240));
    await new Promise(rr => setTimeout(rr, 1000));
    await ss('/Users/coco/mcstory/outputs/gate1_judge_death_min/v_thirdperson_after.png', 3027);
    process.exit(0);
  });
})();
