# 場景外部化(PHASES → data/scene.json)設計 — 編輯器轉換 P2a

日期:2026-06-16
狀態:設計已與 yazelin 對話確認(autonomous run);待最終人工驗收。

## 背景

編輯器轉換 P2(見 [[project_red_cliffs_3d_editor]] 路線 P1→P4)。P1(契約 + SOP)已 ship。P2a = 把寫死在 `index.html` 的九幕 `PHASES`(:1111-1215)外部化成 `data/scene.json`,讓「場景/時間軸」也成為 package 的一層、可被 AI 編輯。P2b(音訊 manifest)另開。

## 關鍵發現

`PHASES` 幾乎全是資料(`key/era/title/dur/env/narr/power/shots/set/march/events/strat/scrubSet/finale`),引擎透過 `applySet`/`spawnEvent`/`showStrat`/`addMarch` 已當資料消費。**唯一非資料 = `fx`**:`fx:[{at, fn:()=>…}]` 是 JS 閉包(僅出現在第三、七幕,共 7 個),呼叫 `fireVolley`/`setState('burn')`/`shake`/`campWulinFire.target`。P2a 把這 7 個閉包轉成**宣告式事件** + 引擎 `dispatchFx`。

## 已拍板決策

| 決策 | 結論 |
|---|---|
| 範圍 | 只做 scene(九幕)外部化;音訊=P2b |
| fx | **宣告式事件詞彙** + `dispatchFx`(取代閉包);其餘 PHASES 欄位直接搬(已是資料) |
| 行為 | **與 main 行為等價**(忠實轉錄 + dispatchFx≡原 fn);可結構/數值驗,不靠截圖 |
| 契約+SOP | `schema/scene.schema.json` + validator;`docs/authoring/scene.md` |
| manifest | `battlefield.json` 加 `scene`,從 `pending` 移除 |

## fx 事件詞彙(涵蓋九幕全部 fx)

| type | 欄位 | 對應原 fn |
|---|---|---|
| `volley` | `from:[x,z], to:[x,z], n, fire` | `fireVolley(from,to,n,fire)` |
| `ignite` | `unit, shake?` | `U[unit].setState('burn')`(+ 可選 `shake(mag)`) |
| `shake` | `mag` | `shake(mag)`(獨立;九幕未用但收進詞彙) |
| `campFire` | `camp` | camp→fire emitter(目前 `campWulin`→`campWulinFire.target=1`) |

第七幕原 `{at:12, fn:()=>{campWulinFire.target=1; fireVolley(...)}}` 拆成**兩個事件**(campFire + volley,同 `at`)。

## 目標資料/程式

### `data/scene.json`
```json
{ "acts": [
  { "key":"第一幕","era":"…","title":"大軍南下","dur":32,"env":"day",
    "narr":"…","power":{…},"shots":[…],"set":{…},"march":[…],"events":[…] },
  … 第三幕含 "fx":[{"at":8,"type":"volley","from":[18,10],"to":[-20,-4],"n":50,"fire":false},…] …
  … 第七幕含 ignite/campFire/volley 事件、"scrubSet":{…}、第七幕 set …,
  … 終幕 "finale":14 …
] }
```
每幕逐欄位忠實轉錄自 `PHASES`;`fx` 改宣告式。

### 引擎(index.html)
- 模組頂層:`const SCENE = await (await fetch('data/scene.json')).json(); const PHASES = SCENE.acts;`(取代 inline `const PHASES=[…]`)。
- 新增 `dispatchFx(e)`:依 `e.type` 呼叫對應引擎函式(表上四種)。
- `gotoPhase` 內 `(p.fx||[]).forEach(f=>pending.push(f))` 改為 `(p.fx||[]).forEach(e=>pending.push({at:e.at, fn:()=>dispatchFx(e)}))`。
- 其餘(applySet/spawnEvent/showStrat/addMarch/scrubSet/finale 處理)**完全不動**。

### `battlefield.json`
`data.scene = "data/scene.json"`;`pending` 去掉 `"scene"`(剩 `["audio"]`)。

### 契約 + SOP
- `schema/scene.schema.json`:acts 陣列;每幕 required key/title/dur/env;fx items required at/type(enum volley/ignite/shake/campFire)。
- validator 擴充:scene.json 存在 + 每個 fx.type 在詞彙內 + 每幕有必填欄位。
- `docs/authoring/scene.md`:怎麼編一幕(加幕/改 dur/env、改運鏡 shots、加 events、加 strat、加 fx 事件、set 旗標說明、scrubSet/finale),含可貼範例 + 驗收。

## 驗證(不靠截圖)

1. **結構等價**:`data/scene.json` 的每幕逐欄位 === 原 `PHASES`(除 fx);寫一次性 node 腳本 diff(把原 PHASES 的非-fn 欄位 dump 出來比對)。
2. **dispatchFx ≡ 原 fn**:逐一核對——act3 兩個 volley 的 from/to/n/fire 一致;act7 的 ignite(hgFleet)、ignite(caoNavy)+shake2.2、campFire(campWulin)+volley、兩個 volley 參數一致。
3. **node load-check**:載入 scene.json,斷言每幕含引擎會讀的欄位;每個 fx.type ∈ 詞彙;每個 ignite.unit ∈ U 的鍵;event/strat 形狀正確。
4. `node --check`(抽出的 module script)語法 OK;`node tools/validate-data.mjs` PASS。
5. **零其他行為變動**:`git diff main` 僅動 index.html(PHASES→load + dispatchFx + 一行 forEach)+ 新增 scene.json/schema/scene.md + battlefield.json + validator。applySet/spawnEvent/showStrat 未改。
6. 最終 yazelin 肉眼跑九幕(火攻/箭雨/震動/燒營/跳幕/scrub)確認與舊版一致。

## 不做(YAGNI)

- 不外部化音訊(P2b)。不抽 repo(P3)。不改 applySet/運鏡/audio 邏輯。不新增 fx 詞彙以外的效果型別。
