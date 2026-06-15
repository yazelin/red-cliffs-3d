# 單位外部化(units → data/units.json)設計 — 編輯器轉換 P2d

日期:2026-06-16  狀態:autonomous run;待人工驗收。

## 背景
P2a/P2b 已把 scene/audio 資料化。`U` 單位名冊仍寫死在 index.html:1054-1060(7 個 `new Army|Fleet(id,faction,n[,opts])` + `setLabel(name,generals)`)。P2d 把單位「定義」外部化成 `data/units.json`,讓兵力名冊也可被 AI 編輯。`Army/Fleet/Unit` class(行為)留程式;外部化的是「有哪些單位、陣營/兵種/兵力/名稱/將領」。

## 目標資料 `data/units.json`
```json
{ "units": [
  {"id":"caoMain","kind":"army","faction":"cao","n":60,"name":"曹操本軍","generals":"曹操・張遼・徐晃・于禁"},
  {"id":"caoNavy","kind":"fleet","faction":"cao","n":24,"name":"曹軍水師","generals":"蔡瑁・張允 編練"},
  {"id":"caoRen","kind":"army","faction":"cao","n":20,"name":"江陵守軍","generals":"曹仁・徐晃"},
  {"id":"liuArmy","kind":"army","faction":"liu","n":34,"name":"劉備軍","generals":"劉備・關羽・張飛・趙雲"},
  {"id":"liuFleet","kind":"fleet","faction":"liu","n":5,"name":"江夏水軍","generals":"劉琦・關羽"},
  {"id":"sunFleet","kind":"fleet","faction":"sun","n":14,"name":"周瑜水師","generals":"周瑜・程普・魯肅"},
  {"id":"hgFleet","kind":"fleet","faction":"sun","n":6,"fireShip":true,"name":"黃蓋先鋒","generals":"黃蓋・蒙衝鬥艦十艘"}
] }
```

## 引擎(index.html)
- 頂層載入 `const UNITS = await (await fetch('data/units.json')).json();`(與其他 await 同處)。
- 1054-1060 七行改成迴圈:
```js
for(const u of UNITS.units){
  U[u.id] = u.kind==='army' ? new Army(u.id,u.faction,u.n) : new Fleet(u.id,u.faction,u.n, u.fireShip?{fireShip:true}:{});
  U[u.id].setLabel(u.name, u.generals);
}
```
- 迴圈位置=原七行處(其後 buildChains(U.caoNavy)/attachFire/scene 引用 U.<id> 不變)。Army/Fleet/Unit/setLabel **不動**。

## 契約+SOP+manifest
- `schema/units.schema.json`(units 陣列;item required id/kind(enum army/fleet)/faction(enum cao/sun/liu)/n;選 name/generals/fireShip)。
- validator 加 units(存在、kind/faction enum、id 唯一);`docs/authoring/units.md`。
- `battlefield.json` data 加 `units`。

## 驗證(結構/呼叫等價)
1. units.json 七筆 === 原七行(id/kind/faction/n/name/generals/fireShip 逐一)。
2. 迴圈建出的 U 鍵集 === {caoMain,caoNavy,caoRen,liuArmy,liuFleet,sunFleet,hgFleet};hgFleet 帶 fireShip。
3. scene.json moves / structures camps / dispatchFx ignite 引用的 unit id 都在名冊內。
4. zero 其他變動(Army/Fleet/Unit/setLabel 不動;只換七行→迴圈 + 頂層 await + manifest/schema/validator)。
5. `node tools/validate-data.mjs` PASS(加 units);node --check。
6. 最終 yazelin 跑一遍確認單位/標籤/兵力一致。

## 不做
不動 Army/Fleet 行為、陣型、移動。不抽 repo。
