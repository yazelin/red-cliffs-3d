# 戰場 package 編輯 SOP(總覽)

這裡是 red-cliffs-3d 的「戰場 package」編輯指南。給 **AI 與人共讀**:AI 依此知道要改哪些檔、怎麼改、怎麼自證;人依此驗收與微修。

> 範圍:這是 P1「契約層」,只定義 package 邊界與編輯 SOP,**不動 index.html 引擎**。改 `data/` 下的資料檔不會改變引擎行為,只改變引擎讀到的資料。

## 1. 什麼是「戰場 package」

一份戰場 package = 重現一場戰役所需的資料集合。目錄與元資料記在 `data/battlefield.json`(manifest):

```json
{
  "name": "赤壁之戰 208",
  "era": "東漢建安十三年(208)",
  "description": "長江赤壁的火攻決戰——孫劉聯軍以火攻破曹操水師",
  "engine": "red-cliffs-3d",
  "data": {
    "factions": "data/factions.json",
    "terrain": "data/terrain.json",
    "structures": "data/structures.json"
  },
  "pending": ["scene", "audio"]
}
```

manifest 的 `data` 列出**已外部化**的三層;`pending` 誠實標註**尚未外部化**的層。

| 部分 | 檔案 | 狀態 |
|---|---|---|
| 陣營 | `data/factions.json` | 已外部化(見 [factions.md](factions.md)) |
| 地形 | `data/terrain.json` | 已外部化(參數化類比,見 [terrain.md](terrain.md)) |
| 結構 | `data/structures.json` | 已外部化(見 [structures.md](structures.md)) |
| 場景/時間軸 | inline `PHASES`(index.html) | 待外部化(P2) |
| 音訊 manifest | `assets/` + inline | 待外部化(P2) |

> 注意:P1 階段 `battlefield.json` **尚未被 index.html 載入**——它是 package 的「目錄 + 元資料」,給 SOP、未來編輯器與 AI 知道 package 由哪些檔組成。引擎仍各自讀 `data/*.json`。

## 2. AI ↔ 人協作模型

- **AI 產 / 改資料**:依各格式指南編輯 `data/` 下的 JSON——加一條河、移一座城、調陣營色等。AI 負責讓改動「對得上 schema、過得了驗收」。
- **人驗收 + 微修**:人看視覺(截圖)是否符合意圖,做最後的小幅調整與拍板。
- **引擎 / 生成器只讀資料**:渲染器與地形生成器不含戰役知識,只忠實讀 `data/` 下的資料畫出來。要改畫面 = 改資料,不改引擎。

換句話說:**資料是契約,指南讓 AI 知道怎麼改,人保留視覺與意圖的最終判斷。**

## 3. 共同驗收流程

任何對 `data/` 的改動,都跑這條流程自證:

1. **schema / 契約**
   ```bash
   node tools/validate-data.mjs
   ```
   檢查 factions / structures / terrain / battlefield 的必填欄位、型別、列舉值、id 唯一、manifest `data` 指到的檔存在。要 PASS。
2. **地形重現**(只在改 `terrain.json` 時)
   ```bash
   node tools/terrain-fit.mjs
   ```
   把參數化地形與基準函式逐格比對,印出 `mean|Δ|` 與 `max|Δ|`。改地形後確認誤差仍在可接受範圍(細節見 [terrain.md](terrain.md))。
3. **視覺檢查(由人)**:在瀏覽器開 `index.html`,截圖檢查地形、河道、城/營/地名位置、陣營色是否符合意圖。schema 過了不代表畫面對——這一步由人把關。

## 4. 各格式指南

- [terrain.md](terrain.md) — `terrain.json`:rivers / bumps / bands / regions / colorRamp,怎麼加河、加山、改紅崖、加沼澤。
- [structures.md](structures.md) — `structures.json`:city / camp / pass / marker,怎麼加城 / 營 / 關口 / 地名,footprint 要離河道。
- [factions.md](factions.md) — `factions.json`:陣營欄位(name / flag / css / col / dark),怎麼加 / 改陣營。

每份指南都含「給 AI 的最小可複製範例」(一段可貼的 JSON 片段 + 驗收指令)。

## 5. 尚未外部化(P2 待辦)

下列兩層目前仍 inline 在 `index.html`,**還沒有對應的 `data/` 檔與指南**,編輯它們暫時得直接改引擎:

- **scene(場景 / 時間軸)**:九幕的運鏡、單位移動、事件、計策、旁白文稿,目前在 inline `PHASES`。P2 會外部化成資料並補對應 SOP。
- **audio manifest(音訊對應)**:配樂 / 旁白 / 音效與場景的對應,目前散在 `assets/` 與 inline。P2 會外部化成 manifest。

外部化後,這兩層會加進 `battlefield.json` 的 `data`、從 `pending` 移除,並各補一份 authoring 指南。
