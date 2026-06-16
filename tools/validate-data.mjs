import { readFileSync, existsSync } from 'node:fs';
const read = p => JSON.parse(readFileSync(new URL(p, import.meta.url)));
let errs = [];
const FAC = read('../data/factions.json');
for (const [k, v] of Object.entries(FAC)) {
  for (const f of ['name', 'flag', 'css', 'col', 'dark']) if (!(f in v)) errs.push(`factions.${k} 缺 ${f}`);
  for (const f of ['col', 'dark']) if (v[f] && !/^#[0-9a-fA-F]{6}$/.test(v[f])) errs.push(`factions.${k}.${f} 非 #RRGGBB`);
}
const S = read('../data/structures.json').structures;
const TYPES = ['city', 'camp', 'pass', 'marker'], ids = new Set();
S.forEach((s, i) => {
  if (!TYPES.includes(s.type)) errs.push(`structures[${i}] type 非法: ${s.type}`);
  for (const f of ['x', 'z']) if (typeof s[f] !== 'number') errs.push(`structures[${i}] ${f} 非數字`);
  if (s.type === 'camp' && !['cao', 'sun', 'liu'].includes(s.faction)) errs.push(`structures[${i}] camp 缺 faction`);
  if (s.id) { if (ids.has(s.id)) errs.push(`重複 id: ${s.id}`); ids.add(s.id); }
});
const T = read('../data/terrain.json');
if (!Array.isArray(T.rivers) || !T.rivers.length) errs.push('terrain 缺 rivers');
for (const [i, r] of (T.rivers || []).entries()) {
  if (!Array.isArray(r.centerline) || r.centerline.length < 2) errs.push(`river[${i}] centerline 不足`);
  for (const f of ['halfWidth', 'depth']) if (typeof r[f] !== 'number') errs.push(`river[${i}] ${f} 非數`);
}
const xy2 = a => Array.isArray(a) && a.length === 2 && a.every(n => typeof n === 'number');
for (const [i, b] of (T.bumps || []).entries()) {
  if (!xy2(b.center)) errs.push(`bump[${i}] center`);
  if (!xy2(b.radius) && !xy2(b.k)) errs.push(`bump[${i}] 需 radius 或 k`);
  if (typeof b.height !== 'number') errs.push(`bump[${i}] height`);
}
for (const [i, rg] of (T.regions || []).entries()) {
  if (!xy2(rg.center)) errs.push(`region[${i}] center`);
  if (!xy2(rg.radius) && !xy2(rg.k)) errs.push(`region[${i}] 需 radius 或 k`);
}
for (const [i, s] of (T.colorRamp || []).entries()) if (!/^#[0-9a-fA-F]{6}$/.test(s.color || '')) errs.push(`colorRamp[${i}] color`);
const BF = read('../data/battlefield.json');
for (const f of ['name', 'era', 'data']) if (!(f in BF)) errs.push(`battlefield 缺 ${f}`);
if (BF.meta && !(BF.meta.finale && BF.meta.finale.title)) errs.push('battlefield.meta.finale.title 缺');
for (const [k, p] of Object.entries(BF.data || {})) {
  if (typeof p !== 'string') { errs.push(`battlefield.data.${k} 非路徑字串`); continue; }
  // manifest paths are resolved relative to the manifest dir (data/), mirroring the engine's PKG_BASE
  if (!existsSync(new URL('../data/' + p, import.meta.url))) errs.push(`battlefield.data.${k} 路徑不存在: ${p}`);
}
const FX_TYPES = ['volley', 'ignite', 'shake', 'campFire'];
let acts = [];
if (!existsSync(new URL('../data/scene.json', import.meta.url))) {
  errs.push('scene.json 不存在');
} else {
  const SCENE = read('../data/scene.json');
  acts = SCENE.acts;
  if (!Array.isArray(acts) || !acts.length) errs.push('scene.acts 非非空陣列');
  else acts.forEach((a, i) => {
    for (const f of ['key', 'title', 'dur', 'env']) if (!(f in a)) errs.push(`scene.acts[${i}] 缺 ${f}`);
    (a.fx || []).forEach((e, j) => {
      if (typeof e.at !== 'number') errs.push(`scene.acts[${i}].fx[${j}] at 非數`);
      if (!FX_TYPES.includes(e.type)) errs.push(`scene.acts[${i}].fx[${j}] type 非法: ${e.type}`);
    });
  });
}
const AUDIO_CUE_TYPES = ['synth', 'sfx', 'sword', 'burst'];
let audioCueCount = 0;
if (!existsSync(new URL('../data/audio.json', import.meta.url))) {
  errs.push('audio.json 不存在');
} else {
  const AUDIO = read('../data/audio.json');
  const scenes = AUDIO.music?.scenes;
  if (!Array.isArray(scenes) || !scenes.length) errs.push('audio.music.scenes 非非空陣列');
  else scenes.forEach((p, i) => {
    if (typeof p !== 'string') { errs.push(`audio.music.scenes[${i}] 非路徑字串`); return; }
    if (!existsSync(new URL('../' + p, import.meta.url))) errs.push(`audio.music.scenes[${i}] 路徑不存在: ${p}`);
  });
  for (const [scene, list] of Object.entries(AUDIO.cues || {})) {
    (list || []).forEach((e, j) => {
      audioCueCount++;
      if (typeof e.at !== 'number') errs.push(`audio.cues[${scene}][${j}] at 非數`);
      if (!AUDIO_CUE_TYPES.includes(e.type)) errs.push(`audio.cues[${scene}][${j}] type 非法: ${e.type}`);
    });
  }
}
const UNIT_KINDS = ['army', 'fleet'], UNIT_FACTIONS = ['cao', 'sun', 'liu'];
let unitCount = 0;
if (!existsSync(new URL('../data/units.json', import.meta.url))) {
  errs.push('units.json 不存在');
} else {
  const UNITS = read('../data/units.json');
  const units = UNITS.units;
  if (!Array.isArray(units) || !units.length) errs.push('units.units 非非空陣列');
  else {
    const uids = new Set();
    units.forEach((u, i) => {
      unitCount++;
      for (const f of ['id', 'kind', 'faction', 'n']) if (!(f in u)) errs.push(`units[${i}] 缺 ${f}`);
      if (!UNIT_KINDS.includes(u.kind)) errs.push(`units[${i}] kind 非法: ${u.kind}`);
      if (!UNIT_FACTIONS.includes(u.faction)) errs.push(`units[${i}] faction 非法: ${u.faction}`);
      if (typeof u.n !== 'number') errs.push(`units[${i}] n 非數字`);
      if (u.id) { if (uids.has(u.id)) errs.push(`重複 unit id: ${u.id}`); uids.add(u.id); }
    });
  }
}
if (errs.length) { console.error('FAIL\n' + errs.join('\n')); process.exit(1); }
console.log(`PASS — factions ${Object.keys(FAC).length}、structures ${S.length}、terrain ${T.rivers.length}河、battlefield、scene ${acts.length}幕、audio ${audioCueCount}cue、units ${unitCount}`);
