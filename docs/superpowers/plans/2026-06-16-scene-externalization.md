# 場景外部化(P2a)Implementation Plan

> Executed via orchestrated Workflow (author core + SOP in parallel → adversarial structural/behavioral verify → integrate). Checkbox steps.

**Goal:** `PHASES`(九幕)→ `data/scene.json`;`fx` 閉包 → 宣告式事件 + `dispatchFx`;引擎載入 scene.json。**與 main 行為等價**,可結構/行為驗(不靠截圖)。

**Architecture:** index.html 模組頂層 `const SCENE=await fetch('data/scene.json'); const PHASES=SCENE.acts;`;新增 `dispatchFx(e)`(volley/ignite/shake/campFire);`gotoPhase` 的 fx 推送改走 dispatchFx;其餘引擎不動。

**Spec:** `docs/superpowers/specs/2026-06-16-scene-externalization-design.md`

**Source of truth:** `index.html` 的 `PHASES`(:1111-1215)、`gotoPhase`/`applySet`/`spawnEvent`/`showStrat`/`dispatchFx 對應的 fireVolley/setState/shake/campWulinFire`。

---

### Task 1: scene.json + 引擎載入 + dispatchFx + battlefield/schema(core)
- [ ] `data/scene.json`:逐幕忠實轉錄 `PHASES`(key/era/title/dur/env/narr/power/shots/set/march/events/strat/scrubSet/finale);`fx` 轉宣告式(act3 兩 volley;act7 ignite hgFleet / ignite caoNavy+shake2.2 / campFire campWulin + volley / 兩 volley)。座標/參數一字不差。
- [ ] index.html:`const PHASES=[…]` 整段換成 `const SCENE=await (await fetch('data/scene.json')).json(); const PHASES=SCENE.acts;`(放在原 PHASES 位置;模組已支援 top-level await)。
- [ ] index.html:新增 `dispatchFx(e)`(switch e.type:volley→fireVolley(e.from,e.to,e.n,e.fire);ignite→U[e.unit].setState('burn'),e.shake&&shake(e.shake);shake→shake(e.mag);campFire→`{campWulin:campWulinFire}[e.camp]?.target=1` 或等效)。
- [ ] index.html:`(p.fx||[]).forEach(f=>pending.push(f))` → `(p.fx||[]).forEach(e=>pending.push({at:e.at,fn:()=>dispatchFx(e)}))`。其餘 gotoPhase/applySet 不動。
- [ ] `battlefield.json`:加 `data.scene:"data/scene.json"`,`pending` 去掉 scene。
- [ ] `schema/scene.schema.json` + validator 擴充(scene 存在、fx.type enum、每幕必填)。
- [ ] 驗:`node --check`(抽 module)OK;`node tools/validate-data.mjs` PASS;node load-check(每幕欄位 + fx.type∈詞彙 + ignite.unit∈U)。

### Task 2: docs/authoring/scene.md(SOP,parallel)
- [ ] 對照 scene.json/PHASES 寫:一幕的結構(欄位意義)、怎麼加幕/改運鏡(shots:line/orbit/follow)/加 events/加 strat/加 fx 事件(詞彙表)/set 旗標(path/visible/formation/chains/wind/state)/scrubSet/finale;含可貼範例(加一個 volley 事件、加一幕)+ 驗收指令。CRITICAL:只用 scene.schema 內的欄位 + 詞彙。

### Task 3: 整合驗證
- [ ] 結構等價:node 腳本 dump 原 PHASES 非-fn 欄位 vs scene.json → 逐幕一致。
- [ ] dispatchFx ≡ 原 fn:逐事件核對參數(act3×2、act7×6 事件)。
- [ ] zero-behavior:git diff main 僅預期檔;applySet/spawnEvent/showStrat 未改。
- [ ] validator PASS;node --check OK。

## Self-Review
- Spec 覆蓋:scene.json(T1)、dispatchFx+load(T1)、schema/validator(T1)、SOP(T2)、結構/行為等價驗(T3)✓。
- 風險:轉錄漏欄位/改數值 → T3 結構等價 diff 抓;fx 參數錯 → T3 逐事件核對;漏改 forEach 或 dispatchFx 漏 type → load-check + node--check。
