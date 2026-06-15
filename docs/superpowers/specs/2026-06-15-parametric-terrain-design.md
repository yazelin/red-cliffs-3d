# 參數化類比地形(特徵庫 + 生成器)設計

日期:2026-06-15
狀態:設計已與 yazelin 對話確認,待 spec 審閱

## 背景

第四輪 hex tilemap 地形走查否決(見 `2026-06-15-hex-dryrun-conclusion.md`):粗 tile 掉細節、共格衝突、盲調不收斂。拍板改走**參數化類比地形**——保留原本連續/平滑的地形生成器(漂亮),把它的**特徵抽成資料**(AI 可生任意戰場),作為 AI 戰場編輯器的地形格式。

本輪在 red-cliffs-3d 把現有 `ground()`(類比地形)的特徵抽成 `data/terrain.json` + 一個生成器,**數值上重現原地形**(因此不震動既有結構/艦隊/運鏡),完成編輯器地形格式的第一個可用實作 + 驗證。

## 已拍板的決策

| 決策 | 結論 |
|---|---|
| 通用度 | **通用特徵庫**(river/bump/band/region 可組合),非赤壁專用常數;用它重現赤壁當驗收 |
| 重現精度 | 河道用折線取樣 RZ → **夠近、非像素一致**;但整體 `terrainHeight ≈ ground()` 須控制在小誤差內(見驗證) |
| 落地處 | red-cliffs-3d:`ground()` 改為讀 `terrain.json` 的生成器;單一 `index.html`、零依賴、零 build |
| 不破壞下游 | 因 `terrainHeight ≈ ground()`,既有結構/艦隊/運鏡/標籤(對準原高度)不位移 |
| 不做 | hex / 天氣 / 移動;不過度設計新特徵型 |

## 現有 `ground()` 的特徵(要抽成資料的東西)

```
RZ(x)=18*sin(0.012x)-0.12x                                   // 長江中心線(sinusoid)
河道:d<34 → h=-7*(1-d/34)                                    // 寬 34、深 -7
漢水支流:z<RZ(150) 時 d=min(d,|x-xt|*2.6),xt=150-(RZ(150)-z)*0.10   // 第二河、各向異性窄
岸+丘:t=d-34 → min(t*0.18,4)+fbm(x*.013+5,z*.013)*min(t*.14,16)
邊山:+= max(0,|z|-118)*0.22*(0.4+fbm(x*.02,z*.02+7))
赤壁紅崖:+= 24*exp(-((x-30)²/700+(z-44)²/180))
上色:高度色帶(bed<0/sand<1.2/grass<7/grass2→hill<16/hill→mt) + 紅崖 tint(中心30,44 k=700,180)+ 華容沼澤 tint(中心-110,-86 k=1500,700)
```

## 目標資料結構 `data/terrain.json`

```json
{
  "world": { "W": 680, "H": 460, "segX": 200, "segZ": 140 },
  "colorRamp": [
    { "maxH": 0,    "color": "#27343a" },
    { "maxH": 1.2,  "color": "#6e6549" },
    { "maxH": 7,    "color": "#46523a", "lerpTo": "#5a6242", "by": "fbm" },
    { "maxH": 16,   "color": "#5a6242", "lerpTo": "#5d5a45", "by": "ramp", "from": 7, "span": 9 },
    { "maxH": null, "color": "#5d5a45", "lerpTo": "#716d63", "by": "ramp", "from": 16, "span": 14 }
  ],
  "rivers": [
    { "id": "changjiang", "centerline": [[x,z], …(沿 RZ 取樣)], "halfWidth": 34, "depth": -7,
      "bankSlope": 0.18, "bankCap": 4, "bankFbm": { "scale": 0.013, "ampCap": 16 } },
    { "id": "hanshui", "centerline": [[x,z], …], "halfWidth": 13, "depth": -7,
      "bankSlope": 0.18, "bankCap": 4, "bankFbm": { "scale": 0.013, "ampCap": 16 } }
  ],
  "bumps": [
    { "id": "chibi", "center": [30,44], "k": [700,180], "height": 24,
      "tint": { "color": "#7c4034", "threshold": 0.18, "gain": 2.2, "max": 0.85, "minH": 2 } }
  ],
  "bands": [
    { "axis": "z", "beyond": 118, "slope": 0.22, "fbm": { "scale": 0.02, "base": 0.4, "offset": 7 } }
  ],
  "regions": [
    { "id": "huarong", "center": [-110,-86], "k": [1500,700],
      "tint": { "color": "#39473e", "threshold": 0.25, "gain": 1.6, "max": 0.8, "minH": 0.5, "maxH": 8 } }
  ]
}
```

- **rivers**:`centerline` 是折線(取樣自 RZ;Catmull/線性內插都行)。距離 = 點到折線最近距離。`halfWidth`/`depth` 雕河;`bankSlope/bankCap/bankFbm` 抬岸。多河取「最深者勝」(min height)+「最近河」算岸 — 重現 ground() 的 `d=min(...)` 行為。漢水的各向異性(×2.6)以較小 `halfWidth` 近似。
- **bumps**:高斯隆起,`k=[kx,kz]`(對應 `exp(-((x-cx)²/kx+(z-cz)²/kz))`),可選 `tint`(達門檻才上色)。紅崖既是高度也是顏色。
- **bands**:沿某軸超過 `beyond` 後線性抬升 × fbm 調變(邊山)。
- **regions**:純上色區(沼澤),不改高度。
- **colorRamp**:由高度查色帶,`by:"fbm"` 用 `fbm(x*.05,z*.05)` 混、`by:"ramp"` 用帶內線性比例混。

## 生成器(取代 `ground()` + 上色迴圈)

`index.html` 模組頂層 `const TERRAIN = await (await fetch('data/terrain.json')).json();`,並建兩個函式:

- **`terrainHeight(x,z)`**:base(0)→ 河流(逐 river 算距離,雕河 or 抬岸,取最深/最近)→ 逐 bump 加高斯 → 逐 band 加山帶。回傳高度。
- **`terrainColor(x,z)`**:colorRamp 依高度取底色 → 逐 bump.tint(高斯權重達門檻)疊色 → 逐 region.tint 疊色。回傳 THREE.Color。
- `function ground(x,z){ return terrainHeight(x,z); }`(薄包裝,其他呼叫點——結構/單位/火焰/水標籤 RZ ——不動;`RZ` 若仍被水標籤用則保留,或改為查 changjiang centerline)。
- 地形網格頂點迴圈改用 `terrainHeight`/`terrainColor`(取代 :542-556 的硬寫色帶 + tint)。

模組化:生成器與特徵函式各自獨立(river/bump/band/region 各一個 contribution 函式),易讀易測。

## 走查驗證(關鍵 — 且純數值可驗,不靠截圖)

1. **高度貼合**:寫 dev 腳本(node,複製 fbm/RZ/原 ground())對密格(例如 200×140 頂點全跑)比較 `terrainHeight(x,z)` vs 原 `ground(x,z)`,報平均 |Δ| 與 max |Δ|。目標:**平均 |Δ| 小(個位數內)、無大面積偏離**(河道/崖/邊山位置一致)。誤差來源主要是河道折線 vs sinusoid 與漢水近似;調 centerline 取樣密度/halfWidth 收斂。
2. **不震下游**:抽查既有結構/艦隊座標處 `terrainHeight ≈ ground`(差 < ~1)→ 確認結構貼地、艦隊水位、運鏡不位移。
3. **上色**:抽查數點 `terrainColor` vs 原色帶邏輯一致(bed/sand/grass/hill/mt + 紅崖/沼澤 tint)。
4. **回歸**:`node tools/validate-data.mjs` 通過(terrain.json 對 schema);九幕、火攻、結構、音訊不回歸。
5. **收尾**:yazelin 肉眼確認仍像赤壁(數值貼合已先保證安全)。

## schema + validator

`schema/terrain.schema.json`(world/colorRamp/rivers/bumps/bands/regions 欄位與型別),`tools/validate-data.mjs` 加 terrain.json 檢查(必填欄位、color #RRGGBB、centerline 為點陣列、k 為兩數)。

## 不做的事(YAGNI)

- 不碰 hex / 天氣 / 移動 / 模型層。
- 河道不追求與 sinusoid 像素一致(折線夠近)。
- 不新增超出 river/bump/band/region 的特徵型(夠表達赤壁;之後按需擴)。
- 不引入 build / 套件。

## 與編輯器的關係

這是編輯器「地形層」的格式雛形:AI 寫一份 `terrain.json`(河道控制點、崖/丘 bump、山帶、沼澤區、色階)= 一張新戰場,平滑生成器照畫。本輪在 red-cliffs-3d 證明「能重現既有精調地形」即驗證格式可行;之後推廣到任意戰場 + 接編輯器。
