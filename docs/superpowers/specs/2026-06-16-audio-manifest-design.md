# 音訊 manifest 外部化(P2b)設計 — 編輯器轉換

日期:2026-06-16
狀態:autonomous run;待最終人工(聽覺)驗收。

## 背景

編輯器轉換 P2b。P2a(場景 scene.json)已 ship。P2b 把**音訊設定**外部化成 `data/audio.json`,讓 package 的最後一層(音訊)也成為資料 → `battlefield.json` 的 `pending` 清空,**整張戰場=純資料**。配樂/旁白/音效的 mp3 與程序合成器(Sfx synth)是引擎/資產,不動;外部化的是「**哪個檔配哪幕、旁白聲線/路徑、每幕音效 cue 時間表**」。

## 關鍵發現

`index.html` 音訊引擎內聯資料:
- **Music**:`SRC=[1..9].map(n=>'assets/music/scene${n}.mp3')`;主題曲=scene9。
- **Narration**:`voice` yunjhe/hsiaochen;路徑 `assets/narration/${voice}/scene${i+1}.mp3`;`assets/narration/cues.json`。
- **Sfx**:`playFile` 自 `assets/sfx/${name}.mp3`(battlecry/chains/sword1-4);**`AUDIO_CUES`(:1477-1493)是每幕事件音效閉包**(同 fx 問題)——`play(inst,{v})`/`playFile(name,v)`/`sword(v)`/一個 setTimeout 連發。

## 已拍板決策

| 決策 | 結論 |
|---|---|
| 範圍 | 外部化音訊 manifest(檔對應 + 旁白設定 + AUDIO_CUES);程序合成器(Sfx BUILD)留程式 |
| AUDIO_CUES | 宣告式音效事件詞彙 + `dispatchAudioCue`(同 P2a 的 dispatchFx 模式) |
| 行為 | 與 main 等價(URL 逐一相同、cue 逐一相同、dispatcher≡閉包);結構/呼叫等價驗,聲音由人最終聽 |
| manifest | `battlefield.json` 加 `audio`,`pending` 清空(=[]) |
| 契約+SOP | `schema/audio.schema.json` + validator;`docs/authoring/audio.md` |

## 音效事件詞彙(涵蓋 AUDIO_CUES 全部)

| type | 欄位 | 對應原 |
|---|---|---|
| `synth` | inst('drum'|'boom'), v | `play(inst,{v})` |
| `sfx` | name, v | `playFile(name,v)` |
| `sword` | v | `sword(v)`(隨機 sword 變體) |
| `burst` | inst, n, interval, v | setTimeout 連發(第七幕 23.4「雷鼓大進」6×drum@0.4s) |

複合閉包拆多事件(同 P2a):如第三幕 9.5 = synth drum + sfx battlecry;第七幕 23.4 = burst + sfx battlecry。

## 目標資料 `data/audio.json`
```json
{
  "music": { "scenes": ["assets/music/scene1.mp3", … 9 …], "theme": "assets/music/scene9.mp3" },
  "narration": { "voices": ["yunjhe","hsiaochen"], "default": "yunjhe",
    "pathPattern": "assets/narration/{voice}/scene{n}.mp3", "cues": "assets/narration/cues.json" },
  "sfx": { "dir": "assets/sfx", "files": ["battlecry","chains","sword1","sword2","sword3","sword4"] },
  "cues": { "0": [ {"at":2,"type":"synth","inst":"drum","v":0.5}, … ], "2": […], "3":[…], "6":[…], "8":[…] }
}
```

## 引擎(index.html)
- 模組頂層或音訊 init:`const AUDIO = await fetch('data/audio.json')`(或併入既有 await)。
- Music:`SRC` 改讀 `AUDIO.music.scenes`;主題曲讀 `AUDIO.music.theme`。
- Narration:`voices`/`default`/路徑由 `AUDIO.narration`(pathPattern 以 voice/n 代入,等價於原 `assets/narration/${voice}/scene${i+1}.mp3`);cues.json 路徑讀 manifest。
- Sfx:`playFile` 的 dir 讀 `AUDIO.sfx.dir`;`AUDIO_CUES` 改讀 `AUDIO.cues`;新增 `dispatchAudioCue(e)`(synth/sfx/sword/burst)於 Sfx 內(play/playFile/sword 在 scope);`onScene` 的 `forEach(c=>pending.push(c))` 改 `forEach(e=>pending.push({at:e.at,fn:()=>dispatchAudioCue(e)}))`。
- 程序合成器(BUILD/play 的合成)與 OfflineAudioContext 測試**不動**。

## 驗證(結構/呼叫等價;聲音人聽)
1. **URL 等價**:manifest + 引擎產生的每個 music/narration/sfx URL === 原內聯 URL(逐一列出比對:music scene1-9、theme、narration 兩聲線×九幕、sfx 各檔)。
2. **cue ≡ 閉包**:`AUDIO.cues` 逐事件還原原 AUDIO_CUES 閉包的呼叫(inst/name/v/at;burst 的 n/interval;複合拆分);`dispatchAudioCue(e)` 呼叫 === 原閉包。
3. **node load-check**:audio.json parse;每 cue.type∈詞彙;每 music/sfx 路徑指向**存在**的 assets 檔。
4. `node --check`、`node tools/validate-data.mjs` PASS(加 audio)。
5. **零其他變動**:git diff 僅音訊 init + AUDIO_CUES→manifest + dispatchAudioCue;合成器/其他引擎不動。
6. 最終 yazelin **聽**一遍九幕(配樂切換/旁白/箭雨刀劍鼓/火攻音景)確認與舊版一致。

## 不做(YAGNI)
- 不動程序合成器、ducking、autoplay、字幕邏輯。不重做海選。不抽 repo(P3)。
