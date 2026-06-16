# P2h 實作計劃 — 引擎去赤壁化(讓任意資料包都能渲染)

> 執行方式:單檔(index.html)緊耦合重構,**分塊改 + 每塊瀏覽器驗證**(赤壁逐幕不變 + 官渡逐步前進)。
> 驗收門檻:`?pkg=battlefields/guandu/...` 完整渲染三幕、console 0 error;赤壁預設九幕畫面/行為等價。
> 殘留清單見 `docs/.../2026-06-16-P2g-findings-residue-audit.md`。

**Goal:** 把引擎 module top-level 的赤壁專屬硬編碼(陣營/具名單位/結構/面板)全部改為資料驅動。
**Architecture:** 資料模型補欄位(units.start/gait/chainable/info、structures.fire、scene.combat、factions.panel/legend);引擎以迴圈取代寫死名字。
**Tech Stack:** 單檔 Three.js r160 + 零依賴資料包 + node validator;headless Chrome(swiftshader)截圖驗證。

## 資料模型新增欄位

- **factions.json**(每陣營):`panel`(戰力面板名,default=name)、`legend`(圖例名,default=name)。
- **units.json**(每單位):`start`{x,z,visible,formation?}、`gait`("cav"|"foot",army,default foot)、`chainable`(fleet,連環)、`info`[short,long]。
- **structures.json**:`fire`{scale,yOff}(會燃燒的結構,如 campWulin)。
- **scene.json**(每幕):`combat`[unitIds](broadside 參戰艦隊,取代 COMBAT_FLEETS);set 內 `fleetCao/fleetHg` 改 `<unitId>:{state}`,`campFire/campSmoke` 改 `<structId>:{fire|smoke}`。

## 分塊(每塊獨立可驗)

### Chunk 1 — 面板資料驅動(純顯示,零行為風險)
- FAC builder 加 `darkHex/panel/legend`。
- factions.json(赤壁+官渡)加 panel/legend。
- HTML `#powers` 清空、`#legend` 移除靜態 .lg(留 .hd)。
- 加 `buildPanels()`(FAC 後):依 Object.keys(FAC) 產 .pw 列(id `n_<fac>/b_<fac>/s_<fac>`、inline 色)+ legend 列。
- 戰力更新(原 1632-1635)改 `for(const fac in p.power)`。
- 驗:赤壁面板/圖例外觀不變;官渡顯示袁軍/曹軍。

### Chunk 2 — flagTex 迴圈(載入阻斷 #1)
- `flagTex` 改 `for(const fac of Object.keys(FAC)) flagTex[fac]=flagTexture(fac)`。
- 驗:赤壁旗不變;官渡越過 'hex' 錯。

### Chunk 3 — 單位資料驅動(載入阻斷 #4 + 行為)
- units.json(赤壁+官渡)補 start/gait/chainable/info。
- `initPlace()` 改遍歷 UNITS;camp-type 結構 reset 為 invisible;chainsOn=false。
- `UNIT_INFO` 改由 units.json info 組。
- 載入處 `buildChains(U.caoNavy)` 改:遍歷 chainable fleet。
- `LAND_UNITS` 改由 kind==='army' + gait 組。
- gotoPhase reset 區(1601-1610)改遍歷 U 的 fleet(取代 caoNavy/hgFleet 寫死)。
- 驗:赤壁九幕不變;官渡單位就位。

### Chunk 4 — 結構/火源資料驅動(載入阻斷 #3 + 行為)
- structures.json campWulin 加 fire。
- STRUCT_DATA 提到 module 層;建 `fireEmitters{}`(掃 s.fire);移除 campWulin/campChibi/campWulinFire 具名 const。
- applySet:移除 fleetCao/fleetHg/campWulin/campChibi/campFire/campSmoke 特例,改:
  通用 `if(STRUCT[id])` 處理 visible + fireEmitters[id] 的 fire/smoke;通用 `if(d.state)u.setState`。
- dispatchFx campFire 改 `fireEmitters[e.camp]`。
- scene.json(赤壁):fleetCao→caoNavy{state}、fleetHg→hgFleet{state}、campFire→campWulin{fire:1}、campSmoke→campWulin{smoke:0.8}。
- 驗:赤壁 act7 火、act8 殘骸+煙不變;官渡完整渲染。

### Chunk 5 — combat 逐幕資料(行為)
- scene.json(赤壁)acts 第三/四/七幕加 combat。
- gotoPhase `COMBAT_FLEETS` 改 `p.combat`。
- 驗:赤壁 broadside 不變。

### Chunk 6 — validator/schema 去寫死
- 陣營白名單由該包 factions.json key 推導;validator 支援 `--pkg <manifest>` 驗任意資料包。
- 驗:validator 過赤壁 + 官渡。

## 最終驗收
- 赤壁九幕 headless 截圖逐幕對照(結構/行為等價、0 error)。
- 官渡三幕 headless 截圖(完整渲染、0 error)。
- Workflow 多視角對抗驗證(赤壁等價 / 官渡渲染 / code quality / 漏網殘留 critic)。
