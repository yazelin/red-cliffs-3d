# `data/factions.json` 編輯指南

陣營(faction)資料表。定義赤壁戰場上各方勢力的**顯示名稱、軍旗字、配色與 CSS 類別**。其他資料檔(`structures.json` 的 `camp.faction`、引擎內各單位的 `fac`)都以這裡的 **faction id** 為 key 來查顏色與名稱,所以這份檔案是陣營的單一事實來源。

對照 schema:`schema/factions.schema.json`。

---

## 結構

頂層是一個物件,**key 就是 faction id**(`cao` / `sun` / `liu`),value 是該陣營的設定物件。沒有外層陣列、沒有包裝欄位。

```json
{
  "cao": { "name": "曹軍", "flag": "曹", "css": "cao", "col": "#3d7de0", "dark": "#1d3f78" },
  "sun": { "name": "吳軍", "flag": "孫", "css": "sun", "col": "#d84040", "dark": "#7e2020" },
  "liu": { "name": "劉軍", "flag": "劉", "css": "liu", "col": "#3fae6a", "dark": "#1e5e38" }
}
```

### faction id(物件的 key)

短字串識別碼,例如 `cao`。**這個 id 會被別處引用**:

- `data/structures.json` 中 `type: "camp"` 的 `faction` 欄位只接受 `cao` / `sun` / `liu`(validator 寫死)。
- `index.html` 引擎內單位用同樣的 id 查 `FAC[id]` 取得顏色/名稱。

> 因此**新增或改 id 不是只動這一檔**:validator 目前把 camp 的合法 faction 寫死成 `['cao','sun','liu']`,引擎內單位的陣營也是程式碼指定的。純加第四陣營到 `factions.json` 不會自動讓地圖上出現它的單位。本檔負責「這個陣營長怎樣」,不負責「誰屬於這個陣營」。

### 每個陣營的欄位

schema 規定每個 value 都**必填**這 5 個欄位,沒有其他可選欄位:

| 欄位 | 型別 | 意義 |
|------|------|------|
| `name` | string | 顯示名稱,如「曹軍」。出現在單位資訊面板(`ucFac`)等 UI。 |
| `flag` | string | 畫在軍旗貼圖上的字,通常一個漢字(如「曹」)。引擎用 canvas 把它寫在旗面中央。 |
| `css` | string | CSS 類別名(class 後綴)。引擎產生單位標籤時加上 `uLab <css>`,樣式在 `index.html` 以 `.uLab.cao`、`.pw.cao` 等選擇器定義。 |
| `col` | string | 主色,`#RRGGBB` 六位十六進位。**載入時轉成 three.js 顏色**用於旗面、船帆、單位描邊等;同時原字串保留為 `hex` 供 CSS/canvas 用。 |
| `dark` | string | 暗色,`#RRGGBB`。同樣轉 three.js 顏色,用作軍旗漸層的暗端、船體暗部等。一般取 `col` 的較深版本。 |

#### `col` / `dark` 是怎麼被用的

兩者都是 `#RRGGBB` 字串,在 `index.html` 載入時轉換:

```js
out[k] = { name: v.name, flag: v.flag, css: v.css, hex: v.col,
           col: parseInt(v.col.slice(1), 16),    // → three.js 數值色
           dark: parseInt(v.dark.slice(1), 16) };
```

- 字串 `"#3d7de0"` → 去掉 `#`、以 16 進位 parse → `0x3d7de0`,直接餵給 `THREE.Color` / material 的 `color`。
- 原字串另存為 `hex`,canvas 畫旗時當填色字串、UI 文字顏色用。

**格式硬性要求(schema + validator):** 必須符合 `^#[0-9a-fA-F]{6}$` —— 開頭 `#`、剛好 6 位 hex。三位簡寫(`#abc`)、八位含 alpha(`#aabbccdd`)、`rgb()`、顏色名(`red`)都會驗證失敗。

#### `css` 與顏色的關係(別搞混)

`css` 只負責**接上 CSS 類別**(`.uLab.<css>` 的字型/邊框等)。CSS 裡的 `--cao` / `--sun` / `--liu` 顏色變數是在 `index.html` 的 `:root` 內**另外手寫**的,目前數值剛好等於各陣營的 `col`,但兩者沒有自動同步。改了 `col` 不會自動改 CSS 變數;若希望 UI 邊框/進度條顏色一致,需手動同步 `index.html` 的 `:root`(這超出本資料檔範圍)。

---

## RECIPE:改一個陣營的顏色

只改顏色最單純,不影響任何引用。例:把劉軍從綠改成偏青的綠。

1. 編輯 `data/factions.json`,改該陣營的 `col`(必要時連 `dark` 一起,維持「dark 較深」的關係):

```json
{
  "cao": { "name": "曹軍", "flag": "曹", "css": "cao", "col": "#3d7de0", "dark": "#1d3f78" },
  "sun": { "name": "吳軍", "flag": "孫", "css": "sun", "col": "#d84040", "dark": "#7e2020" },
  "liu": { "name": "劉軍", "flag": "劉", "css": "liu", "col": "#2fae8a", "dark": "#175e48" }
}
```

2. 驗證格式:

```bash
node tools/validate-data.mjs
```

通過會印出類似:`PASS — factions 3、structures 14、terrain 2河、battlefield`。

3. (可選)若要讓 UI 同步,手動把 `index.html` `:root` 的 `--liu` 改成相同色值。本步驟會動 `index.html`,屬視覺微調,非本資料契約的一部分。

---

## RECIPE:新增一個陣營

例:加「黃巾」陣營(假想)。

1. 在 `data/factions.json` 加一個新 key,**5 個欄位都要填**:

```json
{
  "cao": { "name": "曹軍", "flag": "曹", "css": "cao", "col": "#3d7de0", "dark": "#1d3f78" },
  "sun": { "name": "吳軍", "flag": "孫", "css": "sun", "col": "#d84040", "dark": "#7e2020" },
  "liu": { "name": "劉軍", "flag": "劉", "css": "liu", "col": "#3fae6a", "dark": "#1e5e38" },
  "huang": { "name": "黃巾軍", "flag": "黃", "css": "huang", "col": "#d6a72e", "dark": "#7e6017" }
}
```

2. 驗證:

```bash
node tools/validate-data.mjs
```

3. **記得**:`factions.json` 通過驗證**不代表新陣營會出現在戰場上**。要讓它真的能用,還需要(超出本檔範圍):
   - 若要放它的營寨,validator 內 camp 的合法 faction 清單(`['cao','sun','liu']`)要一起放寬,否則 `structures.json` 用 `faction: "huang"` 的 camp 會驗證失敗。
   - 引擎內(`index.html`)的單位是程式碼指定陣營的,需要手動建單位才看得到。
   - `index.html` `:root` 沒有 `--huang` 變數,UI 用到 `.pw.huang` 等選擇器的部分會缺色;需要時手動補。

---

## 快速檢查清單

- [ ] 頂層每個 value 都有 `name` / `flag` / `css` / `col` / `dark`(全部必填,沒有別的欄位)。
- [ ] `col`、`dark` 都是 `#RRGGBB`(`#` + 6 位 hex,無簡寫、無 alpha)。
- [ ] 改/加的 faction id 沒有跟別處的引用衝突(尤其 `structures.json` 的 camp、validator 寫死的 faction 清單)。
- [ ] `node tools/validate-data.mjs` 印出 `PASS`。
