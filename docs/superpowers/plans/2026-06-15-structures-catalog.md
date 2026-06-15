# 赤壁 3D 結構 catalog 化(陣營 + 城池/關口/營寨資料驅動)Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `index.html` 裡硬寫的陣營(`FAC`)與結構(`makeCity`/`makeCamp`/地名 `locLabel`)抽成 `data/factions.json` + `data/structures.json`,renderer 啟動時讀資料用 type→builder registry 建出;並把城池升級成像樣的 3D 模型、新增可擴充的「關口」type 當高價值範例。

**Architecture:** `index.html` 為 `<script type="module">`(line 466,可用 top-level await)。在既有 `FAC` 定義處改為 `await` 載入 `data/factions.json` 並轉色;在既有地名/城池/營寨建立區(:969-983)改為讀 `data/structures.json` 跑統一迴圈,依 `type` 分派到 builder,建好的群組以 `id` 存入 `STRUCT` 查表,並把後續用名字引用的 `campWulin`/`campChibi` 改成 `STRUCT.<id>` 別名以最小化改動。結構/單位仍是同一份 three.js 程式繪製,只是「畫什麼、畫在哪」改由 `data/` 決定。

**Tech Stack:** Three.js r160(CDN importmap,無 build)、原生 `fetch` + top-level await、JSON Schema(契約,放 `schema/`)、無依賴 node 驗證腳本(`tools/validate-data.mjs`)、headless Chrome(MCP DevTools)視覺/console 驗證。

**Spec:** `docs/superpowers/specs/2026-06-15-battlefield-editor-dryrun-design.md`(步驟 1+2)

**發佈紀律(同音訊輪):本機驗到 OK 才 push。** 全程 commit 留本機,起 `python3 -m http.server` 交付 localhost URL 給 yazelin 走一遍,拍板後才 push / 開 PR。

**重要既有掛載點(index.html,行號為 commit `0d97955`):**

| 掛載點 | 位置 | 用途 |
|---|---|---|
| `FAC` 字面量 | :494-498 | 三陣營色/名/旗/css — 改為載入 |
| `flagTexture`/`makeBanner`/`makeShip` | :596 / :619 / :634 | 用 `FAC[...].col` 等 — 須在 FAC 就緒後才被呼叫(都是建場時才呼叫,OK) |
| `makeCity(x,z)` | :790-799 | 城池 box 模型 builder |
| `makeCamp(fac,x,z)` | :800-812 | 營寨 builder(建好 `g.visible=false`) |
| `locLabel(txt,x,z,cls)` | :964 | CSS2D 地名標籤 |
| 城池/地名建立區 | :969-981 | 4 城 `makeCity`+`locLabel`、8 個純地名 `locLabel`、3 個 water 標籤 |
| `campWulin`/`campChibi` 宣告 | :983-984 | `const` 群組,**被下列各處用名字引用** |
| `initPlace()` 重置 | :1016 | `campWulin.visible=false;campChibi.visible=false;` |
| 第七幕事件 | :1119 | `campWulinFire.target=1` |
| 火焰掛載 | :1152 | `attachFire(campWulin,2.2,2)` |
| 點擊/set 分派 | :1589-1592 | `id==='campWulin'`/`'campChibi'` 切 visible |

> 註:水域標籤「長江」用 `RZ(x)` 算 z(:979-980),無法乾淨寫進 JSON,**這 2 個保留在程式**;「漢水」用固定 z=-120,進資料。

---

### Task 1: 抽 `data/factions.json` 並改為載入

**Files:** Create `data/factions.json`;Modify `index.html` :494-498

- [ ] **Step 1.1: 建資料檔** Create `data/factions.json`(色值改存 CSS hex 字串,載入時轉 three.js 數值):

```json
{
  "cao": { "name": "曹軍", "flag": "曹", "css": "cao", "col": "#3d7de0", "dark": "#1d3f78" },
  "sun": { "name": "吳軍", "flag": "孫", "css": "sun", "col": "#d84040", "dark": "#7e2020" },
  "liu": { "name": "劉軍", "flag": "劉", "css": "liu", "col": "#3fae6a", "dark": "#1e5e38" }
}
```

- [ ] **Step 1.2: 改 index.html 載入** 把 :494-498 的 `const FAC={...}` 整段換成:

```js
const FAC = await (async () => {
  const raw = await (await fetch('data/factions.json')).json();
  const out = {};
  for (const [k, v] of Object.entries(raw)) {
    out[k] = { name: v.name, flag: v.flag, css: v.css, hex: v.col,
               col: parseInt(v.col.slice(1), 16), dark: parseInt(v.dark.slice(1), 16) };
  }
  return out;
})();
```

(top-level await 會讓模組其餘程式等資料就緒才執行;`FAC.cao.col` 等於原本的 `0x3d7de0`,`FAC.cao.hex` 等於 `'#3d7de0'`,欄位語意不變。)

- [ ] **Step 1.3: 驗證** 起 `python3 -m http.server 8137 -d /tmp/rc3d`,headless Chrome 開 `http://localhost:8137/`:
  - DevTools console 無錯
  - `evaluate_script`:`FAC.cao.col === 0x3d7de0 && FAC.sun.hex === '#d84040'` → true
  - 截圖:三方軍旗顏色與原本一致(藍/紅/綠)

- [ ] **Step 1.4: Commit**

```bash
git add data/factions.json index.html
git commit -m "refactor(data): 陣營抽成 data/factions.json,renderer 載入轉色"
```

---

### Task 2: 建 `data/structures.json`

**Files:** Create `data/structures.json`

- [ ] **Step 2.1: 建資料檔** 統一陣列、每筆帶 `type`,涵蓋現有 4 城 + 2 營寨 + 7 個地名標記(長江×2 保留在程式,故不在此):

```json
{
  "structures": [
    { "id": "xiangyang", "type": "city", "x": -250, "z": -160, "label": "襄陽", "labelPos": [-250, -148], "labelClass": "big" },
    { "id": "jiangling", "type": "city", "x": -240, "z": -36, "label": "江陵", "labelPos": [-240, -24], "labelClass": "big" },
    { "id": "xiakou",    "type": "city", "x": 162,  "z": -46, "label": "夏口", "labelPos": [164, -36],  "labelClass": "big" },
    { "id": "chaisang",  "type": "city", "x": 272,  "z": 21,  "label": "柴桑", "labelPos": [272, 33],   "labelClass": "big" },

    { "id": "campWulin", "type": "camp", "faction": "cao", "x": -45, "z": -46 },
    { "id": "campChibi", "type": "camp", "faction": "sun", "x": 36,  "z": 44 },

    { "type": "marker", "label": "長坂坡", "x": -150, "z": -104 },
    { "type": "marker", "label": "華容道", "x": -110, "z": -80 },
    { "type": "marker", "label": "烏林",   "x": -45,  "z": -50 },
    { "type": "marker", "label": "赤壁",   "x": 30,   "z": 52, "labelClass": "big" },
    { "type": "marker", "label": "陸口",   "x": 105,  "z": 50 },
    { "type": "marker", "label": "樊口",   "x": 185,  "z": 37 },
    { "type": "marker", "label": "漢水",   "x": 158,  "z": -120, "labelClass": "water" }
  ]
}
```

(座標一字不差來自 :969-981;`labelClass` 對應原 `locLabel` 第四參數,空字串者省略。)

- [ ] **Step 2.2: Commit**

```bash
git add data/structures.json
git commit -m "feat(data): 城池/營寨/地名抽成 data/structures.json"
```

---

### Task 3: catalog 載入 + type→builder registry,取代硬寫呼叫

**Files:** Modify `index.html`(:964 `locLabel` 之後新增載入區;:969-984 整段替換)

- [ ] **Step 3.1: 新增 registry 與建構迴圈** 在 `locLabel` 函式(:964-981 區塊)之後、原 `makeCity(...)` 那串(:969)之前,先把 :969-984 整段(4 個 `makeCity`+`locLabel`、8 個純 `locLabel`、`campWulin`/`campChibi` 兩個 `const`)**刪除**,改成:

```js
/* ════════ structures catalog(資料驅動) ════════ */
const STRUCT_BUILDERS = {
  city: s => makeCity(s.x, s.z),
  camp: s => makeCamp(s.faction, s.x, s.z),
  pass: s => makePass(s.x, s.z),          // Task 4 新增 builder
};
const STRUCT = {};                         // id -> THREE.Group
{
  const data = await (await fetch('data/structures.json')).json();
  for (const s of data.structures) {
    if (s.type === 'marker') { locLabel(s.label, s.x, s.z, s.labelClass || ''); continue; }
    const build = STRUCT_BUILDERS[s.type];
    if (!build) { console.warn('未知結構 type:', s.type, s); continue; }
    const g = build(s);
    if (s.id) STRUCT[s.id] = g;
    if (s.label) locLabel(s.label, (s.labelPos ? s.labelPos[0] : s.x), (s.labelPos ? s.labelPos[1] : s.z), s.labelClass || '');
  }
}
// 保留名字引用(下游 :1016/:1119/:1152/:1589-1592 仍用這兩個變數)
const campWulin = STRUCT.campWulin;
const campChibi = STRUCT.campChibi;
// 水域標籤用 RZ() 算 z,保留在程式
locLabel('長江', -160, RZ(-160), 'water');
locLabel('長江', 210,  RZ(210),  'water');
```

(`makePass` 在 Task 4 才加;在那之前 registry 的 `pass` 不會被觸發,因為 structures.json 尚無 pass 條目——順序安全。)

- [ ] **Step 3.2: 驗證** 重新整理 `http://localhost:8137/`,headless Chrome:
  - console 無錯、無「未知結構 type」warning
  - `evaluate_script`:`Object.keys(STRUCT).sort().join()` === `'campChibi,campWulin,chaisang,jiangling,xiakou,xiangyang'`
  - `evaluate_script`:`campWulin.visible === false && campChibi.visible === false`(初始隱藏,與原行為一致)
  - 截圖逐項比對:4 城、所有地名標籤位置與改動前一致
  - 跑到第七幕(`gotoPhase` 對應幕)確認烏林營寨出現並著火(驗證 `campWulin` 名字引用與 `attachFire(campWulin,...)` :1152 仍有效)

- [ ] **Step 3.3: Commit**

```bash
git add index.html
git commit -m "refactor(render): 結構改 catalog 驅動(type→builder registry + STRUCT 查表)"
```

---

### Task 4: 城池模型升級 + 新增「關口」type(高價值建模)

**Files:** Modify `index.html`(`makeCity` :790-799 改寫;新增 `makePass`);Modify `data/structures.json`(加一座關口)

- [ ] **Step 4.1: 升級城池模型** 把 `makeCity(x,z)`(:790-799)改寫成有城牆 + 四角樓 + 城門 + 中央城樓的 city group(維持 `(x,z)` 簽名、仍 `scene.add(g);return g;`):

```js
function makeCity(x, z) {
  const g = new THREE.Group(); const h = ground(x, z);
  const wallMat = new THREE.MeshLambertMaterial({ color: 0x6b6258 });
  const stoneMat = new THREE.MeshLambertMaterial({ color: 0x555057 });
  const roofMat = new THREE.MeshLambertMaterial({ color: 0x4b3030 });
  const R = 11, WH = 5;                                  // 半邊長、牆高
  // 四面城牆(box,中間留門感:用兩段短牆夾出南面門洞)
  const seg = (w, d, px, pz) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, WH, d), wallMat); m.position.set(px, WH / 2, pz); g.add(m); };
  seg(2 * R, 1.6, 0, -R);                                // 北牆
  seg(2 * R, 1.6, 0, R - 0.0); seg(1.6, 2 * R, -R, 0); seg(1.6, 2 * R, R, 0); // 南/西/東
  // 南牆改開門:覆蓋一段較矮的門楣
  const gate = new THREE.Mesh(new THREE.BoxGeometry(5, 2.2, 1.6), stoneMat); gate.position.set(0, WH - 1.1, R); g.add(gate);
  // 四角樓
  for (const [sx, sz] of [[-R, -R], [R, -R], [-R, R], [R, R]]) {
    const t = new THREE.Mesh(new THREE.BoxGeometry(3.2, WH + 2.5, 3.2), stoneMat); t.position.set(sx, (WH + 2.5) / 2, sz); g.add(t);
    const tr = new THREE.Mesh(new THREE.ConeGeometry(2.6, 1.8, 4), roofMat); tr.position.set(sx, WH + 2.5 + 0.9, sz); tr.rotation.y = Math.PI / 4; g.add(tr);
  }
  // 中央城樓
  const keep = new THREE.Mesh(new THREE.BoxGeometry(6, 5, 6), new THREE.MeshLambertMaterial({ color: 0x666069 }));
  keep.position.y = WH + 2.5; g.add(keep);
  const roof = new THREE.Mesh(new THREE.ConeGeometry(5.2, 3, 4), roofMat);
  roof.position.y = WH + 2.5 + 4; roof.rotation.y = Math.PI / 4; g.add(roof);
  g.position.set(x, h, z); scene.add(g); return g;
}
```

- [ ] **Step 4.2: 新增關口 builder** 在 `makeCity` 之後新增 `makePass(x,z)`(雙樓夾關門 + 連接牆 + 門洞拱):

```js
function makePass(x, z) {
  const g = new THREE.Group(); const h = ground(x, z);
  const stoneMat = new THREE.MeshLambertMaterial({ color: 0x595158 });
  const roofMat = new THREE.MeshLambertMaterial({ color: 0x3f2a2a });
  // 兩側關樓
  for (const sx of [-7, 7]) {
    const tower = new THREE.Mesh(new THREE.BoxGeometry(5, 9, 6), stoneMat); tower.position.set(sx, 4.5, 0); g.add(tower);
    const tr = new THREE.Mesh(new THREE.ConeGeometry(4, 2.4, 4), roofMat); tr.position.set(sx, 9 + 1.2, 0); tr.rotation.y = Math.PI / 4; g.add(tr);
  }
  // 關門上方門楣(兩樓之間,留出下方門洞)
  const lintel = new THREE.Mesh(new THREE.BoxGeometry(9, 2.4, 4), stoneMat); lintel.position.set(0, 8, 0); g.add(lintel);
  // 門洞拱(半圓柱壓扁,純裝飾)
  const arch = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 4, 16, 1, false, 0, Math.PI), roofMat);
  arch.rotation.z = Math.PI / 2; arch.rotation.y = Math.PI / 2; arch.position.set(0, 5, 0); g.add(arch);
  g.position.set(x, h, z); scene.add(g); return g;
}
```

- [ ] **Step 4.3: 在資料加一座關口** 在 `data/structures.json` 的 `structures` 陣列加一筆(華容道隘口,當高價值範例;位置可由 yazelin 後續改資料微調):

```json
{ "id": "huarongPass", "type": "pass", "x": -95, "z": -72, "label": "華容隘口" }
```

(此筆放在 `華容道` marker 之後即可;`pass` 已在 Task 3 registry 註冊。)

- [ ] **Step 4.4: 驗證** 重整 `http://localhost:8137/`,headless Chrome:
  - console 無錯、無未知 type warning
  - `evaluate_script`:`'huarongPass' in STRUCT` → true
  - 截圖:四座城呈現城牆+角樓+城樓(非原本單一 box);華容隘口顯示雙關樓+門洞;原有運鏡/比例未爆掉(城不過大遮畫面)
  - 全片自動播一遍截幾幀,確認新模型在各鏡頭比例合理

- [ ] **Step 4.5: Commit**

```bash
git add index.html data/structures.json
git commit -m "feat(model): 城池升級為城牆/角樓/城樓 + 新增關口 type 與華容隘口"
```

---

### Task 5: schema 契約 + 無依賴驗證腳本

**Files:** Create `schema/factions.schema.json`、`schema/structures.schema.json`、`tools/validate-data.mjs`

- [ ] **Step 5.1: 寫 factions schema** Create `schema/factions.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": {
    "type": "object",
    "required": ["name", "flag", "css", "col", "dark"],
    "properties": {
      "name": { "type": "string" },
      "flag": { "type": "string" },
      "css": { "type": "string" },
      "col": { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$" },
      "dark": { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$" }
    }
  }
}
```

- [ ] **Step 5.2: 寫 structures schema** Create `schema/structures.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["structures"],
  "properties": {
    "structures": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type", "x", "z"],
        "properties": {
          "id": { "type": "string" },
          "type": { "enum": ["city", "camp", "pass", "marker"] },
          "faction": { "enum": ["cao", "sun", "liu"] },
          "x": { "type": "number" },
          "z": { "type": "number" },
          "label": { "type": "string" },
          "labelPos": { "type": "array", "items": { "type": "number" }, "minItems": 2, "maxItems": 2 },
          "labelClass": { "type": "string" }
        },
        "allOf": [
          { "if": { "properties": { "type": { "const": "camp" } } }, "then": { "required": ["faction"] } }
        ]
      }
    }
  }
}
```

- [ ] **Step 5.3: 寫無依賴驗證腳本** Create `tools/validate-data.mjs`(手寫檢查,不裝 ajv;涵蓋 required/型別/enum/camp 必帶 faction/id 唯一):

```js
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
if (errs.length) { console.error('FAIL\n' + errs.join('\n')); process.exit(1); }
console.log(`PASS — factions ${Object.keys(FAC).length}、structures ${S.length}`);
```

- [ ] **Step 5.4: 跑驗證** `node tools/validate-data.mjs` → 預期印 `PASS — factions 3、structures 14`(含 huarongPass)。故意把一筆 `camp` 的 `faction` 刪掉再跑一次應 `FAIL` 並 `exit 1`,確認檢查有效後改回。

- [ ] **Step 5.5: Commit**

```bash
git add schema/ tools/validate-data.mjs
git commit -m "feat(schema): factions/structures JSON schema + 無依賴驗證腳本"
```

---

### Task 6: 整體 headless 迴歸 + README + 本機交付(不 push 直到 OK)

**Files:** Modify `README.md`;檢查全部

- [ ] **Step 6.1: 完整迴歸** headless Chrome 走 `http://localhost:8137/`:
  - console 零錯誤;九幕自動播完無中斷
  - 跳幕 ×5 隨機:城/營/標籤無殘留或錯位;烏林營第七幕著火、`initPlace()` 重置後營寨回隱藏(驗 :1016 名字引用)
  - 點擊烏林營寨(:1589 分派)仍正確開關 visible
  - 與改動前的逐幕截圖對照:除「城池升級、華容隘口新增」外無非預期差異
- [ ] **Step 6.2: 跑資料驗證** `node tools/validate-data.mjs` → PASS
- [ ] **Step 6.3: README** 在「技術」段補一句資料驅動結構;新增小節說明 `data/`(factions/structures)+ `schema/` 契約 + `tools/validate-data.mjs`;實驗記錄補「第三輪:結構 catalog 化(AI 戰場編輯器走查起點)」。Commit:`docs: README 結構資料化說明 + 第三輪實驗記錄`
- [ ] **Step 6.4: 本機交付** 起 `python3 -m http.server 8137 -d /tmp/rc3d`,交付 `http://localhost:8137/` + 精準驗證清單(本次改了什麼→怎麼驗:四城變城牆樣式/華容隘口出現/地名位置不變/烏林營著火與重置/console 無錯/`node tools/validate-data.mjs` PASS)。**不 push**——yazelin 走一遍拍板後,才 push `feat/structures-catalog` 並開 PR。

---

## Self-Review 記錄

- **Spec 覆蓋(步驟 1+2)**:renderer 讀資料骨架(T1,T3)、factions catalog(T1)、structures catalog 含 city/camp/marker(T2,T3)、type→builder registry(T3)、城池高價值建模 + 關口新 type(T4)、schema 契約(T5)、本機驗證 harness + 不 push 紀律(T1.3,T3.2,T4.4,T6)✓。SOP 筆記(「AI 如何新增結構」「如何擴新 type」)在執行收尾隨 README/spec 對照產出,不在本 plan 範圍硬寫。
- **Placeholder 掃描**:無 TBD/TODO;每個改 code 的步驟都附完整程式與確切行號/檔名 ✓。
- **型別/命名一致**:`FAC.<k>.{col,dark,hex,name,flag,css}`、`STRUCT_BUILDERS.{city,camp,pass}`、`STRUCT[id]`、`makeCity(x,z)`/`makeCamp(fac,x,z)`/`makePass(x,z)`、structures 欄位 `{id,type,faction,x,z,label,labelPos,labelClass}` 全文一致 ✓。
- **已知風險**:top-level await 會讓首屏延遲到 fetch 完成(資料極小,可忽略);城池模型放大後可能在某些鏡頭顯大——T4.4/T6.1 截圖檢查比例,過大則調 `R`/`WH` 或 city `scale`;`makePass` 的 `pass` builder 在 Task 3 已註冊但 Task 4 才定義,故 Task 3 階段 structures.json 不可有 pass 條目(已確保 huarongPass 在 T4.3 才加入)。
