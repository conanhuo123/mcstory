// simple_pov_viewer.js — death_sentence 极简样片 (RCON 版, 不抢占 camera/director 名)
// 单一固定机位(第三人称) + 轻微推近; 处刑者三步动作: 举斧/停手/看牌子; 字幕 3 句.
// 用 RCON 跑特权命令, bot 仅做 prismarine-viewer 与挥斧动画, 故可与批量管线并存.
const net = require('net');
const mineflayer = require('mineflayer');
const { Vec3 } = require('vec3');
const { mineflayer: pv } = require('prismarine-viewer');

const VIEWER_PORT = 3017;
const VILLAGER = new Vec3(-54.5, 122.2, -177); // 镜头注视点

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

  const cam = mineflayer.createBot({ host: 'localhost', port: 25565, username: 'povcam', version: '1.20.4' });
  cam.on('error', e => console.error('cam err', e.message));

  cam.once('spawn', () => {
    console.log('povcam spawned');
    pv(cam, { port: VIEWER_PORT, firstPerson: true, viewDistance: 8 });
    console.log('VIEWER_READY');

    setTimeout(() => {
    const exec = mineflayer.createBot({ host: 'localhost', port: 25565, username: 'povexec', version: '1.20.4' });
    exec.on('error', e => console.error('exec err', e.message));
    exec.on('kicked', r => console.error('exec kicked', String(r).slice(0, 120)));
    exec.on('end', r => console.error('exec end', String(r).slice(0, 80)));
    exec.on('login', () => console.log('povexec login'));

    exec.once('spawn', () => {
      console.log('povexec spawned');
      const C = rcon.cmd.bind(rcon);

      // ---- 场景搭建 ----
      const setup = [
        'difficulty peaceful',
        'gamerule doDaylightCycle false',
        'gamerule doMobSpawning false',
        'gamerule doWeatherCycle false',
        'time set 6000',
        'weather clear',
        'fill -64 119 -185 -46 132 -166 air',
        'fill -60 120 -181 -50 120 -172 polished_blackstone',
        'fill -60 121 -181 -50 125 -181 deepslate_bricks',
        'fill -60 121 -181 -60 124 -172 deepslate_bricks',
        'fill -50 121 -181 -50 124 -172 deepslate_bricks',
        'fill -56 121 -179 -53 121 -176 polished_blackstone',
        'setblock -56 122 -177 iron_bars',
        'setblock -56 123 -177 iron_bars',
        'setblock -53 122 -177 iron_bars',
        'setblock -53 123 -177 iron_bars',
        'setblock -59 121 -173 lantern',
        'setblock -51 121 -173 lantern',
        'setblock -59 122 -180 lantern',
        'setblock -51 122 -180 lantern',
        'setblock -55 123 -180 oak_wall_sign[facing=south]',
        'summon villager -54.5 121 -177 {Rotation:[0f,0f],NoAI:1b}',
        'gamemode adventure povexec',
        'tp povexec -56.5 121 -174.5 -141 -5',
        'item replace entity povexec weapon.mainhand with minecraft:iron_axe',
        'gamemode spectator povcam',
        'tp povcam -55 122 -169 180 5',
      ];
      setup.forEach((c, i) => setTimeout(() => C(c), 200 + i * 120));
      const buildMs = 200 + setup.length * 120 + 1500;

      setTimeout(() => {
        try { cam.lookAt(VILLAGER, true); } catch (e) {}
        try { exec.lookAt(new Vec3(-54.5, 122, -177), true); } catch (e) {}
        console.log('SCENE_READY');

        const BASE = 19000; // recorder 开录后才进时间轴
        const at = (t, fn) => setTimeout(fn, BASE + t * 1000);
        const camMove = z => { C(`tp povcam -55 122 ${z} 180 5`); setTimeout(() => { try { cam.lookAt(VILLAGER, true); } catch (e) {} }, 450); };
        const sub = (text, a, b) => {
          for (let t = a; t < b; t += 0.6)
            at(t, () => C(`title @a actionbar {"text":"${text}","color":"white","bold":true}`));
        };

        // 镜头: 固定机位 + 3 步轻微推近
        at(0, () => camMove(-169));
        at(6.5, () => camMove(-171));
        at(11, () => camMove(-173));

        // 节拍1 字幕「处决台」— 静态画面交代场景
        sub('处决台', 0, 5.3);

        // 节拍2 举斧 — 连续挥斧 t=3.5~6
        for (let t = 3.5; t < 6; t += 0.5) at(t, () => { try { exec.swingArm('right'); } catch (e) {} });

        // 节拍3 停手 + 村民发光求饶 + 字幕「别杀我」
        at(6, () => C('effect give @e[type=villager,limit=1,sort=nearest] glowing 9 0 true'));
        sub('别杀我', 6, 10.6);

        // 节拍4 看牌子 — 处刑者转头看告示牌
        at(10, () => { try { exec.look(-164 * Math.PI / 180, -4 * Math.PI / 180, true); } catch (e) {} });

        // 反转 告示牌浮字 + 字幕「上一任服主」
        at(12, () => C('setblock -55 123 -180 oak_wall_sign[facing=south]{front_text:{messages:[\'"上一任服主"\',\'"villager_42"\',\'""\',\'""\'],has_glowing_text:1b,color:"red"}}'));
        sub('上一任服主', 12, 19.0);

        console.log('TIMELINE_SCHEDULED');
      }, buildMs);
    });
    }, 5000);
  });

  setTimeout(() => process.exit(0), 140000);
}).catch(e => { console.error('RCON FATAL', e.message); process.exit(1); });
