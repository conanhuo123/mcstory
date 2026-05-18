const net=require('net'),mineflayer=require('mineflayer'),{Vec3}=require('vec3'),{mineflayer:pv}=require('prismarine-viewer'),puppeteer=require('puppeteer');
class R{constructor(h,p,pa){this.host=h;this.port=p;this.pass=pa;this.id=0;}connect(){return new Promise(r=>{this.s=net.connect(this.port,this.host,()=>this._s(3,this.pass));this.s.once('data',()=>r());this.s.on('data',()=>{});});}_s(t,b){const u=Buffer.alloc(14+Buffer.byteLength(b));u.writeInt32LE(10+Buffer.byteLength(b),0);u.writeInt32LE(++this.id,4);u.writeInt32LE(t,8);u.write(b,12,'utf8');this.s.write(u);}cmd(s){this._s(2,s.startsWith('/')?s.slice(1):s);}}
async function ss(out,port){const b=await puppeteer.launch({headless:false,args:['--no-sandbox','--enable-webgl','--ignore-gpu-blocklist','--window-size=1280,720','--window-position=2000,2000','--disable-cache']});const p=await b.newPage();await p.setCacheEnabled(false);await p.setViewport({width:1280,height:720});await p.goto(`http://localhost:${port}`,{waitUntil:'networkidle2',timeout:30000});await new Promise(r=>setTimeout(r,9000));await p.screenshot({path:out});await b.close();console.log('SS',out);}
(async()=>{
  const r=new R('127.0.0.1',25575,'mcstory123');await r.connect();
  r.cmd(`kill @e[type=armor_stand]`);await new Promise(rr=>setTimeout(rr,500));
  // BEFORE: 双臂垂下持斧
  r.cmd(`summon armor_stand -39 81 -240 {ShowArms:1b,NoBasePlate:1b,Invulnerable:1b,Tags:["axswing"],HandItems:[{id:"minecraft:iron_axe",Count:1b},{}],Pose:{RightArm:[0f,0f,0f]},CustomName:'{"text":"executioner"}',CustomNameVisible:1b}`);
  await new Promise(rr=>setTimeout(rr,800));
  const u='swv2'+Date.now().toString().slice(-4);
  const cam=mineflayer.createBot({host:'localhost',port:25565,username:u,version:'1.20.4'});
  cam.once('spawn',async()=>{
    r.cmd(`gamemode spectator ${u}`);await new Promise(rr=>setTimeout(rr,800));
    r.cmd(`tp ${u} -36 82 -239`);
    for(let i=0;i<20;i++){await new Promise(rr=>setTimeout(rr,400));if(Math.abs(cam.entity.position.x+36)<2)break;}
    console.log('cam.pos=',cam.entity.position);
    await cam.lookAt(new Vec3(-39,82,-240));await new Promise(rr=>setTimeout(rr,1500));
    pv(cam,{port:3029,firstPerson:false,viewDistance:6});
    await new Promise(rr=>setTimeout(rr,16000));
    await ss('/Users/coco/mcstory/outputs/single_action_check/REAL_swing_before.png',3029);
    // AFTER: brute-force = kill 旧 + spawn 新 (持斧 + RightArm=-90 已起)
    r.cmd(`kill @e[type=armor_stand,tag=axswing]`);
    await new Promise(rr=>setTimeout(rr,800));
    r.cmd(`summon armor_stand -39 81 -240 {ShowArms:1b,NoBasePlate:1b,Invulnerable:1b,Tags:["axswing"],HandItems:[{id:"minecraft:iron_axe",Count:1b},{}],Pose:{RightArm:[-90f,0f,0f]},CustomName:'{"text":"executioner"}',CustomNameVisible:1b}`);
    await new Promise(rr=>setTimeout(rr,1500));
    // cam 微动触发 viewer refresh
    r.cmd(`tp ${u} -36.3 82 -239`);await new Promise(rr=>setTimeout(rr,800));
    r.cmd(`tp ${u} -36 82 -239`);await new Promise(rr=>setTimeout(rr,1500));
    await cam.lookAt(new Vec3(-39,82,-240));await new Promise(rr=>setTimeout(rr,1500));
    await ss('/Users/coco/mcstory/outputs/single_action_check/REAL_swing_after.png',3029);
    process.exit(0);
  });
})();
