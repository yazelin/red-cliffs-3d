# 戰場 package 契約 + AI 編輯 SOP(P1)Implementation Plan

> **For agentic workers:** Executed via an orchestrated Workflow (parallel authoring + adversarial verification). Steps use checkbox (`- [ ]`) syntax.

**Goal:** 定義「戰場 package」manifest(`data/battlefield.json`)+ 寫 AI 編輯 SOP(`docs/authoring/`)+ manifest schema/validator,讓 AI 與人能編輯同一份自描述 package。**契約層,不動引擎、不外部化 PHASES/音訊。**

**Architecture:** 純新增檔(manifest + 文件)+ validator 擴充;零行為變動。SOP 指南必須對照**實際** schema/data 核對(不可出現 schema 沒有的欄位),範例 JSON 片段須過 validator。

**Tech Stack:** JSON manifest、Markdown SOP、零依賴 node validator。

**Spec:** `docs/superpowers/specs/2026-06-16-battlefield-package-authoring-sop-design.md`

**Source of truth(撰寫 SOP 必讀):** `data/{terrain,structures,factions}.json`、`schema/{terrain,structures,factions}.schema.json`、`tools/{validate-data.mjs,terrain-fit.mjs}`。

---

### Task 1: `data/battlefield.json` manifest + schema + validator
- [ ] Create `data/battlefield.json`:`{name:"赤壁之戰 208", era, description, engine:"red-cliffs-3d", data:{factions,terrain,structures 路徑}, pending:["scene","audio"]}`。
- [ ] Create `schema/battlefield.schema.json`(draft 2020-12):required name/era/data;data 各值字串;pending 字串陣列。沿用既有 schema 風格。
- [ ] 擴充 `tools/validate-data.mjs`:讀 battlefield.json,檢查必填 + `data` 指的每個檔存在(`readFileSync` 存在性);PASS 訊息加 `、battlefield`。
- [ ] 驗:`node tools/validate-data.mjs` → PASS。

### Task 2: `docs/authoring/terrain.md`
- [ ] 對照 `terrain.json` + `terrain.schema.json` 寫:每欄位意義(rivers 控制點/halfWidth/depth/bankFbm、bumps center/radius/height/tint、bands、regions、colorRamp);**怎麼加/改**(加河=幾個控制點+halfWidth+depth;加山=bump center+radius+height;改紅崖;加沼澤 region);驗收(`node tools/terrain-fit.mjs` 看 mean|Δ|、`validate-data`、結構不位移);gotcha(河少數控制點 Catmull、radius 是半徑非 σ²、深度負值=水)。含一段可貼 JSON 範例 + 驗收指令。
- [ ] 每個提到的欄位必須在 terrain.schema.json 存在(核對)。

### Task 3: `docs/authoring/structures.md`
- [ ] 對照 `structures.json` + schema 寫:type(city/camp/pass/marker)、欄位(id/type/faction/x/z/label/labelPos/labelClass)、加城/營/關口/地名;faction 限 cao/sun/liu;**footprint 要離河道**(否則泡水,參 P0 教訓);驗收(validate + footprint 在乾地)。含可貼範例。

### Task 4: `docs/authoring/factions.md`
- [ ] 對照 `factions.json` + schema 寫:欄位(name/flag/css/col/dark,色 #RRGGBB);加/改陣營;col/dark 是十六進位色字串(載入轉 three.js)。含可貼範例。

### Task 5: `docs/authoring/README.md`
- [ ] 總覽:什麼是戰場 package(列 battlefield.json + 各 data 檔 + pending 的 scene/audio)、**AI↔人協作模型**(AI 產/改資料、人驗收+微修)、共同驗收流程(validate-data / terrain-fit / 人看視覺)、各格式指南連結、P2+ 待辦(scene/audio 外部化、引擎載入 package、抽 repo)。

### Task 6: 整合驗證(零行為變動 + SOP 正確)
- [ ] `node tools/validate-data.mjs` → PASS(含 battlefield)。
- [ ] SOP 正確性:每份指南欄位/範例對照實際 schema/data 一致;範例 JSON 套進去過 validator(抽驗)。
- [ ] 零行為變動:`git diff main` 只在新增檔 + validator;index.html 未改 → demo 與 main 一致。
- [ ] 本機交付 yazelin 審 SOP 內容;拍板後 push + PR(本機驗到 OK 才 push)。

---

## Self-Review 記錄
- Spec 覆蓋:manifest(T1)、SOP 四份(T2-5)、schema/validator(T1)、零行為變動+SOP正確驗證(T6)✓。
- 無 placeholder;SOP 內容於實作時對照真 schema 寫(adversarial verify 防幻覺欄位)。
- 風險:SOP 寫出 schema 沒有的欄位 → T2-5 各配對抗驗;manifest validator 的檔案存在性檢查用既有 read/fs。
