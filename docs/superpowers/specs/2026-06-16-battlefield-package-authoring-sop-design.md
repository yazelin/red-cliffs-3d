# 戰場 package 契約 + AI 編輯 SOP(編輯器轉換 P1)設計

日期:2026-06-16
狀態:設計已與 yazelin 對話確認,待 spec 審閱

## 背景

北極星:把 red-cliffs-3d 萃出的格式/引擎/SOP 逐步轉成獨立「AI 戰場編輯器」repo(見 [[project_red_cliffs_3d_editor]])。逐步轉換路線 P1→P4:
- **P1(本份)**:定義「戰場 package」契約(manifest)+ 寫 AI 編輯 SOP。**只做契約/文件,不動引擎程式。**
- P2:index.html 引擎重構成「載入 package」+ `PHASES` 場景外部化成資料 + 音訊 manifest。
- P3:抽出獨立編輯器 repo。
- P4:AI authoring skills(prompt→package→渲染→人驗收)。

yazelin 的重點:**編輯器很大程度靠 AI 編輯,所以資料必須附「怎麼編輯」的指南,AI 才知道改哪些、怎麼改,才能和人協作。** P1 把這個指南(SOP)做出來,並給 package 一個明確邊界。

## 已拍板的決策

| 決策 | 結論 |
|---|---|
| P1 範圍 | 只做「契約層」:`battlefield.json` manifest + `docs/authoring/` SOP + manifest 驗證。**不動 index.html 引擎、不外部化 PHASES、不開新 repo。** |
| manifest 角色 | 描述「一份戰場 package 由哪些資料組成」的清單;P1 不被 running demo 載入(零行為變動),供 SOP/未來編輯器/AI 知道 package 內容 |
| SOP 對象 | **AI 與人都讀**:每欄位意義 + 怎麼改/加特徵 + 怎麼驗收 + AI↔人協作邊界 |
| 現況標註 | terrain/structures/factions 已外部化;scene(PHASES)/audio 標為「P2 待外部化」 |
| 零風險 | 純新增檔(manifest + docs)+ validator 擴充;不改既有行為 |

## 戰場 package 是什麼(P1 定義)

一份「戰場 package」= 重現一場戰役所需的資料集合。目前(red-cliffs-3d / 赤壁):

| 部分 | 檔案 | 狀態 |
|---|---|---|
| 陣營 | `data/factions.json` | ✅ 已外部化 |
| 地形 | `data/terrain.json` | ✅ 已外部化(參數化類比) |
| 結構 | `data/structures.json` | ✅ 已外部化 |
| 場景/時間軸(九幕:運鏡/移動/事件/計策/旁白文稿) | inline `PHASES` | ⏳ P2 外部化 |
| 音訊 manifest(配樂/旁白/音效對應) | `assets/` + inline | ⏳ P2 外部化 |

## 目標產出

### 1. `data/battlefield.json`(package manifest)
```json
{
  "name": "赤壁之戰 208",
  "era": "東漢建安十三年",
  "description": "長江赤壁的火攻決戰",
  "engine": "red-cliffs-3d",
  "data": {
    "factions": "data/factions.json",
    "terrain": "data/terrain.json",
    "structures": "data/structures.json"
  },
  "pending": ["scene", "audio"]
}
```
(P1 不被 index.html 載入;是 package 的「目錄+元資料」,給 AI/編輯器/SOP 用。`pending` 誠實標註尚未外部化的層。)

### 2. `docs/authoring/`(AI 編輯 SOP)
- `README.md`:總覽——什麼是戰場 package、AI↔人協作模型(AI 產/改資料、人驗收+微修)、共同驗收流程(`node tools/validate-data.mjs`、`node tools/terrain-fit.mjs`、視覺由人看)、各格式指南連結、哪些還沒外部化(P2)。
- `terrain.md`:`terrain.json` 指南——每欄位意義(rivers 控制點+halfWidth/depth、bumps center/radius/height、bands、regions、colorRamp);**怎麼改/加**(加一條河 / 加一座山 / 改紅崖大小 / 加沼澤區);驗收(terrain-fit 看 mean|Δ|、validate、結構不位移);gotcha(河用少數控制點 Catmull、radius 是半徑非 σ²)。
- `structures.md`:`structures.json` 指南——type(city/camp/pass/marker)、欄位、加一座城/營/關口/地名、faction、footprint 要離河道(避免泡水)、驗收。
- `factions.md`:`factions.json` 指南——欄位(name/flag/css/col/dark,色用 #RRGGBB)、加/改陣營。
- 每份指南都含「**給 AI 的最小可複製範例**」(一段可貼的 JSON 片段 + 驗收指令)。

### 3. manifest 契約 + 驗證
- `schema/battlefield.schema.json`(name/era/data 必填;data 各值為字串路徑;pending 為字串陣列)。
- `tools/validate-data.mjs` 擴充:檢查 battlefield.json(必填欄位、data 指到的檔存在)。

## 驗證

- `node tools/validate-data.mjs` → PASS(含 battlefield.json;data 指的三個檔都存在)。
- **SOP 正確性**:每份 authoring 指南的欄位/範例對照**實際** schema 與 data 檔核對一致(不可寫出 schema 沒有的欄位);範例 JSON 片段套進去能過 validator。
- 零行為變動:index.html 未改 → 九幕/火攻/地形/音訊與 main 完全一致(diff 只在新增檔 + validator)。

## 不做的事(YAGNI)

- 不改 index.html 引擎、不把 PHASES/音訊外部化(P2)。
- 不開新 repo(P3)。
- 不寫 AI authoring 的自動化 skill 程式(P4);P1 的 SOP 是「給 AI 讀的文件指南」,不是可執行 skill。
- manifest 不做版本化/相依解析等過度設計。

## 與後續的關係

P1 把「package 邊界 + 怎麼編輯」釘下來;P2 才把引擎改成真的「載入 battlefield.json → 渲染」並外部化 scene/audio;之後 P3 搬 repo、P4 做自動 authoring skills。SOP 從 P1 起就跟著格式走,確保「AI 知道怎麼改」是內建而非事後補。
