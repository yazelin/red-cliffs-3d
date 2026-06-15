# 參數化類比地形 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `index.html` 的 `ground()`(類比地形)+ 上色迴圈改成讀 `data/terrain.json`(可組合特徵庫:rivers/bumps/bands/regions/colorRamp)的生成器,數值上重現現有地形(因此不震動既有結構/艦隊/運鏡),作為 AI 戰場編輯器「參數化類比地形」格式的第一個實作 + 驗證。

**Architecture:** 新增 `terrainHeight(x,z)` / `terrainColor(x,z)` 生成器,組合 terrain.json 的特徵;`ground()` 變成 `terrainHeight` 薄包裝(其他呼叫點不動)。先在 node 工具(`tools/terrain-fit.mjs`)裡同時放「原 ground() 移植」與「生成器移植」,把 terrain.json 調到 `terrainHeight ≈ ground()`(快速數值迭代),再移植進 index.html。

**Tech Stack:** Three.js r160(CDN importmap,無 build)、原生 fetch + top-level await、零依賴 node dev 工具(數值擬合/驗證)。本 repo 既有驗證方式:數值比對 + headless 載入檢查(地形貼合可純數值驗,不需截圖)。

**Spec:** `docs/superpowers/specs/2026-06-15-parametric-terrain-design.md`

**發佈紀律:本機驗到 OK 才 push。** commit 留本機(branch `feat/parametric-terrain`),交付給 yazelin 驗收後才 push + PR。

**既有掛載點(index.html,實作前 grep 確認):**
| 點 | 約略行 | 用途 |
|---|---|---|
| `RZ(x)=18*sin(0.012x)-0.12x` | :472 | 長江中心線(水標籤也用)|
| `fbm(x,y)` | :477 | value-noise FBM(生成器沿用)|
| `function ground(x,z)` | :478-488 | 類比地形 → 改薄包裝 |
| 地形網格 + 上色迴圈 | :534-559 | `PlaneGeometry(680,460,200,140)` 逐頂點 `ground()` + 色帶/紅崖/沼澤 tint |

原 `ground()` 與上色見 spec「現有特徵」節(實作以此為擬合基準)。

---

### Task 1: node 擬合工具 + `data/terrain.json`(調到數值重現 ground())

**Files:** Create `tools/terrain-fit.mjs`、`data/terrain.json`

- [ ] **Step 1.1: 寫擬合工具骨架** Create `tools/terrain-fit.mjs`,內含(a)原 ground() 移植,(b)生成器移植,(c)讀 data/terrain.json,(d)密格比對。先放原函式:

```js
import { readFileSync } from 'node:fs';
// ---- 原 ground() 移植(擬合基準) ----
const hash=(x,y)=>{const s=Math.sin(x*127.1+y*311.7)*43758.5453;return s-Math.floor(s);};
function vnoise(x,y){const xi=Math.floor(x),yi=Math.floor(y),xf=x-xi,yf=y-yi;
  const tl=hash(xi,yi),tr=hash(xi+1,yi),bl=hash(xi,yi+1),br=hash(xi+1,yi+1);
  const u=xf*xf*(3-2*xf),v=yf*yf*(3-2*yf);
  return tl*(1-u)*(1-v)+tr*u*(1-v)+bl*(1-u)*v+br*u*v;}
function fbm(x,y){let a=0,amp=1,f=1,t=0;for(let i=0;i<4;i++){a+=vnoise(x*f,y*f)*amp;t+=amp;amp*=.5;f*=2;}return a/t;}
const RZ=x=>18*Math.sin(x*0.012)-x*0.12;
function ground(x,z){const zc=RZ(x);let d=Math.abs(z-zc);const zr=RZ(150);
  if(z<zr){const xt=150-(zr-z)*0.10;d=Math.min(d,Math.abs(x-xt)*2.6);}
  let h; if(d<34)h=-7*(1-d/34);
  else{const t=d-34;h=Math.min(t*0.18,4)+fbm(x*0.013+5,z*0.013)*Math.min(t*0.14,16);}
  h+=Math.max(0,Math.abs(z)-118)*0.22*(0.4+fbm(x*0.02,z*0.02+7));
  h+=24*Math.exp(-(((x-30)**2)/700+((z-44)**2)/180)); return h;}
export { fbm, ground, RZ };
```

- [ ] **Step 1.2: 生成器移植(與 index.html 將用的同一套邏輯)** 加入 `tools/terrain-fit.mjs`:

```js
function distSeg(px,pz,a,b){const vx=b[0]-a[0],vz=b[1]-a[1];const wx=px-a[0],wz=pz-a[1];
  const L=vx*vx+vz*vz||1e-9;let t=(wx*vx+wz*vz)/L;t=Math.max(0,Math.min(1,t));
  const cx=a[0]+t*vx,cz=a[1]+t*vz;return Math.hypot(px-cx,pz-cz);}
function distPolyline(x,z,pts){let m=Infinity;for(let i=0;i<pts.length-1;i++)m=Math.min(m,distSeg(x,z,pts[i],pts[i+1]));return m;}
function terrainHeight(x,z,T){
  let carved=null,nearD=Infinity,nearR=null;
  for(const r of T.rivers){const d=distPolyline(x,z,r.centerline);
    if(d<nearD){nearD=d;nearR=r;}
    if(d<r.halfWidth){const ch=r.depth*(1-d/r.halfWidth);carved=carved===null?ch:Math.min(carved,ch);}}
  let h;
  if(carved!==null)h=carved;
  else{const r=nearR,t=nearD-r.halfWidth;const bf=r.bankFbm;
    h=Math.min(t*r.bankSlope,r.bankCap)+fbm(x*bf.scale+(bf.xOff||0),z*bf.scale)*Math.min(t*(bf.ampRate||0.14),bf.ampCap);}
  for(const b of T.bands){const v=Math.abs(b.axis==='z'?z:x);
    h+=Math.max(0,v-b.beyond)*b.slope*(b.fbm.base+fbm(x*b.fbm.scale,z*b.fbm.scale+b.fbm.offset));}
  for(const bm of T.bumps)h+=bm.height*Math.exp(-(((x-bm.center[0])**2)/bm.k[0]+((z-bm.center[1])**2)/bm.k[1]));
  return h;
}
export { distPolyline, terrainHeight };
```

- [ ] **Step 1.3: 寫初版 `data/terrain.json`** 河道中心線取樣 RZ(x) 從 x=-340 到 340 每 20 一點;漢水近似為一條折線(沿 `xt=150-(RZ(150)-z)*0.10`,z 從邊到 RZ(150),halfWidth 取較小值近似 ×2.6):

```json
{
  "world": { "W": 680, "H": 460, "segX": 200, "segZ": 140 },
  "colorRamp": [
    { "maxH": 0,    "color": "#27343a" },
    { "maxH": 1.2,  "color": "#6e6549" },
    { "maxH": 7,    "color": "#46523a", "lerpTo": "#5a6242", "by": "fbm" },
    { "maxH": 16,   "color": "#5a6242", "lerpTo": "#5d5a45", "by": "ramp", "from": 7, "span": 9 },
    { "maxH": null, "color": "#5d5a45", "lerpTo": "#716d63", "by": "ramp", "from": 16, "span": 14 }
  ],
  "rivers": [
    { "id": "changjiang", "centerline": [[-340,46.7],"…每20取樣 RZ…",[340,-19.2]],
      "halfWidth": 34, "depth": -7, "bankSlope": 0.18, "bankCap": 4,
      "bankFbm": { "scale": 0.013, "xOff": 5, "ampRate": 0.14, "ampCap": 16 } },
    { "id": "hanshui", "centerline": [["…沿 xt 線…"]],
      "halfWidth": 13, "depth": -7, "bankSlope": 0.18, "bankCap": 4,
      "bankFbm": { "scale": 0.013, "xOff": 5, "ampRate": 0.14, "ampCap": 16 } }
  ],
  "bumps": [
    { "id": "chibi", "center": [30,44], "k": [700,180], "height": 24,
      "tint": { "color": "#7c4034", "threshold": 0.18, "gain": 2.2, "max": 0.85, "minH": 2 } }
  ],
  "bands": [
    { "axis": "z", "beyond": 118, "slope": 0.22, "fbm": { "scale": 0.02, "base": 0.4, "offset": 7 } }
  ],
  "regions": [
    { "id": "huarong", "center": [-110,-86], "k": [1500,700],
      "tint": { "color": "#39473e", "threshold": 0.25, "gain": 1.6, "max": 0.8, "minH": 0.5, "maxH": 8 } }
  ]
}
```
(centerline 的實際取樣點數值在實作時用一小段 node 算出 RZ 填入,不留 `"…"` 字串。)

- [ ] **Step 1.4: 比對 + 迭代調參** 在 `tools/terrain-fit.mjs` 主程式對 200×140 頂點(x∈[-340,340],z∈[-230,230])算 `Math.abs(terrainHeight - ground)`,印 mean|Δ|、max|Δ|、以及 max 出現的座標。執行 `node tools/terrain-fit.mjs`。目標:**mean|Δ| < 1.0**,且 max|Δ| 不集中在河道/崖/邊山(允許漢水近似處較大)。不到就調 terrain.json(加密 centerline 取樣、調 halfWidth、漢水折線)再跑,直到收斂。記錄最終 mean/max。

- [ ] **Step 1.5: Commit**
```bash
cd /tmp/rc3d
git add tools/terrain-fit.mjs data/terrain.json
git commit -m "feat(terrain): 參數化地形特徵庫資料 + node 擬合工具(terrainHeight≈ground)"
```

---

### Task 2: 生成器移植進 index.html,取代 `ground()` + 上色迴圈

**Files:** Modify `index.html`

- [ ] **Step 2.1: 載入 + 生成器函式** 在 `fbm`(:477)之後、`ground`(:478)之前,加入 top-level 載入與生成器(與 Task 1 的移植同邏輯):
```js
const TERRAIN = await (await fetch('data/terrain.json')).json();
function _distSeg(px,pz,a,b){const vx=b[0]-a[0],vz=b[1]-a[1];const wx=px-a[0],wz=pz-a[1];
  const L=vx*vx+vz*vz||1e-9;let t=Math.max(0,Math.min(1,(wx*vx+wz*vz)/L));
  return Math.hypot(px-(a[0]+t*vx),pz-(a[1]+t*vz));}
function _distPoly(x,z,pts){let m=Infinity;for(let i=0;i<pts.length-1;i++)m=Math.min(m,_distSeg(x,z,pts[i],pts[i+1]));return m;}
function terrainHeight(x,z){
  let carved=null,nearD=Infinity,nearR=null;
  for(const r of TERRAIN.rivers){const d=_distPoly(x,z,r.centerline);
    if(d<nearD){nearD=d;nearR=r;} if(d<r.halfWidth){const ch=r.depth*(1-d/r.halfWidth);carved=carved===null?ch:Math.min(carved,ch);}}
  let h; if(carved!==null)h=carved;
  else{const r=nearR,t=nearD-r.halfWidth,bf=r.bankFbm;
    h=Math.min(t*r.bankSlope,r.bankCap)+fbm(x*bf.scale+(bf.xOff||0),z*bf.scale)*Math.min(t*(bf.ampRate||0.14),bf.ampCap);}
  for(const b of TERRAIN.bands){const v=Math.abs(b.axis==='z'?z:x);
    h+=Math.max(0,v-b.beyond)*b.slope*(b.fbm.base+fbm(x*b.fbm.scale,z*b.fbm.scale+b.fbm.offset));}
  for(const bm of TERRAIN.bumps)h+=bm.height*Math.exp(-(((x-bm.center[0])**2)/bm.k[0]+((z-bm.center[1])**2)/bm.k[1]));
  return h;
}
const _rampCols=null; // (下步 colorRamp 用 THREE.Color 快取)
```

- [ ] **Step 2.2: terrainColor** 加入(用 THREE.Color;colorRamp 解析一次快取):
```js
const _ramp=TERRAIN.colorRamp.map(s=>({maxH:s.maxH,c:new THREE.Color(s.color),
  c2:s.lerpTo?new THREE.Color(s.lerpTo):null,by:s.by,from:s.from,span:s.span}));
const _tintC=new Map();
const tintColor=hex=>{let c=_tintC.get(hex);if(!c){c=new THREE.Color(hex);_tintC.set(hex,c);}return c;};
function terrainColor(x,z){
  const h=terrainHeight(x,z), n=fbm(x*0.05,z*0.05), out=new THREE.Color();
  let seg=_ramp.find(s=>s.maxH===null||h<s.maxH)||_ramp[_ramp.length-1];
  out.copy(seg.c);
  if(seg.c2){ const t=seg.by==='fbm'?n:clamp((h-seg.from)/seg.span,0,1); out.lerp(seg.c2,t); }
  for(const bm of TERRAIN.bumps){ if(!bm.tint)continue; const ti=bm.tint;
    const cf=Math.exp(-(((x-bm.center[0])**2)/bm.k[0]+((z-bm.center[1])**2)/bm.k[1]));
    if(cf>ti.threshold&&h>ti.minH) out.lerp(tintColor(ti.color),clamp((cf-ti.threshold)*ti.gain,0,1)*ti.max); }
  for(const rg of TERRAIN.regions){ const ti=rg.tint;
    const mf=Math.exp(-(((x-rg.center[0])**2)/rg.k[0]+((z-rg.center[1])**2)/rg.k[1]));
    if(mf>ti.threshold&&h>ti.minH&&h<ti.maxH) out.lerp(tintColor(ti.color),clamp((mf-ti.threshold)*ti.gain,0,1)*ti.max); }
  return out;
}
```
(`clamp` 已定義於 :490 附近;`terrainColor` 須在 `clamp` 之後或同模組可見——確認順序。)

- [ ] **Step 2.3: ground() 薄包裝** 把 `function ground(x,z){…}`(:478-488)整段換成:
```js
function ground(x, z){ return terrainHeight(x, z); }
```

- [ ] **Step 2.4: 地形網格改用生成器** 把上色迴圈(:542-556)換成:
```js
for(let i=0;i<pos.count;i++){
  const x=pos.getX(i),z=pos.getZ(i);
  pos.setY(i, terrainHeight(x,z));
  const c=terrainColor(x,z); col.push(c.r,c.g,c.b);
}
```
移除 :539-541 的 `cGrass…tmp` 宣告(若僅此處用;grep 確認後刪)。保留 `geo.computeVertexNormals()` 與 mesh add。`RZ` 保留(水標籤 :locLabel('長江',…,RZ(…)) 仍用)。

- [ ] **Step 2.5: 驗證(載入 + 數值不震)** 起 `python3 -m http.server 8137 -d /tmp/rc3d`,headless 載入 `http://localhost:8137/`(chrome-devtools MCP 若可用;不可用則 `curl` 確認 200 + 讀回編輯確認)。檢查:
  - console 無錯;`data/terrain.json` 200。
  - 既有結構/單位高度不震:`node` 用 Task1 的 `terrainHeight` 與原 `ground` 比對結構座標(襄陽/江陵/夏口/柴桑/campWulin/campChibi 與九幕艦隊 marks)|Δ|<~1。
- [ ] **Step 2.6: Commit**
```bash
cd /tmp/rc3d
git add index.html
git commit -m "feat(terrain): index.html 地形改參數化生成器(ground 薄包裝 + 上色由 terrainColor)"
```

---

### Task 3: schema + validator

**Files:** Create `schema/terrain.schema.json`;Modify `tools/validate-data.mjs`

- [ ] **Step 3.1: schema** Create `schema/terrain.schema.json`(draft 2020-12):`world`(W/H/segX/segZ 數)、`colorRamp`(陣列,item 有 `color` #RRGGBB、`maxH` number|null)、`rivers`(item required centerline(點陣列)/halfWidth/depth)、`bumps`(item required center([2 數])/k([2 數])/height)、`bands`、`regions`。參照既有 `schema/structures.schema.json` 風格。
- [ ] **Step 3.2: validator** 在 `tools/validate-data.mjs` PASS 前加 terrain.json 檢查:
```js
const T=read('../data/terrain.json');
if(!Array.isArray(T.rivers)||!T.rivers.length)errs.push('terrain 缺 rivers');
for(const[i,r]of (T.rivers||[]).entries()){
  if(!Array.isArray(r.centerline)||r.centerline.length<2)errs.push(`river[${i}] centerline 不足`);
  for(const f of['halfWidth','depth'])if(typeof r[f]!=='number')errs.push(`river[${i}] ${f} 非數`);}
for(const[i,b]of (T.bumps||[]).entries()){
  if(!Array.isArray(b.center)||b.center.length!==2)errs.push(`bump[${i}] center`);
  if(!Array.isArray(b.k)||b.k.length!==2)errs.push(`bump[${i}] k`);
  if(typeof b.height!=='number')errs.push(`bump[${i}] height`);}
for(const[i,s]of (T.colorRamp||[]).entries())if(!/^#[0-9a-fA-F]{6}$/.test(s.color||''))errs.push(`colorRamp[${i}] color`);
```
更新 PASS 訊息加 `、terrain ${T.rivers.length}河`。
- [ ] **Step 3.3: 驗證** `node tools/validate-data.mjs` → PASS(含 terrain)。故意刪一個 river.depth → FAIL,改回 PASS。
- [ ] **Step 3.4: Commit**
```bash
cd /tmp/rc3d
git add schema/terrain.schema.json tools/validate-data.mjs
git commit -m "feat(schema): terrain.json schema + validator 擴充"
```

---

### Task 4: 整體迴歸 + README + 本機交付(不 push)

**Files:** Modify `README.md`;檢查全部

- [ ] **Step 4.1: 擬合 + 不震複驗** `node tools/terrain-fit.mjs` → mean|Δ| 仍小;結構/艦隊 marks |Δ|<~1(沿用 Task2.5 比對)。
- [ ] **Step 4.2: headless 迴歸** `http://localhost:8137/`:console 零錯;九幕自動播完;結構貼地、艦隊水位、運鏡未位移(因地形≈原版);火攻正常。`node tools/validate-data.mjs` PASS。
- [ ] **Step 4.3: README** 「技術」段:地形改述為「參數化類比——`data/terrain.json`(河道折線/隆起/山帶/沼澤/色階)經生成器產連續高度場與上色」;新增小節「地形資料(編輯器格式)」;實驗記錄補「第五輪:參數化類比地形(取代 hex tilemap 方向)」。Commit:`docs: README 參數化地形 + 第五輪記錄`。
- [ ] **Step 4.4: 本機交付** 起 `python3 -m http.server 8137 -d /tmp/rc3d`,交付 `http://localhost:8137/` + 精準驗證清單(本次改了什麼→怎麼驗:地形仍像赤壁/結構不浮不位移/河道與紅崖/沼澤色/九幕火攻正常/`node tools/terrain-fit.mjs` mean|Δ| 小/`node tools/validate-data.mjs` PASS)。**不 push**——yazelin 驗收拍板後才 push `feat/parametric-terrain` + 開 PR。

---

## Self-Review 記錄

- **Spec 覆蓋**:特徵庫資料(T1.3)、生成器 terrainHeight/terrainColor(T1.2,T2.1-2.2)、ground 薄包裝 + 網格改用(T2.3-2.4)、數值重現 ground 驗證(T1.4,T2.5,T4.1)、不震下游(T2.5,T4.1-4.2)、schema+validator(T3)、本機驗證+不 push(各 T,T4.4)✓。
- **Placeholder 掃描**:terrain.json 的 centerline 取樣點以「實作時用 node 算 RZ 填入,不留字串」明確標註(非佔位);其餘步驟附完整程式 ✓。
- **型別/命名一致**:`terrainHeight(x,z)`、`terrainColor(x,z)`、`_distPoly`/`_distSeg`、`TERRAIN.{world,colorRamp,rivers,bumps,bands,regions}`、river `{centerline,halfWidth,depth,bankSlope,bankCap,bankFbm{scale,xOff,ampRate,ampCap}}`、bump `{center,k,height,tint}`、band `{axis,beyond,slope,fbm}`、region `{center,k,tint}` 全文一致 ✓。
- **已知風險**:① 漢水各向異性(×2.6)以折線+小 halfWidth 近似,擬合誤差最可能集中此處——T1.4 允許該處較大、但不可影響結構/艦隊(它們離漢水遠);② node 移植與 index.html 生成器須同邏輯(兩處同步,T2 用 T1 同碼);③ 每頂點跑河道折線距離 ×(200×140)約一次性建場成本,可接受;④ colorRamp 的 `by:"ramp"` 區間混色須對齊原 (h-7)/9、(h-16)/14。
