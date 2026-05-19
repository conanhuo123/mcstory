// door_anomaly_pov_viewer.js — 一人称任务流样片 (simple_pov_task v1)
// 开门 -> 看到异常 -> 靠近 -> 触发事件 -> 逃跑/反转。单机位第一人称。
// RCON 建场 (端口 25575), 单个 bot 'doorcam' 只做镜头。端口 3019, 不与批量管线冲突。
// 时间轴在 /tmp/_pov_rec_go 文件出现时启动 (录制器写入), 保证录制与剧情精确对齐。
const net = require('net'), fs = require('fs');
const mineflayer = require('mineflayer');
const { Vec3 } = require('vec3');
const { mineflayer: pv } = require('prismarine-viewer');

const VIEWER_PORT = 3019;
const GO = '/tmp/_pov_rec_go';
const VILLAGER = new Vec3(-54.5, 121.9, -181); // 镜头注视点 (村民胸口)

// ---- 极简 RCON 客户端 ----
class Rcon {
  constructor(host, port, pass) { this.host = host; this.port = port; this.pass = pass; this.id = 0; }
  connect() {
    return new Promise((res, rej) => {
      this.sock = net.connect(this.port, this.host, () => this._send(3, this.pass));
      this.sock.once('data', () => res());
      this.sock.on('data', () => {});
      this.sock.on('error', rej);
    });
  }
  _send(type, body) {
    const buf = Buffer.alloc(14 + Buffer.byteLength(body));
    buf.writeInt32LE(10 + Buffer.byteLength(body), 0);
    buf.writeInt32LE(++this.id, 4);
    buf.writeInt32LE(type, 8);
    buf.write(body, 12, 'utf8');
    this.sock.write(buf);
  }
  cmd(s) { try { this._send(2, s.startsWith('/') ? s.slice(1) : s); } catch (e) { console.error('rcon', e.message); } }
}

const rcon = new Rcon('localhost', 25575, 'mcstory123');

rcon.connect().then(() => {
  console.log('RCON connected');
  const C = rcon.cmd.bind(rcon);

  const cam = mineflayer.createBot({ host: 'localhost', port: 25565, username: 'doorcam', version: '1.20.4' });
  cam.on('error', e => console.error('cam err', e.message));
  cam.on('kicked', r => console.error('cam kicked', String(r).slice(0, 120)));

  cam.once('spawn', () => {
    console.log('doorcam spawned');
    pv(cam, { port: VIEWER_PORT, firstPerson: true, viewDistance: 6 });
    console.log('VIEWER_READY');

    // ---- 场景搭建 ----
    const setup = [
      'difficulty peaceful',
      'gamerule doDaylightCycle false',
      'gamerule doWeatherCycle false',
      'gamerule doMobSpawning false',
      'gamerule doFireTick false',
      'time set 6000',
      'weather clear',
      'kill @e[type=villager]',
      'kill @e[type=item]',
      // 清空建造区
      'fill -64 119 -186 -46 132 -166 air',
      // 地板 + 天花板
      'fill -61 120 -185 -49 120 -167 polished_blackstone',
      'fill -61 126 -185 -49 126 -167 deepslate_bricks',
      // 外墙
      'fill -61 121 -185 -61 125 -167 deepslate_bricks',
      'fill -49 121 -185 -49 125 -167 deepslate_bricks',
      'fill -61 121 -167 -49 125 -167 deepslate_bricks',
      'fill -61 121 -185 -49 125 -185 deepslate_bricks',
      // 隔墙 z=-177
      'fill -61 121 -177 -49 125 -177 deepslate_bricks',
      // 门洞
      'setblock -55 121 -177 air',
      'setblock -55 122 -177 air',
      // 木门 (关着)
      'setblock -55 121 -177 oak_door[facing=south,half=lower,hinge=right,open=false]',
      'setblock -55 122 -177 oak_door[facing=south,half=upper,hinge=right,open=false]',
      // 玩家这侧: 暖光, 看清门
      'setblock -55 125 -171 glowstone',
      'setblock -59 123 -170 lantern',
      'setblock -51 123 -170 lantern',
      'setblock -59 123 -174 lantern',
      'setblock -51 123 -174 lantern',
      // 门后房间: 昏暗灵魂灯冷光, 衬出村民
      'setblock -57 121 -183 soul_lantern',
      'setblock -53 121 -183 soul_lantern',
      'setblock -57 121 -179 soul_lantern',
      'setblock -53 121 -179 soul_lantern',
      'setblock -55 121 -184 soul_lantern',
      // 村民: 背对镜头, 一动不动
      'summon minecraft:villager -54.5 121 -181 {Rotation:[180f,0f],NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b}',
      // 镜头 bot
      'gamemode spectator doorcam',
      'tp doorcam -54.5 121 -173 180 2',
    ];
    setup.forEach((c, i) => setTimeout(() => C(c), 300 + i * 110));
    const buildMs = 300 + setup.length * 110 + 1800;

    setTimeout(() => {
      try { cam.lookAt(VILLAGER, true); } catch (e) {}
      console.log('SCENE_READY');
      waitGo(C);
    }, buildMs);
  });

  function waitGo(C) {
    const iv = setInterval(() => {
      if (fs.existsSync(GO)) {
        clearInterval(iv);
        try { fs.unlinkSync(GO); } catch (e) {}
        console.log('GO detected — timeline start');
        runTimeline(C);
      }
    }, 150);
  }

  function runTimeline(C) {
    const look = v => { try { cam.lookAt(v, true); } catch (e) {} };
    const at = (t, fn) => setTimeout(fn, t * 1000);

    // 前推 dolly: 镜头沿 z 轴推近, 始终看村民
    function fwd(z0, z1, dur) {
      const steps = Math.max(1, Math.round(dur / 0.12));
      let i = 0;
      const iv = setInterval(() => {
        i++;
        const z = z0 + (z1 - z0) * (i / steps);
        C(`tp doorcam -54.5 121 ${z.toFixed(2)}`);
        look(VILLAGER);
        if (i >= steps) clearInterval(iv);
      }, 120);
    }
    // 转身: 注视点绕镜头扫过 180 度 (th: PI -> 0)
    function turn(zc0, zc1, dur) {
      const steps = Math.max(1, Math.round(dur / 0.12));
      let i = 0;
      const iv = setInterval(() => {
        i++;
        const k = i / steps;
        const z = zc0 + (zc1 - zc0) * k;
        const th = Math.PI * (1 - k);
        C(`tp doorcam -54.5 121 ${z.toFixed(2)}`);
        look(new Vec3(-54.5 + 6 * Math.sin(th), 122.4, z + 6 * Math.cos(th)));
        if (i >= steps) clearInterval(iv);
      }, 120);
    }

    // 节拍0: 静止, 面对关着的门
    C('tp doorcam -54.5 121 -173 180 2');
    look(VILLAGER);

    // 节拍1 (1.8s): 开门
    at(1.8, () => {
      C('setblock -55 121 -177 oak_door[facing=south,half=lower,hinge=right,open=true]');
      C('setblock -55 122 -177 oak_door[facing=south,half=upper,hinge=right,open=true]');
    });
    // 节拍2 (3.0s): 异常浮现 — 村民发光轮廓 (额外保险)
    at(3.0, () => C('effect give @e[type=villager,limit=1,sort=nearest] glowing 60 0 true'));

    // 节拍3 (6.0s): 靠近 — 第一人称推近, 穿过门洞
    at(6.0, () => fwd(-173, -178.6, 3.2));

    // 节拍4 (9.5s): 触发事件 — 灯光骤亮 + 村民猛转头
    at(9.5, () => {
      C('tp @e[type=villager,limit=1,sort=nearest] -54.5 121 -181 0 0');
      ['-54 125 -181', '-56 125 -181', '-54 125 -179', '-56 125 -179', '-55 125 -182', '-55 125 -180']
        .forEach(p => C(`setblock ${p} glowstone`));
      C('team add anom');
      C('team modify anom color red');
      C('team join anom @e[type=villager,limit=1,sort=nearest]');
      for (let t = 0; t < 2; t += 0.3)
        setTimeout(() => C('particle minecraft:soul_fire_flame -54.5 122 -181 0.4 0.6 0.4 0.05 30 force'), t * 1000);
      look(VILLAGER);
    });

    // 节拍5 (12.0s): 逃跑/反转 — 回头, 门已封死
    at(12.0, () => {
      C('setblock -55 121 -177 deepslate_bricks');
      C('setblock -55 122 -177 oak_wall_sign[facing=south]{front_text:{messages:[\'"出口"\',\'"已消失"\',\'""\',\'""\'],has_glowing_text:1b,color:"red"}}');
      turn(-178.6, -179.8, 1.8);
    });

    console.log('TIMELINE_SCHEDULED');
  }

  setTimeout(() => process.exit(0), 120000);
}).catch(e => { console.error('RCON FATAL', e.message); process.exit(1); });
