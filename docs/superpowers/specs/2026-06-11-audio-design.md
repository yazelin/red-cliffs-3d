# 赤壁之戰 3D — 電影級音訊設計(配樂/音效/旁白)

日期:2026-06-11
狀態:設計已與 yazelin 對話確認,待 spec 審閱

## 目標

為 `index.html` 的九幕 3D 戰場加上:

1. 各幕電影級背景配樂(情緒跟著劇情走)
2. 環境與事件音效(行軍、馬蹄、燃燒、風、刀劍、將士吶喊、箭雨、鐵索、計策靈光一閃)
3. zh-TW 紀錄片腔旁白,逐幕解說歷史
4. 完成後**只留本機預覽、不 push**;yazelin 拍板後才公開發佈

## 已拍板的決策

| 決策 | 結論 |
|---|---|
| 配樂來源 | CC0 真實音檔優先(Freesound API + Wikimedia Commons + OpenGameArt),找不到的幕退 Web Audio 合成 |
| 音效來源 | 程序化合成為主(風/火/箭雨/馬蹄/鐘磬);喊殺、人群吶喊等合成弱項抓 CC0 真實錄音 |
| 旁白 | edge-tts 預產 mp3;YunJhe(男)+ HsiaoChen(女)兩套都產,本機試聽後定稿刪一套 |
| 幕長 | 旁白為主,各幕 `dur` 延長到「旁白長度+緩衝」,全片約 3.5–4 分鐘 |
| 選曲品質把關 | Gemini 2.5-flash 音訊理解代聽海選(已實測準確),入圍曲做本機試聽頁由 yazelin 終審 |
| 授權 | 只收 CC0;逐檔記錄來源與授權於 README |

## 架構

### 音訊匯流排(Web Audio,單一 AudioContext)

```
master ─┬─ music bus(配樂,旁白播放時 ducking 至 ~40%)
        ├─ sfx bus(環境層 + 事件層)
        └─ narration bus(HTMLAudioElement → MediaElementSource)
```

- 瀏覽器 autoplay 限制:開場標題改為「點擊進入」入口,點擊時 resume AudioContext
- 控制列新增:總音量、旁白開關、字幕開關、(預覽期)男/女聲切換
- 跳幕/快轉:旁白即停換段、配樂 crossfade(~1.5s);0.5×/2× 時旁白 `playbackRate` 跟隨且 `preservesPitch`

### 配樂:每幕一個 cue

| 幕 | 情緒方向 | 搜尋關鍵詞方向 |
|---|---|---|
| 一 大軍南下 | 沉重行軍鼓+低音 drone,壓迫 | war drums march, ominous drone |
| 二 孫劉同盟 | 箏/簫對話,廟堂縱橫 | guzheng, chinese traditional calm |
| 三 初戰赤壁 | 緊張弦樂 ostinato+鼓點 | tense strings battle percussion |
| 四 鐵索連環 | 低迴 drone+金屬點綴 | dark ambient metal drone |
| 五 苦肉計 | 黃昏孤簫,隱忍 | chinese flute melancholy, dizi xiao solo |
| 六 東風驟起 | 風聲漸強+弦樂爬升 | rising tension crescendo wind |
| 七 火燒赤壁 | 全編制高潮:急鼓、鈸、弦樂狂奔 | epic battle drums intense climax |
| 八 敗走華容 | 殘破慢板、孤簫嗚咽 | sad defeat ambient, mournful flute |
| 九 天下三分 | 主題開闊再現,收束 | epic resolution majestic ending |

選曲流程(已實測可行):

1. Freesound API(`license:"Creative Commons 0"` + `duration` 篩選)+ Commons API + OpenGameArt,每幕收 3–8 個候選
2. 下載 preview-hq-mp3 → ffprobe 長度/格式
3. Gemini 2.5-flash 固定清單代聽:實際樂器/節奏能量/有無人聲/現代感(槍聲合成器)/可否 loop/適配分 0–10
4. 淘汰後入圍曲列入本機試聽頁(`audition.html`,不進正式頁)由 yazelin 點播終審
5. 找不到合格曲的幕 → Web Audio 合成 cue(戰鼓/Karplus-Strong 古琴/簫/弦樂 pad/drone),用 OfflineAudioContext 渲染 wav 丟 Gemini 批改後才採用

實測校準:代聽必用 gemini-2.5-flash 以上(flash-lite 會把合成測試音聽成木吉他);下載數/標題不可信(下載榜首的 "war drums" 實為 hip-hop 刮碟包,代聽淘汰)。

### 音效

**環境持續層**(隨幕 `env` 切換,合成):

- 風:filtered noise,東風幕(六)增強,inferno 幕(七)轉熱風
- 江水:低頻 noise 緩波
- 火場:roar(brown noise)+ 嗶剝(隨機短脈衝),掛七、八幕燒營狀態

**事件觸發層**(掛現有 timeline 鉤點):

| 音效 | 來源 | 鉤點 |
|---|---|---|
| 行軍腳步 | 合成(節奏化 thump) | 各幕 `set` 路徑移動中 |
| 馬蹄 | 合成(雙連音脈衝) | 一、八幕騎兵移動 |
| 箭雨破空 | 合成(noise sweep) | 既有 `volleys.push` |
| 刀劍交鋒 | 合成(金屬 FM+noise) | 三、七幕接戰 |
| 將士吶喊 | **CC0 真實錄音** | 三、七幕接戰、火攻衝陣 |
| 鐵索鏗鏘 | 合成(金屬撞擊)或 CC0 | 四幕連環 |
| 火船爆燃 | 合成(boom+debris) | 七幕火攻事件 |
| 計策靈光一閃 | 合成(鐘磬+swoosh) | 計策卡顯示 |

### 旁白

- 九段紀錄片腔文稿,維持現有「史/演義」分流嚴謹度,每段約 15–25 秒
- edge-tts(venv 安裝)產兩套:`assets/narration/yunjhe/scene{1..9}.mp3`、`assets/narration/hsiaochen/...`
- ffprobe 量實際長度 → 每幕 `dur = max(現有, 旁白長 + 3s)` 寫回 SCENES
- 字幕列同步顯示旁白文字(可關)
- 配樂 ducking:旁白 onplay 壓 music bus 至 0.4,onended 回升(各 ~0.6s ramp)

## 驗證

- OfflineAudioContext 渲染各合成 cue/音效 → 程式化斷言非靜音 + Gemini 批改
- headless Chrome(MCP):console 無錯、九幕逐幕切換、AudioContext state、旁白檔 200
- 試聽頁 `audition.html`:每幕候選曲 + 代聽筆記 + 播放鍵
- 正式預覽:本機 http server,yazelin 全片走一遍
- 最終驗證清單隨交付附上(per-change verify checklist)

## 發佈與授權

- 所有 commit 留本機,**不 push**,yazelin 看過拍板才發佈
- README 新增「音訊」章節:逐檔列 Freesound/Commons 來源連結 + CC0 標示;實驗記錄補上這一輪(含 AI 代聽選曲管線)
- 落選的旁白聲音與候選音檔在定稿後移除,不進正式 repo

## 不做的事(YAGNI)

- 不做近距離單人語音喊話(合成假、CC0 中文素材難找)
- 不做音樂跟 0.5×/2× 變速連動(配樂維持原速,只有旁白跟速)
- 不引入 build step、不加套件依賴;新增檔案僅 `assets/`、`audition.html`(暫時)、spec/README
