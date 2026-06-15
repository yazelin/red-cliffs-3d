# 編寫 `data/scene.json`

給 AI 與人類編輯者的指南。本檔每個欄位都對應引擎(`index.html`)實際消費的資料,或 `schema/scene.schema.json` 的契約。**不要發明欄位**——本指南沒列到的欄位,引擎會默默忽略,validator 也可能直接退件。

## `scene.json` 是什麼

`scene.json` 是整段時間軸(timeline)的劇本資料。它只有一個頂層欄位 `acts`,是一個**幕(act)陣列**,目前九幕:第一幕到終幕。引擎在啟動時載入:

```js
const SCENE = await (await fetch('data/scene.json')).json();
const PHASES = SCENE.acts;
```

時間軸引擎逐幕播放:每進一幕(`gotoPhase`)就套用該幕的環境、單位佈署、行軍動線、相機運鏡,並把該幕的 `events / strat / fx / finale` 排成「到第幾秒觸發」的待辦佇列(`pending`),隨幕內時間 `phaseT` 推進依序執行。

這份檔案以前是寫死在 `index.html` 的 `PHASES` 常數;外部化後它成為戰場 package 的一層,可被 AI 編輯。`battlefield.json` 用 `data.scene` 指向本檔。

### 座標系統

世界座標為 `x`(東西)與 `z`(南北),單位同 `terrain.json` 的世界單位。幕內所有 `path`、`shots` 的相機點、`events` 的位置、`fx` 的 `from/to` 都用這套座標。佈署/動線的點寫成 `[x, z]`(兩元素);相機點寫成 `[x, y, z]`(三元素,含高度 `y`)。

### 時間單位

幕的 `dur` 與所有 `at`(events / strat / fx / finale 的觸發時間)都是**幕內秒數**,從進入該幕起算 0。`set` 內移動的 `dur` 也是秒。

---

## 一幕的欄位

每個 act 物件可有下列欄位。`key / era / title / dur / env` 為每幕必填;其餘按該幕需要而定。

| 欄位 | 型別 | 意義 |
|---|---|---|
| `key` | string | 幕名,如 `第一幕`、`終幕`(顯示於幕標) |
| `era` | string | 年代字串,如 `建安十三年 秋`(顯示於幕標與年代區) |
| `title` | string | 幕標題,如 `大軍南下` |
| `dur` | number | 該幕總長(秒) |
| `env` | string | 環境光照預設,見下方枚舉 |
| `narr` | string | 旁白文字(顯示於下方解說) |
| `power` | object | 三方勢力面板,見下方 |
| `shots` | array | 相機運鏡序列,見「相機 `shots`」 |
| `set` | object | 進幕時套用的場景狀態旗標,見「`set` 旗標」 |
| `march` | array | 行軍動線箭頭,見下方 |
| `events` | array | 事件標記(地圖上彈出卡),見下方 |
| `strat` | object | 計策卡(畫面彈出大卡),見下方 |
| `fx` | array | 宣告式特效事件,見「fx 事件詞彙」 |
| `scrubSet` | object | 跳幕時瞬間套用的狀態,見下方 |
| `finale` | number | 幕內第幾秒顯示結局畫面 |

### `env`(必填)

環境光照預設鍵,只能是以下其中之一(對應引擎 `ENV` 表):

`day` ・ `cold` ・ `dusk` ・ `night` ・ `inferno` ・ `dawn`

其中 `inferno`(火燒赤壁)會開啟火光(`glow`)。不要新增其他鍵。

### `power`

三方勢力資訊面板,固定三鍵 `cao / sun / liu`,每個值是 **三元素陣列** `[兵力字串, 進度百分比, 狀態字串]`:

```json
"power":{
  "cao":["約 200,000+（號稱八十萬）",100,"新得荊州・銳氣正盛"],
  "sun":["30,000",15,"按兵柴桑・觀望形勢"],
  "liu":["約 20,000（含劉琦）",10,"長坂新敗・退保夏口"]
}
```

第二元素是 0–100 的數字,當作那一方力量條的寬度(`%`)。

### `march`(行軍動線)

陣列,每元素是一條行軍箭頭:

| 欄位 | 型別 | 意義 |
|---|---|---|
| `pts` | array of `[x,z]` | 動線折點(≥2 點) |
| `fac` | string | 陣營,`cao` / `sun` / `liu`(決定箭頭顏色) |

```json
"march":[{"pts":[[-250,-150],[-242,-100],[-240,-40]],"fac":"cao"}]
```

`march` 只畫示意箭頭,不會移動單位本體;要移動單位用 `set` 的 `path`。

### `events`(事件標記)

陣列,每元素是一張在地圖上某點彈出的小卡:

| 欄位 | 型別 | 意義 |
|---|---|---|
| `at` | number | 幕內第幾秒彈出 |
| `x` | number | 世界 x |
| `z` | number | 世界 z |
| `t` | string | 卡片文字 |
| `tag` | string | `史`(史實)或 `演義`(小說),決定卡片配色 |

```json
{"at":2.5,"x":-250,"z":-160,"t":"劉琮舉州投降","tag":"史"}
```

### `strat`(計策卡)

單一物件(每幕至多一張),於 `at` 秒在畫面彈出一張大卡:

| 欄位 | 型別 | 意義 |
|---|---|---|
| `at` | number | 幕內第幾秒彈出 |
| `name` | string | 計策名,如 `連環計` |
| `by` | string | 出處/人物,如 `龐統 獻計 曹操`(顯示時前綴 `史載・`/`演義・`) |
| `tag` | string | `史` 或 `演義`(決定印章是 `史` 還是 `計`,及前綴) |
| `desc` | string | 計策說明全文 |

```json
"strat":{"at":2,"name":"連環計","by":"龐統 獻計 曹操","tag":"演義",
  "desc":"正史載曹操自令船艦相連以減顛簸;演義中為龐統詐獻之計。"}
```

### `scrubSet`(跳幕瞬間狀態)

物件,結構與 `set` 相同,但語意是「**跳到/重建此幕時瞬間套用**(無動畫)」。重建時間軸(往回跳或拖曳 scrub)會把先前各幕的 `set` 與 `scrubSet` 都以瞬間模式重播,確保跳到任何一幕時世界狀態正確。例如第七幕用 `scrubSet` 讓「跳進火燒幕」時曹軍船陣直接呈現燃燒、營寨直接著火:

```json
"scrubSet":{"fleetCao":"burn","campFire":true}
```

### `finale`

數字。設了之後,該幕第 `finale` 秒會顯示結局畫面(目前只有終幕用,值 `14`)。

---

## 相機 `shots`(運鏡)

`shots` 是陣列,依序播放;每個 shot 用滿自己的 `dur` 後切到下一個。三種 `kind`:

### `line`(直線推移)

相機從 `a` 沿直線移動到 `b`,鏡頭一直看向 `look`。

| 欄位 | 型別 | 意義 |
|---|---|---|
| `kind` | `"line"` | |
| `a` | `[x,y,z]` | 起點相機位置 |
| `b` | `[x,y,z]` | 終點相機位置 |
| `look` | `[x,y,z]` | 注視點(全程固定) |
| `dur` | number | 此鏡頭時長(秒) |

```json
{"kind":"line","a":[-420,250,300],"b":[-250,160,170],"look":[-180,0,-70],"dur":16}
```

### `orbit`(環繞)

相機繞著中心 `c`,半徑 `r`、固定高度 `h`,角度從 `a0` 弧度掃到 `a1` 弧度。

| 欄位 | 型別 | 意義 |
|---|---|---|
| `kind` | `"orbit"` | |
| `c` | `[x,y,z]` | 環繞中心(亦為注視點) |
| `r` | number | 環繞半徑 |
| `h` | number | 相機高度 |
| `a0` | number | 起始角(弧度) |
| `a1` | number | 結束角(弧度) |
| `dur` | number | 此鏡頭時長(秒) |

```json
{"kind":"orbit","c":[-42,0,-11],"r":74,"h":34,"a0":2.7,"a1":4.3,"dur":25}
```

### `follow`(跟拍單位)

相機以固定偏移 `off` 跟著某個單位移動,鏡頭看向該單位。

| 欄位 | 型別 | 意義 |
|---|---|---|
| `kind` | `"follow"` | |
| `unit` | string | 要跟的單位鍵(見下方單位鍵清單) |
| `off` | `[dx,dy,dz]` | 相對單位位置的相機偏移 |
| `dur` | number | 此鏡頭時長(秒) |

```json
{"kind":"follow","unit":"hgFleet","off":[10,22,-34],"dur":14.4}
```

---

## `set` 旗標(進幕狀態)

`set` 是一個物件,鍵是「要設定的東西」。進幕時以**動畫模式**套用,跳幕重建時以**瞬間模式**套用。鍵分兩類:**單位鍵**(值是物件)與**特殊旗標**。

### 單位鍵

下列單位鍵的值是物件,可帶 `path` / `visible` / `formation`:

| 單位鍵 | 說明 |
|---|---|
| `caoMain` | 曹操本軍(陸軍) |
| `caoNavy` | 曹軍水師 |
| `caoRen` | 江陵守軍 曹仁 |
| `liuArmy` | 劉備軍 |
| `liuFleet` | 江夏水軍 |
| `sunFleet` | 周瑜水師 |
| `hgFleet` | 黃蓋先鋒(火船) |

單位物件可帶的欄位:

| 欄位 | 型別 | 意義 |
|---|---|---|
| `path` | array of `[x,z]` | 移動路徑折點;動畫模式下沿路徑移動並自動現身,瞬間模式下直接放到終點 |
| `dur` | number | 沿 `path` 移動的秒數(預設 8) |
| `visible` | boolean | 顯示/隱藏該單位 |
| `formation` | string | 隊形,`tight`(緊密,如鐵索連環)或 `loose`(鬆散) |

```json
"set":{
  "caoNavy":{"path":[[-150,16],[-90,4],[-42,-11]],"dur":9},
  "sunFleet":{"path":[[60,10],[30,13]],"dur":8},
  "hgFleet":{"visible":true}
}
```

### 特殊旗標

| 鍵 | 型別 | 意義 |
|---|---|---|
| `chains` | boolean | 鐵索連環(`true` 顯示連鎖鐵環) |
| `wind` | boolean | 東南風(`true` 開啟風場;會同步加強旗幟飄動) |
| `campWulin` | `{visible}` | 烏林大營顯示/隱藏 |
| `campChibi` | `{visible}` | 赤壁大營顯示/隱藏 |
| `campFire` | `true` | 點燃烏林大營(設成著火) |
| `campSmoke` | `true` | 烏林大營轉為冒煙(餘燼,僅煙) |
| `fleetCao` | string | 曹軍水師(caoNavy)整體狀態字串:`normal` / `burn` / `wreck` |
| `fleetHg` | string | 黃蓋火船(hgFleet)整體狀態字串:`normal` / `burn` / `wreck` |

`fleetCao` / `fleetHg` 是用「狀態字串」一次切換整支船隊的外觀(`burn` 燃燒、`wreck` 殘骸);與單位鍵的 `caoNavy` / `hgFleet` 物件是兩種不同寫法,不要混用同一鍵。

```json
"set":{"caoNavy":{"formation":"tight"},"chains":true}
```

```json
"set":{"fleetCao":"wreck","fleetHg":"wreck","chains":false,"wind":false,"campSmoke":true}
```

---

## fx 事件詞彙

`fx` 是宣告式特效事件陣列(取代以前寫死的 JS 閉包)。每個事件至少有 `at`(幕內秒)與 `type`,引擎在 `at` 秒呼叫對應特效。**只有以下四種 `type`**:

| `type` | 必填欄位 | 可選 | 效果 |
|---|---|---|---|
| `volley` | `from:[x,z]`, `to:[x,z]`, `n`, `fire` | — | 從 `from` 射 `n` 支箭/火箭到 `to`;`fire:true` 為火箭、`false` 為箭雨 |
| `ignite` | `unit` | `shake` | 把單位 `unit` 點燃(設為 `burn`);若給 `shake`,同時以該強度震動相機 |
| `shake` | `mag` | — | 相機震動,強度 `mag`(獨立使用) |
| `campFire` | `camp` | — | 點燃指定營寨(目前唯一有效值 `campWulin`) |

`volley` 各欄位:

| 欄位 | 型別 | 意義 |
|---|---|---|
| `at` | number | 觸發秒 |
| `from` | `[x,z]` | 起點 |
| `to` | `[x,z]` | 落點 |
| `n` | number | 投射物數量 |
| `fire` | boolean | 是否火焰(火攻用 `true`) |

`ignite` / `shake` / `campFire`:

| 欄位 | 型別 | 意義 |
|---|---|---|
| `at` | number | 觸發秒 |
| `unit` | string | (ignite)要點燃的單位鍵,須是上方單位鍵之一(如 `hgFleet`、`caoNavy`) |
| `shake` | number | (ignite 可選)點燃同時震動的強度 |
| `mag` | number | (shake)震動強度 |
| `camp` | string | (campFire)營寨鍵,目前用 `campWulin` |

範例(第三幕的兩波箭雨對射、第七幕火攻的點燃+震動+燒營+火箭齊射):

```json
"fx":[
  {"at":8,"type":"volley","from":[18,10],"to":[-20,-4],"n":50,"fire":false},
  {"at":10,"type":"volley","from":[-26,-6],"to":[12,9],"n":50,"fire":false}
]
```

```json
"fx":[
  {"at":4.5,"type":"ignite","unit":"hgFleet"},
  {"at":10,"type":"ignite","unit":"caoNavy","shake":2.2},
  {"at":12,"type":"campFire","camp":"campWulin"},
  {"at":12,"type":"volley","from":[-6,6],"to":[-44,-12],"n":60,"fire":true},
  {"at":14.5,"type":"volley","from":[-12,2],"to":[-50,-16],"n":60,"fire":true},
  {"at":17,"type":"volley","from":[-30,-2],"to":[-58,-20],"n":50,"fire":true}
]
```

> 同一時刻可有多個事件(如第七幕 `at:12` 的 campFire 與 volley 同時)。`shake` 既能當 `ignite` 的可選欄位,也能當獨立 `type` 用。

---

## RECIPES(操作食譜)

### 加一幕

在 `acts` 陣列適當位置插入一個 act 物件。`key / era / title / dur / env` 必填,其餘按需。最簡可運作的一幕:

```json
{
  "key":"第N幕","era":"建安十三年 冬","title":"範例幕","dur":20,"env":"cold",
  "narr":"這裡是旁白。",
  "power":{
    "cao":["約 200,000",90,"對峙烏林"],
    "sun":["30,000",15,"火攻之策已定"],
    "liu":["約 20,000",10,"整軍備戰"]
  },
  "shots":[
    {"kind":"line","a":[90,40,-30],"b":[58,30,-6],"look":[46,2,16],"dur":20}
  ],
  "set":{"hgFleet":{"visible":true}},
  "events":[{"at":5,"x":30,"z":13,"t":"範例事件","tag":"史"}]
}
```

注意:幕的順序就是播放順序;加幕會改變後續幕的索引,引擎內以幕索引判定戰鬥船隊等行為,插隊時請整體檢查。

### 改一個相機運鏡

找到該幕的 `shots`,改對應 shot 的欄位即可。例如把第六幕的單一直線鏡頭改成繞著聯軍中心轉:

```json
"shots":[{"kind":"orbit","c":[46,2,16],"r":60,"h":40,"a0":0.5,"a1":2.5,"dur":25}]
```

切換 `kind` 時記得換成該 kind 的欄位:`line` 用 `a/b/look`,`orbit` 用 `c/r/h/a0/a1`,`follow` 用 `unit/off`。所有 kind 都要 `dur`。多個 shot 的 `dur` 加起來最好接近幕的 `dur`。

### 加一個事件標記

在該幕的 `events` 陣列加一筆。`x/z` 是地圖座標,`at` 是幕內秒,`tag` 用 `史` 或 `演義`:

```json
{"at":9,"x":-128,"z":-76,"t":"關雲長義釋曹操","tag":"演義"}
```

### 加一張計策卡

在該幕加(或設定)`strat`(每幕一張):

```json
"strat":{"at":3,"name":"借東風","by":"諸葛亮 七星壇祭風","tag":"演義",
  "desc":"萬事俱備,只欠東風——史家多認為乃冬至前後江上東南風之天候。"}
```

### 加一個 fx 事件(箭雨 / 點燃)

在該幕加(或補進)`fx` 陣列。一波火箭齊射:

```json
{"at":14.5,"type":"volley","from":[-12,2],"to":[-50,-16],"n":60,"fire":true}
```

點燃某支船隊並震動:

```json
{"at":10,"type":"ignite","unit":"caoNavy","shake":2.2}
```

只能用 `volley / ignite / shake / campFire` 這四種 `type`;`ignite` 的 `unit` 必須是合法單位鍵(`caoMain / caoNavy / caoRen / liuArmy / liuFleet / sunFleet / hgFleet`)。

---

## 複製即用範例(一個 fx 事件 + 一幕)

以下是一個含 fx 事件的最小完整幕,可直接貼進 `acts` 陣列:

```json
{
  "key":"範例幕","era":"建安十三年 冬十一月","title":"火攻演示","dur":18,"env":"inferno",
  "narr":"火烈風猛,船往如箭,盡燒北船。",
  "power":{
    "cao":["折損過半",45,"水陸大潰"],
    "sun":["30,000",15,"全線總攻"],
    "liu":["約 20,000",10,"水陸並進"]
  },
  "shots":[
    {"kind":"follow","unit":"hgFleet","off":[10,22,-34],"dur":9},
    {"kind":"orbit","c":[-42,4,-11],"r":88,"h":42,"a0":0.5,"a1":2.3,"dur":9}
  ],
  "set":{"hgFleet":{"path":[[14,8],[-16,-2],[-38,-9]],"dur":10},"wind":true},
  "fx":[
    {"at":4.5,"type":"ignite","unit":"hgFleet"},
    {"at":8,"type":"ignite","unit":"caoNavy","shake":2.2},
    {"at":8,"type":"campFire","camp":"campWulin"},
    {"at":10,"type":"volley","from":[-6,6],"to":[-44,-12],"n":60,"fire":true}
  ],
  "events":[{"at":11,"x":-38,"z":-9,"t":"火船衝陣・盡燒北船","tag":"史"}]
}
```

---

## 驗收

1. 結構/契約驗:

   ```bash
   node tools/validate-data.mjs
   ```

   應印出 `PASS`。若改了 JSON 結構,先確認此指令通過(它會檢查 `battlefield.json` 指到的各 `data` 路徑存在、欄位齊全)。

2. 人類播放時間軸:在瀏覽器開 `index.html`,逐幕走一遍,確認你改/加的幕在對的時間出現對的運鏡、事件卡、計策卡、特效(箭雨/火攻/震動/燒營),以及往回跳幕(scrub)時世界狀態正確。

> 提醒:本檔是純資料。改完不需重編譯,重新整理頁面即可載入新的 `scene.json`。`fx` 只接受 `volley / ignite / shake / campFire` 四種 `type`——不要新增特效型別。
