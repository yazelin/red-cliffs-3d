# P2g 發現報告 — 第二戰場乾跑 + 引擎殘留審計

> **乾跑目的**:用第二個戰場(官渡之戰)反向驗證「戰場 = 資料包,引擎只是載入器」這個抽象是否成立。
> 結論:**資料包載入機制成立**,但引擎仍有一批赤壁專屬的硬編碼會在載入非赤壁陣營的資料包時 throw。
> 這份報告把殘留逐一定位,作為 **P2h(引擎去赤壁化)** 的工作清單。

## 乾跑作法

- 新增 `?pkg=` query param + `PKG_BASE`,讓引擎能載入任意 manifest(相對於 manifest 所在目錄解析子層路徑)。
- 新增 `battlefields/guandu/`:一份完整、合法的官渡之戰資料包(7 檔,陣營 yuan/cao,地形黃河+烏巢,無赤壁/長江)。
- 用 headless Chrome(swiftshader WebGL)同時載入兩個資料包截圖驗證。

## 乾跑結果

| 資料包 | manifest/meta 載入 | 模組執行 | console error | 畫面 |
|---|---|---|---|---|
| 赤壁(預設 `data/battlefield.json`) | ✅ 標題/年號正確 | ✅ `__start` 存在 | **none** | ✅ 完整渲染 |
| 官渡(`?pkg=battlefields/guandu/battlefield.json`) | ✅ 標題「官渡之戰」、年號「建安五年・西元二〇〇」正確 | ❌ `__start` undefined(模組 throw) | `Cannot read properties of undefined (reading 'hex')` | ❌ 空白 |

**判讀**:`?pkg=` + manifest 相對路徑 + `applyMeta()` 全部成立(官渡的標題、年號、文案都正確套上 DOM)。
真正的牆是**引擎在 module top-level 執行的赤壁專屬程式碼**:它在資料載完後立刻用寫死的陣營/單位/結構名字去 new 物件,換一個陣營組合就 throw。
這正是乾跑要找的東西 —— 把它清掉,引擎才真的是「載入器」。

## 殘留清單(= P2h 工作項,附 index.html 行號)

### A. 載入即 throw(擋住第二戰場連畫面都出不來)

1. **`flagTex` 寫死三陣營**(行 676)
   `const flagTex={cao:flagTexture('cao'),sun:flagTexture('sun'),liu:flagTexture('liu')};`
   `flagTexture('sun')` 讀 `FAC['sun'].hex`(行 663)→ 官渡無 sun → **這就是 `'hex'` 那個錯**。
   修法:對 `Object.keys(FAC)` 迴圈產生 flagTex。

2. **`buildChains(U.caoNavy)`**(行 1091,module load 即執行)
   引用具名單位 `caoNavy`;官渡無此單位 → `buildChains(undefined)`。
   修法:連環(chains)改為資料宣告(單位或場景上的 flag),無宣告則跳過。

3. **具名結構火源**(行 1079 / 1112 / 1146)
   `const campWulin = STRUCT.campWulin;` → 官渡無 → 行 1146 `attachFire(campWulin,...)` throw;`campChibi` 同理(行 1112)。
   修法:火源 emitter 由資料宣告(哪些結構會燃燒),引擎掃描產生。

4. **`initPlace()` 具名單位初始座標**(行 1104–1112,結尾行 1763 還會再呼叫一次)
   `U.caoMain.place(-250,-150)` 等一串寫死的赤壁單位起點;官渡單位不存在 → throw。
   修法:每單位的初始座標/可見性/陣形寫進資料(units.json 的 `start` 或 scene 第 0 幕),`initPlace()` 改為遍歷資料。

### B. 載入後行為錯(畫面出得來但播放不對)

5. **`LAND_UNITS` 寫死陸戰單位 id**(行 1471)`{caoMain:'cav',liuArmy:'foot',caoRen:'foot'}` → 行軍腳步聲只認這三個。修法:由單位 kind/type 推導。
6. **`COMBAT_FLEETS` 寫死幕→艦隊**(行 1614)`{2:['caoNavy','sunFleet'],...}`。修法:由場景資料(每幕參戰單位)或單位 kind 推導。
7. **`applySet` 內寫死 id 分支**(行 1573–1578)`if(id==='fleetCao')` / `'campWulin'` / `'campFire'` / `'campSmoke'`。修法:走通用 path(行 1583 已有雛形),特例改資料驅動。
8. **`dispatchFx` campFire 寫死 camp**(行 1594)`if(e.camp==='campWulin')`。修法:通用 camp → fire emitter 查表。
9. **`reset()` 引用具名單位/火源**(行 1603–1609)`U.caoNavy` / `campWulinFire`。修法:遍歷資料中的艦隊與火源。

### C. 面板/圖例硬編碼(顯示錯但不 throw)

10. **戰力面板**(HTML 行 388–393)寫死「曹操軍/孫權軍/劉備軍」+ `nCao/nSun/nLiu` id + `.cao/.sun/.liu` class,且假設正好 3 陣營。修法:由 factions.json 產生列。
11. **圖例 legend**(HTML 行 399+)同樣寫死陣營色塊。修法:由 factions.json 產生。
12. **單位卡 `ucFac`**(行 1733–1734)`FAC[u.fac].name` 已是資料驅動,確認在 N 陣營下成立即可。

### D. 工具殘留

13. **validator/schema 陣營 enum 寫死 `[cao,sun,liu]`**,且只驗 `data/`。修法:陣營白名單由該包 factions.json 推導;validator 支援 `--pkg <manifest>` 驗任意資料包。

## 收尾建議

- **本 PR(P2g)交付**:`?pkg=` 載入機制(赤壁實測 0 error、畫面不變)+ 官渡資料包(合法但待 P2h 才會渲染,僅 `?pkg=` 可達、不影響線上赤壁)+ 本報告。
- **下一步 P2h**:依上表 A→B→C→D 去赤壁化。驗收門檻:`?pkg=battlefields/guandu/...` 能完整渲染九幕、console 0 error,且赤壁預設畫面逐幕不變(結構/行為等價)。

## P2h 結案(殘留逐項對照)

P2h 已完成,六塊分批改 + 每塊瀏覽器實測。**赤壁九幕 + 官渡三幕皆 0 console error**。逐項收尾:

| # | 殘留 | 解法 | 驗收 |
|---|---|---|---|
| 1 | flagTex 寫死三陣營 | `for(Object.keys(FAC))` 迴圈 | 赤壁旗不變 / 官渡過 'hex' |
| 2 | buildChains(U.caoNavy) | units.chainable 宣告,迴圈建鎖 | 官渡無連環不報錯 |
| 3 | 具名結構火源 campWulin/campChibi | structures.fire → fireEmitters{} 掃描 | 赤壁 act7 火、官渡烏巢火皆成立 |
| 4 | initPlace 具名單位座標 | units.start 驅動,遍歷 UNITS | 兩戰場單位皆就位 |
| 5 | LAND_UNITS 寫死 | kind=army + gait 推導 | 行軍腳步聲正常 |
| 6 | COMBAT_FLEETS 寫死幕→艦隊 | scene.acts[].combat 陣列 | 赤壁 broadside 不變 |
| 7 | applySet fleetCao/campWulin… 特例 | 通用 STRUCT[id]+d.state | 赤壁/官渡 set 皆生效 |
| 8 | dispatchFx campFire 寫死 camp | fireEmitters[e.camp] 查表 | 官渡 campFire 焚烏巢 |
| 9 | reset 引用具名單位/火源 | 遍歷 U 的 fleet + emitters | 赤壁 scrub-reset 過 act7/8 |
| 10 | 戰力面板硬編碼 | buildPanels() 由 factions 產生 | 官渡顯示袁紹軍/曹操軍 |
| 11 | 圖例 legend 硬編碼 | 同上(legend 欄位) | 官渡圖例正確 |
| 12 | 單位卡 ucFac | 既已資料驅動,N 陣營成立 | — |
| 13 | validator 陣營 enum + 只驗 data/ | `--pkg` + 白名單由 factions 推導 | 雙包皆 PASS |
| 額外 | 長江標籤 / 旁白 voice / 音訊空欄位 | followRiver marker / voices 推導 / 空欄位防呆 | 官渡無多餘長江、0 error |

未做(留 P3):WDIR 風向常數仍寫死(不阻擋,留資料化到 P3);world-size 等 P3 audit 其他項。
