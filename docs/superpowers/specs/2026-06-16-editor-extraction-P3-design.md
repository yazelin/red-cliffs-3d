# 編輯器抽出(引擎 / 格式 / SOP → 獨立「AI 戰場編輯器」repo)設計 — P3

日期:2026-06-16
狀態:autonomous design;待人工審(待 yazelin 拍板)。

## 北極星

把 red-cliffs-3d 的**引擎 + 資料格式 + SOP** 抽成獨立的「**AI 戰場編輯器**」repo:**任何一場戰役都是一份引擎載入的資料 package**;red-cliffs-3d 的赤壁,變成這個編輯器「消費」的其中一份 package。判斷成功的標準很簡單——**換一份 package,就換一場戰役,不必動引擎程式。**

## 背景 / 我們在哪

| 階段 | 內容 | 狀態 |
|---|---|---|
| P1 | 戰場 package 契約(`battlefield.json` manifest)+ AI 編輯 SOP(`docs/authoring/`)+ manifest 驗證。不動引擎。 | ✅ ship([[2026-06-16-battlefield-package-authoring-sop-design]]) |
| P2a | 場景 / 時間軸(九幕 `PHASES`)外部化 → `data/scene.json`;`fx` 閉包 → 宣告式 + `dispatchFx`。 | ✅ ship([[2026-06-16-scene-externalization-design]]) |
| P2b | 音訊外部化 → `data/audio.json`;`AUDIO_CUES` 閉包 → 宣告式 + `dispatchAudioCue`。`pending` 清空。 | ✅ ship([[2026-06-16-audio-manifest-design]]) |
| P2d | 單位名冊外部化 → `data/units.json`(7 個 Army/Fleet 改迴圈建立)。 | ✅ ship([[2026-06-16-units-externalization-design]]) |

現況:`data/battlefield.json` 的 `pending` 已是 `[]`,manifest 列出全部六層(factions / terrain / structures / scene / audio / units)。**整張戰場名義上=純資料。**

**但這份是 P2→P3 的橋。** P2a/b/d 把資料搬出去了,可是引擎還沒真的「以 package 為入口」:`battlefield.json` 從未被載入(`grep battlefield index.html` → 0 命中),六個資料檔仍以**寫死路徑**各自 fetch;而且仍有一批赤壁專屬的文案 / 常數 / 實體 id 寫死在 `index.html`。要達成北極星,得先把這些殘留收乾淨(P2e/f),用一份**第二個 package** 驗證引擎真的 package-driven(P2g),才談得上實際搬 repo(P3)。

> 本份 P3 spec 的角色:**定義「引擎 vs package 邊界」、把 P2 收尾(P2e/f/g)切成可逐步 ship 的階段、再給出 repo 抽出方案。** 它本身不動程式碼(autonomous design),交付物是後續各步驟的契約。

## 審計依據

本 spec 建立在一份對 `index.html`(1811 行)的唯讀審計上(對照 `data/` 既有 package)。審計逐項標出仍寫死的赤壁專屬內容,並分類為 **(a) ENGINE** 留程式 / **(b) DATA** 進資料檔 / **(c) TEXT** 進 manifest 的 `meta`/`ui` 區。下文引用審計編號 #1–#43。已驗證的關鍵事實:

- 六個寫死 fetch 路徑:`index.html` 478(terrain)/479(units)/533(factions)/1035(structures)/1109(scene)/1111(audio)。
- `battlefield.json` 從未 fetch(#43)。
- 最耦合的兩個函式:`initPlace()`(1072–1081,逐行 named unit 起始座標,#37)、ENV 預設表(#29)。
- 「恰好三陣營 cao/sun/liu」假設散落:powers 面板 HTML(389/391/393)、legend HTML(400–403)、`flagTex={cao,sun,liu}`(644)、#10/#11/#42。
- 終幕文案「天下三分 / 赤壁一炬・鼎足之勢成」(419)寫死在 HTML 且**引擎從不覆寫**,只切 `.show` class —— 換戰役會殘留赤壁字樣(#14)。
- 世界尺寸 680×460 同時存在於 `terrain.json` 的 `world` **與** 引擎字面值(574 mesh / 603 水面 / 613–617 撒樹),改 terrain.json 不會改 mesh(#22/#23,bug-class 重複)。

---

## 一、引擎 vs package 邊界(P3 的核心定義)

把 `index.html` 切成三類。**這張表是 P3 抽 repo 時「哪些檔進 engine/、哪些進 package/」的依據。**

### A. GENERIC ENGINE — 留程式(與戰役無關的能力)

| 能力 | 在 index.html 的所在 | 為何是引擎 |
|---|---|---|
| 參數化地形生成器 | terrain mesh build(~552–620)、colorRamp / rivers(Catmull)/ bumps / bands / regions 取樣 | 純讀 `terrain.json` 參數畫高度場;不含戰役知識 |
| 結構建造器 | `buildStructures`(~1035+)、city/camp/pass/marker 幾何、`locLabel` | 依 `structures.json` 的 type 畫;type 詞彙是引擎 |
| Unit / Army / Fleet / setLabel class | ~1054 前的 class 定義、陣型 / 移動 / `setState('burn')` | 兵種行為與外觀;P2d 已把「名冊」抽走,只剩行為 |
| 音訊引擎 + 程序合成器 | `BUILD={drum,hoof,…}`(1285–1384)、`play`/`playFile`/`sword`、OfflineAudioContext 測試 | 通用程序 SFX;`scene/audio.json` 以名稱引用(#31)|
| 時間軸 / 運鏡 / 相機 | `gotoPhase`、`shots` 消費、fog / 視距 / sky / 燈光基礎(#27/#28) | 通用播放器;每幕由資料 tune |
| fx / audio 派發器 | `dispatchFx`(volley/ignite/shake/campFire,1557+)、`dispatchAudioCue`(synth/sfx/sword/burst,1477+) | 宣告式詞彙的執行器;資料驅動(P2a/b 的成果) |
| ENV 混色機制 | `applyEnv`(1095)、`envTgt` 漸變 | 「怎麼混光」是引擎;「有哪些光」是資料(見 B/#29) |
| 風 / 樹 / 粒子系統 | wind particle update、cone-tree 外觀(#24/#25) | 系統與外觀是引擎;範圍 / 方向是資料 |
| UI 殼 + 通用控制 | 載入字樣(367)、播放鈕(上一幕/暫停/速度/運鏡/旁白/字幕/聲線,428–437)、羅盤拖曳提示(135/406)、史/演義 tag **機制**(`e.tag==='史'?…`,1519/1527) | 通用互動 / 播放器 chrome |

### B. PACKAGE DATA — 已外部化的六層(`data/*.json`)

`factions.json` / `terrain.json` / `structures.json` / `scene.json` / `audio.json` / `units.json`。schema 在 `schema/*.schema.json`,SOP 在 `docs/authoring/*.md`。這六層是 package 的本體,P3 抽 repo 時整包成為「赤壁 sample package」。

### C. 仍寫死的赤壁專屬殘留 — P2e/f 要清(審計成果)

分三組。**這組是 P2→P3 橋的實際工作量。**

#### C-1 manifest 未當入口(#43)→ P2e 處理
六個寫死 fetch 路徑各自載入;manifest 的 `data.*` path map 被忽略,`name/era/description` 未用。要換 package 得改六行程式。

#### C-2 殘留赤壁文案 / UI(§1 審計,全是 (c) TEXT)→ P2f 處理
目前**只存在於 HTML / `<head>`**、沒有資料家的赤壁字串。代表項:

| 審計 # | 內容 | 建議新家 |
|---|---|---|
| #1/#6/#7/#17 | `<title>`、`<h1>赤壁之戰`、JSON-LD Event、intro 敘事「建安十三年冬,曹操揮師…」 | `meta.title` / `meta.subtitle` / `meta.intro.*` |
| #2/#4 | description / keywords / 整塊 OG·Twitter | `meta.description` / `meta.keywords` / `meta.og.*` |
| #5/#7 | favicon SVG 字「赤」+ 朱色、top bar 印章「赤」 | `meta.seal`(字 + 色) |
| #8/#15 | era「建安十三年」、時間軸 start/end 標籤 | `meta.era` / `meta.timeline.start`·`.end` |
| **#14** | **終幕「天下三分 / 赤壁一炬・鼎足之勢成」(寫死 + 從不覆寫)** | `meta.finale.title` / `.subtitle` |
| #18 | 「史/演義」來源說明、`classic.html`/`audition.html` sibling 連結 | `meta.legend.sourceNote` / `meta.links`(每部署)|
| #10/#11 | powers 面板 / legend 寫死「曹操軍·孫權軍·劉備軍」三列 + `var(--cao/sun/liu)` | 由 `factions.json` 生成(見 C-3)|

#### C-3 赤壁專屬常數 / 實體 id 寫進控制流(§2–§5 審計)→ P2f 處理
這組最危險,因為「換 package 會壞」而不只是「殘留舊字」:

| 審計 # | 內容 | 處置 |
|---|---|---|
| #22/#23/#25 | 世界尺寸 680×460 寫死於 mesh/水面/撒樹,**無視 `terrain.json` 的 `world`** | (b) 引擎改讀 `TERRAIN.world.W/H/segX/segZ` —— bug 修正,非新功能 |
| #20/#21 | `RZ` 長江中線函式 + 兩個 `locLabel('長江',…)` 寫死 | (b) 兩個水標進 `structures.json`(可跟河 / 預算 x/z) |
| #29 | `ENV={day,cold,dusk,night,inferno,dawn}` 六預設(`inferno` 只因火攻存在) | (b) 新 `environments.json` 或 `scene.environments`;`applyEnv` 留程式 |
| #26 | `WDIR=V3(-0.78,0,-0.63)` 東南風 | (b) `scene.json` meta 或 `meta.windDir`(`wind:true` 旗標已在 scene)|
| #30/#38 | `campFire` 寫死 `campWulin`、`campWulin/campChibi` 全程 special-case | (b) 任何帶 fire emitter 的 camp;引擎迭代 structures 而非點名 |
| #35 | `UNIT_INFO`(caoMain/…/hgFleet 的長文描述) | (c)/(b) 併入 `units.json` 每單位 `role`/`info` |
| #33 | `LAND_UNITS={caoMain:'cav',…}`(哪些單位 hoof vs foot) | (b) `units.json` 每單位 `gait` |
| **#37** | **`initPlace()` 逐行寫死 7 單位起始座標 + 可見性**(最耦合) | (b) 起始 `placement` x/z + visible 進 `units.json`(或 scene `setup`)|
| #36 | `buildChains(U.caoNavy)` 鐵索連環寫死曹軍水師 | (b) 連環 target fleet id 進資料(`scene.json` 已有 `chains:true` 旗標)|
| #39 | `applySet` 別名 `fleetCao→caoNavy`/`fleetHg→hgFleet`/四個 `camp*` 寫死實體 | (a/b) `chains/wind` 留作引擎動詞;實體別名改成真 id |
| #40 | `COMBAT_FLEETS={2:[…],3:[…],6:[…]}` act-index→fleet map | (b) 每幕 `combat:[ids]` 進 `scene.json` |
| #41 | reset 點名 `U.caoNavy.ships`/`U.hgFleet.ships` | (a/b) reset 邏輯留程式,改 loop 全 fleets |
| #42 | `flagTex={cao,sun,liu}` 字面三鍵 | (b) 迭代 `Object.keys(FAC)` —— 引擎別假設恰好三陣營 |
| #34 | `switchVoice` 寫死 yunjhe/hsiaochen(`audio.json` 已宣告 `voices`) | (a/b) 改讀 `AUDIO.narration.voices`(小)|

> **「恰好三陣營」假設**(#10/#11/#42)與**「火攻climax」假設**(#26/#29/#30/#36)是兩條最深的耦合。換成官渡(曹 vs 袁,兩陣營、無火攻)會讓第三 legend 列、`inferno` ENV、`WDIR`、`buildChains`、`campFire` 全部成為死碼或畫錯。這正是 P2g 要用第二 package 逼出來的東西。

---

## 二、遷移順序(逐步、每步可 ship + 可驗,延續 P2a/b/d 風格)

### P2e — manifest 變成載入入口(解 #43)

**目標**:引擎**先** fetch `battlefield.json`,再從其 `data.*` 解析六個路徑去載入;砍掉六個寫死路徑。**這一步本身就解鎖「換 package」。**

引擎(index.html):
- 模組頂層第一個 await:`const PKG = await (await fetch(pkgUrl)).json();`,其中 `pkgUrl` 預設 `'data/battlefield.json'`(P2g 會讓它可被 `?pkg=` 覆寫,見下)。
- 六個 fetch 改成讀 `PKG.data.<key>`:478→`PKG.data.terrain`、479→`PKG.data.units`、533→`PKG.data.factions`、1035→`PKG.data.structures`、1109→`PKG.data.scene`、1111→`PKG.data.audio`。
- 相對路徑以 manifest 所在目錄為基準解析(讓不同資料夾的 package 能載入)。

**驗證(結構等價,不靠截圖)**:
1. `PKG.data` 解析出的六個 URL === 原六個寫死字串(逐一比對)。
2. `git diff main` 僅:加一個頂層 fetch + 六行 fetch 改讀 `PKG.data.*`。其餘引擎不動。
3. `node --check`(抽出的 module script)、`node tools/validate-data.mjs` PASS。
4. yazelin 跑一遍,與 main 行為等價(載入入口換了,渲染不變)。

### P2f — 外部化殘留赤壁文案 / 常數(解 C-2 + C-3)

**目標**:把 §C-2 文案搬進 `battlefield.json` 的新 `meta`(必要時 `ui`)區、§C-3 常數搬進對應資料檔,引擎改讀它們。**做完,`index.html` 內不應再 `grep` 到「赤壁 / 曹操軍 / 天下三分 / WDIR 字面 / 680 / 460 / caoNavy / campWulin」這類戰役字面。**

建議新增 / 擴充(對照審計「Recommended new homes」):

1. **`battlefield.json` 加 `meta` 區**:`title`/`subtitle`/`seal`(字+色)/`description`/`keywords`/`og.*`/JSON-LD 的 event 欄位(name/era/year/place)/`broadcastTag`/`era`·`eraYear`/`intro.{tag,body,foot}`/**`finale.{title,subtitle}`(#14)**/`timeline.{start,end,label}`/`legend.sourceNote`/`links`(sibling 頁,每部署)。可選把 `windDir`(#26)、`camera.initial`(#27)也放這或 scene。
2. **`units.json` 加欄位**:每單位 `info`/`role`(#35)、`gait`(#33)、起始 `placement:{x,z,visible}`(#37)。
3. **`scene.json` 加欄位**:每幕 `combat:[ids]`(#40);把 `fleetCao/fleetHg/camp*` 別名(#39)換成真 unit/structure id;`chains` 的 target fleet id(#36)。
4. **新 `environments.json`(或 `scene.environments`)**:ENV 預設表(#29);`applyEnv` 改讀它,boot 預設由 manifest 指名(取代寫死 `ENV.day`)。
5. **`factions.json` 加欄位**:每陣營 `legend`/`subtitle` 長名,讓 powers 面板 / legend **由 `factions.json` 生成**(#10/#11);引擎所有「三陣營」處改迭代 `factions`(#42)。
6. **terrain / structures**:引擎改讀 `TERRAIN.world`(#22/#23/#25);兩個長江水標 + `RZ` 依賴搬進 `structures.json`(#20/#21);撒樹參數可選進 `terrain.scatter`(#24)。

每項都擴 schema + validator + 對應 `docs/authoring/*.md`(同 P1/P2 慣例:欄位意義 + 怎麼改 + 最小可貼範例 + 驗收)。

**驗證(等價 + 結構)**:
- **文案等價**:`meta` 注入後產生的 `<title>`/`<h1>`/OG/JSON-LD/intro/finale/legend 字串 === 原寫死字串(逐一)。
- **常數等價**:讀 `TERRAIN.world` 產生的 mesh 尺寸 === 680×460(等價,不再重複);ENV 由 `environments.json` 還原原六預設值;`WDIR` 由資料還原原向量;`flagTex` 迭代 factions 產生的三張 === 原三張。
- **id 完整性**:scene `combat`/`chains` target、camp fire binding、unit placement/gait 引用的 id 都在 `units.json`/`structures.json` 內。
- `git diff`:僅文案 / 常數注入點 + 新資料欄位 + schema / validator / authoring;A 類引擎能力不動。
- yazelin 最終肉眼 / 肉耳跑一遍九幕確認與 main 一致。

> P2e + P2f 做完,**才真的達成「整張赤壁=純資料,引擎零赤壁字面」。** 這是 P3 抽 repo 的前置條件 —— 否則抽出去的「引擎」還夾帶赤壁。

### P2g(驗證關卡)— 用第二份最小 package 證明引擎是 package-driven

**目標**:作者一份**最小的第二戰場 package**,經引擎載入,**逼出任何仍寫死的赤壁假設**。這是「引擎真的通用了嗎」的客觀檢驗。

最小 package 內容(刻意小,覆蓋耦合點):
- `terrain.json`:小世界(自訂 `world`)+ 1 條河 + 1 個 bump —— 驗 #22/#23 真的讀 world。
- `factions.json`:**兩個**陣營(例如曹 vs 袁)—— 直接打「恰好三陣營」假設(#10/#11/#42),legend / powers 面板應自動只出兩列、`flagTex` 只兩張。
- `structures.json`:幾個 city/camp/marker。
- `units.json`:2–3 單位含 `placement`/`gait`,**無 fireShip / 無連環** —— 驗 #36/#37。
- `scene.json`:1–2 幕,**無 fire / 無 wind / 無 chains** —— 驗 `inferno`/`WDIR`/`buildChains`/`campFire`(#26/#29/#30/#36)在沒有火攻時不炸、不殘留。
- `audio.json`:最小或省略(若引擎允許無音訊則更能驗健壯性)。
- `environments.json`:自己的小 ENV 集(不含 `inferno`)。
- `battlefield.json`:自己的 `meta`(自己的 title/finale/seal,**絕不能出現赤壁字樣**)。

載入方式:`?pkg=packages/onggang/battlefield.json`(P2e 已把 `pkgUrl` 做成可由 query 覆寫),或暫時換 manifest 路徑。

**自動可驗的部分**(視 / 聽正確性仍需人):
1. **載入成功**:引擎以第二 manifest 開,無 console error,六(或更少)層解析完成。
2. **生成成功**:terrain mesh / structures / units / 兩陣營 legend 都依新資料生成;**畫面 / 標題不含任何赤壁字面**(可寫一次性檢查:DOM `<title>`/`<h1>`/finale/legend 文字 ⊄ 赤壁字典)。
3. **validator PASS**:`node tools/validate-data.mjs --pkg packages/onggang/battlefield.json`(validator 需支援指定 package)對新 package 全綠。
4. **無火攻不炸**:在沒有 chains/wind/fire 的 package 下,`buildChains`/`campFire`/`WDIR`/`inferno` 路徑安全跳過(不 throw、不殘留赤壁 emitter)。

> 明確界線:**視覺 / 音訊 / 編排(choreography)的「對不對」只有人能判**。P2g 的自動關卡只證明「**載入 + 生成 + 該 package 的 validator 通過 + 無赤壁殘字**」。第二 package 是否「像一場戰役」由 yazelin 看。P2g 的價值是**把剩餘寫死處逼成 console error / 殘字 / validator 失敗**,讓它們無所遁形。

### P3 — 實際抽成獨立 repo

P2e/f/g 綠燈後才動 repo 結構。先決條件:引擎零赤壁字面 + 第二 package 能載。

**Repo layout 方案**:

| 方案 | 結構 | 優點 | 缺點 |
|---|---|---|---|
| **(1) 先 monorepo 內部分層** | 同 repo:`engine/`(index.html + 抽出的 module)+ `schema/` + `tools/` + `docs/authoring/`(SOP)+ `packages/chibi/`(現 `data/` 搬入)+ `packages/<test>/` | **改動最小、最快可逆**;一次 commit 就能對照 diff;CI / validator 不必跨 repo;P2g 的第二 package 自然落在 `packages/` | 仍混在 red-cliffs-3d 倉內,品牌 / 邊界沒物理切開 |
| (2) 直接抽新 repo | 新 `battle-editor` repo(engine + schema + tools + SOP),red-cliffs-3d 退化成「**一份 sample package + 指向 editor 的薄殼**」 | 邊界物理清楚、北極星形狀 | 跨 repo 相依 / 版本 / 部署一次到位,風險集中;red-cliffs-3d 既有部署 URL / sibling 頁(classic/audition)要處理 |

**建議:先做方案 (1)(monorepo 內 `engine/` + `packages/`),P4 之後或邊界穩定再升級到 (2)。** 理由:延續 P2「每步小、可逆、可結構驗」的紀律;monorepo 分層讓「引擎 vs package」邊界先在**目錄層**坐實、被 CI 守住,而不必同時承擔搬倉 + 跨倉相依的風險。red-cliffs-3d 的 `data/` 原地改名 / 搬成 `packages/chibi/`(赤壁 sample),`battlefield.json` 不變仍是該 package 入口。等 (1) 跑順、第二 package 證明引擎通用,再評估是否值得 (2) 的物理切分(屆時 red-cliffs-3d 的對外 URL / SEO / sibling 頁如何遷移要另案處理)。

抽 repo 同時要帶走的「工具鏈」:`schema/*.schema.json`(契約)、`tools/validate-data.mjs` + `tools/terrain-fit.mjs`(驗證)、`docs/authoring/*.md`(SOP,P1 起就跟著格式走)。**引擎 + 契約 + 驗證 + SOP 是一套,不可拆。**

### P4 — AI authoring skills(prompt → package → render → 人驗收)

(承襲 P1 規劃,本 spec 只標位置,不展開)把 SOP 從「給 AI 讀的文件」升級成可執行 skill:輸入意圖 → 產 / 改 package → 跑 validator + terrain-fit → 渲染 → 人看 / 聽驗收。P2g 的「載入 + 生成 + validator + 無殘字」正是 P4 自動 loop 的客觀 gate。

---

## 三、風險與各步驗證

| 風險 | 說明 | 緩解 / 驗證 |
|---|---|---|
| **視 / 聽只有人能驗** | 地形河道、城營位置、陣營色、運鏡、火攻音景、九幕編排「對不對」無法自動判 | 每步保留 yazelin 肉眼 / 肉耳關卡(同 P2a/b/d);自動部分只做**結構 / 等價 / 無殘字**驗 |
| **編排耦合(choreography)** | scene 的 fx / cue / move 與特定 unit id / camp / fleet 綁(#30/#36/#37/#39/#40/#41);改成資料驅動後時序 / 對位易跑掉 | P2f 改的是「綁定來源」(寫死 id → 資料 id),**值不變**;逐一核對 dispatch 呼叫 === 原呼叫(延續 P2a 的「dispatchFx≡原 fn」驗法)|
| **世界尺寸重複(bug-class)** | 680×460 同時在 terrain.json 與引擎字面,改 terrain 不改 mesh(#22/#23) | P2f 視為**修 bug**:改讀 `TERRAIN.world` 後斷言尺寸 === 680×460(等價);第二 package 用不同 world 驗真的生效 |
| **「換 package 才暴露」的死碼** | 三陣營 / 火攻假設在赤壁下「剛好對」,換戰役才壞 | **P2g 第二 package 是專門的逼出機制**:兩陣營 + 無火攻直接踩這些假設,壞掉會以 error / 殘字 / validator 失敗現形 |
| **manifest 入口改錯路徑解析** | P2e 相對路徑以哪個目錄為基準,跨資料夾 package 會載錯 | P2e 驗「解析出的六 URL === 原六字串」+ 第二 package 在不同目錄能載 |
| **抽 repo 時工具鏈 / SOP 漏帶** | 引擎搬走但 schema / validator / authoring 留下 → package 失去契約 | P3 把 engine + schema + tools + docs/authoring 當**一套**搬;validator 對 sample package + 第二 package 都要 PASS |
| **red-cliffs-3d 對外資產** | sibling 頁 classic.html / audition.html、OG image、canonical URL、SEO(#3/#4/#18) | 方案 (1) 暫不動對外 URL(原地);真要 (2) 時對外遷移另案;`meta.links` 把 sibling 連結變每部署設定 |

**通用驗證原則(延續 P2)**:能結構 / 等價驗的一律自動(逐欄位 diff、URL 逐一比對、dispatch≡原呼叫、id 完整性、`node --check`、`validate-data.mjs`);視 / 聽 / 編排的「對不對」交人。每步 `git diff main` 必須只動該步宣告的範圍,A 類引擎能力在文案 / 常數外部化時**不得改行為**。

---

## 四、不做(YAGNI / 明確 out of scope)

- **不在 P2e/f 動 A 類引擎能力的行為**:地形生成器 / 結構建造器 / Army·Fleet 行為 / 程序合成器 / 運鏡 / dispatch 詞彙都不重寫,只改「資料從哪來」。
- **不擴 fx / audio / structure / ENV 詞彙**:第二 package 用既有詞彙;新效果型別不在本輪。
- **不做 package 版本化 / 相依解析 / 多 package 同載 / 熱切換 UI**:`?pkg=` 是驗證手段,不是要做 package 選單。
- **不在 P3 就跳方案 (2)**:先 monorepo 分層(`engine/` + `packages/`),物理拆 repo 等邊界穩。
- **不把第二 package 做成「完整官渡」**:P2g 的第二 package 是**驗證探針**(最小、踩耦合點),不是要再重現一場完整戰役;完整新戰役屬 P4 之後。
- **不做自動視覺 / 音訊回歸**:截圖 / 聽覺對比仍由人;不引入 visual diff 框架。
- **不重做對外 SEO / 部署 / 品牌切分**:方案 (1) 期間 red-cliffs-3d 對外 URL 不動;遷移屬 (2) 的另案。
- **P4 的 authoring skill 程式不在本 spec**:本 spec 只把 P2g 的客觀 gate 定義好,供 P4 的 loop 復用。

## 五、P2h 後補:資產路徑規範(P3 處理,勿在 P2 硬修)

P2h 的能力審計發現:**音訊/旁白/音效的素材路徑沒有吃 `PKG_BASE`**——`AUDIO.music.scenes`、`pathPattern`、`AUDIO.sfx.dir`、`AUDIO.narration.cues` 在引擎裡是「相對 document root」直接 fetch(對照 `data/*.json` 那層是有 `PKG_BASE` 前綴的)。原因是**赤壁的素材在 repo root 的 `assets/`**(不在 `data/` 底下),audio.json 以 root 相對路徑引用。

⚠️ **不能在 P2 直接給素材路徑硬加 `PKG_BASE`**:赤壁 `PKG_BASE="data/"`,硬加會變成 `data/assets/...` → 弄壞線上赤壁。這是「資產基準(asset base)規範」的設計題,屬 P3:

- 現況可用:非赤壁 package 用 **root 相對爬升路徑**(如 `battlefields/<name>/assets/...`、`narration.cues="battlefields/<name>/cues.json"`),引擎照吃、validator 也接受——**不阻擋任何 package 取得音樂/語音/音效**。
- P3 抽 repo 時定案:每個 package 宣告自己的 `assetBase`(或素材隨 package 目錄走 + 遷移赤壁素材),讓 `packages/<name>/` 真正自足。屆時 engine 對「資料層」與「素材層」用一致的 base 解析。

同源的兩個 P2h 已修小殘留(供 P3 一併納入規範,非阻擋項):語音切換鈕標籤改由 `narration.voiceLabels` 提供(不再寫死 `yunjhe→男聲`);字幕加「無語音時由場景計時器驅動」的 fallback(`Narration.subTick`),讓「先有字幕文字、語音後補」的 authoring 流程可行——正對應「用編輯器把官渡補完」的 dogfood 路線。

## 與後續的關係

P2e/f 把「引擎以 manifest 為入口 + 零赤壁字面」釘死;P2g 用第二 package 客觀證明「換 package = 換戰役」並逼出殘留;P3 才在綠燈上把 engine + schema + tools + SOP 分層(先 monorepo,後可選獨立 repo),赤壁 `data/` 降格為 `packages/chibi/` sample;P4 把 SOP 升級成 AI authoring loop,以 P2g 的 gate 自動把關。**北極星(任何戰役=一份 package、赤壁只是其一)在 P2e 解鎖、P2g 證明、P3 在 repo 結構上坐實。**
