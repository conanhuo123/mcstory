// pov_recorder.js — headless chrome 录 prismarine-viewer (端口 3019)
// usage: node pov_recorder.js <out.mp4> <duration_s>
// 用 CDP Page.startScreencast 高速截帧 (远快于 page.screenshot), 按真实到达时间合成,
// 输出时长 == 真实时长不变速。流程: 打开页 -> settle -> 写 /tmp/_pov_rec_go (触发 viewer 时间轴)
//          -> 录 DUR 秒 -> ffmpeg concat 合成 30fps raw.mp4
const puppeteer = require('puppeteer');
const fs = require('fs');
const { spawnSync } = require('child_process');

const OUT = process.argv[2] || '/tmp/pov.mp4';
const DUR = parseFloat(process.argv[3] || '15.5');
const PORT = 3019;
const SETTLE = 12000;
const GO = '/tmp/_pov_rec_go';
const TMP = '/tmp/pov_frames_' + Date.now();
fs.mkdirSync(TMP);

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto('http://localhost:' + PORT, { waitUntil: 'domcontentloaded', timeout: 30000 });
  console.log('page loaded, settle ' + SETTLE + 'ms for chunks');
  await new Promise(r => setTimeout(r, SETTLE));

  const client = await page.target().createCDPSession();
  const frames = [];   // {buf, t}
  client.on('Page.screencastFrame', async (ev) => {
    frames.push({ buf: Buffer.from(ev.data, 'base64'), t: Date.now() });
    try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {}
  });

  try { fs.unlinkSync(GO); } catch (e) {}
  fs.writeFileSync(GO, '1');
  console.log('REC_CAPTURE_START');

  await client.send('Page.startScreencast', {
    format: 'jpeg', quality: 80, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1,
  });
  await new Promise(r => setTimeout(r, DUR * 1000));
  try { await client.send('Page.stopScreencast'); } catch (e) {}
  await new Promise(r => setTimeout(r, 300));
  await browser.close();

  if (frames.length < 20) { console.error('REC FATAL too few frames:', frames.length); process.exit(1); }
  const span = (frames[frames.length - 1].t - frames[0].t) / 1000;
  console.log(`captured ${frames.length} frames over ${span.toFixed(2)}s -> ${(frames.length / span).toFixed(2)} fps`);

  // 写帧 + concat 列表 (按真实到达间隔)
  const list = [];
  for (let i = 0; i < frames.length; i++) {
    const fp = `${TMP}/f${String(i).padStart(5, '0')}.jpg`;
    fs.writeFileSync(fp, frames[i].buf);
    list.push(`file '${fp}'`);
    const dt = i < frames.length - 1 ? (frames[i + 1].t - frames[i].t) / 1000 : 0.05;
    list.push(`duration ${Math.max(0.008, dt).toFixed(4)}`);
  }
  list.push(`file '${TMP}/f${String(frames.length - 1).padStart(5, '0')}.jpg'`); // 末帧补一行
  const listFile = `${TMP}/list.txt`;
  fs.writeFileSync(listFile, list.join('\n'));

  const r = spawnSync('/opt/homebrew/bin/ffmpeg', [
    '-y', '-f', 'concat', '-safe', '0', '-i', listFile,
    '-vf', 'scale=1920:1080,fps=30', '-fps_mode', 'cfr',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
    OUT,
  ], { encoding: 'utf8' });
  fs.rmSync(TMP, { recursive: true, force: true });
  if (r.status !== 0) { console.error('ffmpeg fail', (r.stderr || '').slice(-500)); process.exit(1); }
  console.log('raw assembled ->', OUT);
  process.exit(0);
})().catch(e => { console.error('REC FATAL', e.message); process.exit(1); });
