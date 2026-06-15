import { readFileSync } from 'node:fs';
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
for (const [i, b] of (T.bumps || []).entries()) {
  if (!Array.isArray(b.center) || b.center.length !== 2) errs.push(`bump[${i}] center`);
  if (!Array.isArray(b.k) || b.k.length !== 2) errs.push(`bump[${i}] k`);
  if (typeof b.height !== 'number') errs.push(`bump[${i}] height`);
}
for (const [i, s] of (T.colorRamp || []).entries()) if (!/^#[0-9a-fA-F]{6}$/.test(s.color || '')) errs.push(`colorRamp[${i}] color`);
if (errs.length) { console.error('FAIL\n' + errs.join('\n')); process.exit(1); }
console.log(`PASS — factions ${Object.keys(FAC).length}、structures ${S.length}、terrain ${T.rivers.length}河`);
