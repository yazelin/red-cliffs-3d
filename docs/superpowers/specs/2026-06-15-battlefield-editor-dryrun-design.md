# 赤壁之戰 3D — 「AI 戰場編輯器」第一次走查設計(地形 / 天氣 / 軍隊結構 + SOP 萃取)

日期:2026-06-15
狀態:設計已與 yazelin 對話確認,待 spec 審閱

## 背景與真正的目標

這一輪**不是**在美化既有 demo。`index.html` 已是一次對話產出的完整 3D 戰場(程序化地形、九幕資料驅動時間軸、三方艦隊軍團、GPU 火焰、第二輪的電影級音訊)。

真正目的是:**把製作一張歷史戰場的流程實際走一次**,從中萃出未來「AI 戰場編輯器」所需的資料格式與 skill SOP。red-cliffs-3d 在這一輪變成那個編輯器的**參考實作與第一個案例**。

編輯器的定位(yazelin 拍板):

- **給 AI 操作,不是給人用的 GUI**。AI 負責產生與修改戰場;**人負責驗收 + 微修**(例如地形某處小缺陷,人手動調一筆即可)。
- 是一套 **AI 與人協作**的 authoring 系統,最終會落在**另一個獨立 repo**。
- **音訊海選(Freesound → Gemini 代聽 → 人耳終審)本身就是這個編輯器的一條成熟 sub-skill**,涵蓋特效音 / 背景音 / 旁白;這一輪不重做音訊,而是把它登記進編輯器需求,並補上視覺面缺的那幾條 skill。
- 終局:人人可用同一套 AI skills 製作各種歷史戰場主題,像一個「電影級戰場劇情編輯器」。

## 設計原則(全部對齊「AI 改、人驗收 + 微修」)

1. **renderer 只讀資料**:AI 的「修改」就是改 `data/` 裡的 JSON;人的「微修」也是改同一份資料(不碰程式)。`index.html` 退化為讀 `data/` 畫場景的 renderer。
2. **每份資料附 schema**:`schema/` 下放 JSON schema,作為 AI 與編輯器之間的契約。AI 照 schema 產資料,編輯器照 schema 驗。
3. **驗收 harness 沿用現成的**:DevTools 逐幕截圖(視覺驗收)、OfflineAudioContext 非靜音檢查(音訊驗收)。這兩個前兩輪都已在用,正好是人 / AI 的驗收工具,不另造。
4. **混合形式化**:結構/單位這種「資產」先全資料化(最像編輯器要吐的東西);地形、天氣先做視覺升級、但把參數抽成 config 並寫 SOP。完整 schema 化的硬骨頭誠實標註、留給編輯器 repo。

## 已拍板的決策

| 決策 | 結論 |
|---|---|
| 形式化程度 | 混合:結構/單位先抽成 catalog;地形天氣參數化 + 視覺升級 + SOP 筆記 |
| 軍隊模型層級 | 兩者都做:可擴充 catalog 系統 **＋** 挑 1–2 個高價值結構(關口 / 城池)做真正 3D 建模當範例,其餘維持簡單 mesh 佔位 |
| 編輯器定位 | AI 操作、人驗收 + 微修;AI 與人協作;落在另一個獨立 repo |
| 音訊 | 不重做;音訊海選管線登記為既成 sub-skill,引用 `2026-06-11-audio-design.md` |
| scene 抽取範圍 | 只抽「每幕的環境 / 結構 / 音訊引用」;複雜事件邏輯先留程式,標註為編輯器待解硬骨頭 |
| 無 build / 無新依賴 | 維持單一 `index.html` + CDN importmap;新增僅 `data/`、`schema/`、`docs/sop/` |

## 目標資料結構

```
red-cliffs-3d/
  data/
    factions.json     ← 從現有 FAC 抽出(曹藍 / 孫紅 / 劉綠)
    structures.json   ← 城池 / 關口 / 營寨 catalog,可擴充(本輪重點)
    terrain.json      ← 高度場參數 + 地標 + 人工微修 edits[]
    weather.json      ← 晴 / 陰 / 夜 / 起風 / 火場 presets
    scene.json        ← 九幕:引用 weather preset + structures + 既有 audio cue
  schema/             ← 上面每種資料的 JSON schema(編輯器契約)
  index.html          ← renderer:讀 data/ 畫場景
  docs/sop/           ← 邊做邊記的 skill 筆記 + 最終編輯器需求
```

## 實作順序(每一步都留下一條 SOP)

時間不訂死,但順序固定 —— 後面每一步都依賴前面打通的「renderer 讀資料」骨架。

### 步驟 1 — 打通「renderer 讀資料」骨架(最低風險先行)

- 抽 `data/factions.json`(從 `FAC`)與 `data/structures.json`(從現有 `makeCity` / `makeCamp` 的座標與類型)。
- `index.html` 改為啟動時讀這兩份 JSON,迴圈建出結構;`makeCity` / `makeCamp` 改成 catalog 驅動。
- 為什麼先做:用最小改動驗證「資料驅動 renderer」這條主幹,之後地形 / 天氣 / 場景全靠它。
- **SOP 產出**:結構 catalog schema 雛形。

### 步驟 2 — 軍隊 / 結構:catalog 系統 + 高價值建模

- 擴充 `structures.json` schema:`type`(wall / gate-pass / tower / camp / city...)、`faction`、座標、scale、label、可選 model variant。
- 建 **type → builder registry**:AI 在資料加一筆結構即生效;若引用到新 type,則是一次 renderer 擴充(這本身是一條 skill:「如何新增一個結構 type」)。
- 挑 **關口 / 城池**做真正的 3D 建模(城牆 + 城樓 + 關隘),當作「高價值建模」範例;其餘結構維持簡單 box mesh 佔位、由 type 引用。
- **SOP 產出**:兩條 ——「AI 如何新增一個結構(純資料)」與「如何擴一個新結構 type(資料 + renderer)」。

### 步驟 3 — 地形:參數化 + 視覺升級 + 人工微修格式

- 把現有 `ground` / `fbm` / 河道 `RZ` / 上色的硬寫參數抽進 `terrain.json`(octaves、河道係數、color ramp、關鍵地標高度)。
- 視覺升級:紅崖更銳利、華容道沼澤質地、頂點上色改善。
- 加 **人工微修 `edits[]`** 格式:一串 local height nudge / paint,讓人(或 AI)修地形小缺陷不必動程式 —— 直接服務「人負責微修」。
- **SOP 產出**:地形參數 schema + 人工微修格式。

### 步驟 4 — 天氣:presets 資料化 + 效果升級

- `data/weather.json`:預設集(晴 / 陰 / 夜 / 起風 / 火場 = 天空色、霧、光、風向風力、粒子設定)。
- 各幕透過 `scene.json` 引用 preset(例如「東風驟起」→ 起風 preset)。
- 視覺升級:風場 / 粒子更豐富(可加晨霧)。
- **SOP 產出**:天氣 preset schema。

### 步驟 5 — 收口 scene.json + 萃取編輯器需求(最終交付物)

- `data/scene.json`:九幕各自引用 weather preset、structures、既有 audio cue,把整張戰場收成一份資料。
- **範圍取捨(誠實標註)**:只抽「每幕的環境 / 結構 / 音訊引用」;九幕複雜事件邏輯(計策卡、火攻點燃、scrubSet 等)埋在程式裡的部分**先不硬抽**,在 SOP 標為「編輯器待解的硬骨頭」。硬抽完整會爆範圍。
- 寫 `docs/sop/editor-requirements.md`:列齊全部 sub-skill —— 地形 / 天氣 / 結構 / 單位 / **音訊海選(引用既有 spec)** —— 加上共用驗收 harness(截圖迴圈 + 音訊 QA)。這份是未來獨立編輯器 repo 的種子。

## 驗證

- **視覺**:headless Chrome(MCP DevTools)逐幕截圖,console 無錯;結構 / 地形 / 天氣改動逐項對照截圖。
- **資料**:每份 `data/*.json` 對 `schema/*` 驗證通過;renderer 讀不到欄位時有合理 fallback。
- **音訊**:沿用既有 OfflineAudioContext 非靜音檢查(本輪不動音訊,僅確認資料化後不回歸)。
- **回歸**:旁白 / 配樂 / 音效 / 九幕時間軸在資料化後行為不變;`classic.html` 無聲原版不受影響。
- 交付附 per-change verify checklist(動 `index.html` renderer 與 `data/` schema 的部分標清楚)。

## 不做的事(YAGNI)

- 不在這個 repo 蓋編輯器 UI/工具 —— 編輯器是另一個 repo,這輪只產資料格式與 SOP。
- 不硬抽九幕事件邏輯成資料(留給編輯器 repo)。
- 不重做音訊(已成熟,僅登記為 sub-skill)。
- 不引入 build step、不加套件依賴。
- 不把每一種結構都做精緻 3D 建模 —— 只挑 1–2 個高價值的(關口 / 城池),其餘佔位。

## 與外部 PR 的關係

PR #2(外部貢獻者的九幕語音旁白)與第二輪已實作的雙聲旁白功能重疊、且 `index.html` 衝突,故不合併。這份 roadmap 的順序與「結構 / 地形 / 天氣」分工會提前同步給貢獻者,讓未來想參與的部分不再撞點。
