# 赤壁 3D 音訊(配樂/音效/旁白)Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 為 `index.html` 九幕加上 CC0 配樂、合成+真實混合音效、edge-tts 雙聲旁白與同步字幕,全程本機驗證、不 push。

**Architecture:** 單一 AudioContext 三匯流排(music/sfx/narration);配樂走「Freesound CC0 海選 → Gemini 2.5-flash 代聽 → audition.html 用戶終審」管線;音效合成為主、喊殺等用 CC0 真檔;旁白 edge-tts 預產 mp3+SRT,幕長隨旁白延長且 shots 等比縮放。

**Tech Stack:** Web Audio API、edge-tts(venv)、Freesound APIv2、Gemini 2.5-flash 音訊理解、ffmpeg/ffprobe、headless Chrome(MCP)驗證。

**Spec:** `docs/superpowers/specs/2026-06-11-audio-design.md`

**重要既有掛載點(index.html,行號為 commit ae2c2f7 時點):**

| 掛載點 | 位置 | 用途 |
|---|---|---|
| `start(auto)` | :1193 | 開場按鈕點擊 → `audio.unlock()`(瀏覽器手勢) |
| `gotoPhase(i,viaScrub)` | :1065 | 幕切換 → 配樂 crossfade、旁白換段 |
| `showStrat(s)` | :1033 | 計策卡 → 靈光一閃 chime |
| `fireVolley(...)` | :600 | 箭雨 → 破空 whoosh |
| `applySet` 的 `d.path` 分支 | :1058 | 部隊開拔 → 行軍/馬蹄循環音登記 |
| 第七幕 `fx` | :983-987 | 火船/燒營/震動 → 爆燃 boom |
| `togglePlay` | :1152 | 暫停 → narration.pause()、music bus 壓低 |
| `bSpeed` handler | :1157 | 變速 → `narration.playbackRate=speed`(preservesPitch) |
| `loop()` 內 `windCur` :1244、`emitters` :1237 | 每幀 | 風/火環境音強度跟隨 |
| `PHASES[i].dur` / `shots` | :912-1014 | 幕長延長 + shots 等比縮放 |
| `p.narr` | 各幕 | 旁白文稿底稿(文言紀錄片體,改寫口語) |

---

### Task 1: 環境準備

**Files:** Create `.gitignore`、`.venv-audio/`(不進 git)、`audio-work/`(不進 git)

- [ ] **Step 1.1** 建 venv 並裝 edge-tts:

```bash
cd /home/ct/red-cliffs-3d
python3 -m venv .venv-audio && .venv-audio/bin/pip install -q edge-tts
.venv-audio/bin/edge-tts --list-voices | grep zh-TW   # 預期看到 HsiaoChen/HsiaoYu/YunJhe
```

- [ ] **Step 1.2** 建 `.gitignore`:

```
.venv-audio/
audio-work/
```

- [ ] **Step 1.3** `mkdir -p audio-work/{candidates,reports} assets/narration/{yunjhe,hsiaochen} assets/music assets/sfx`
- [ ] **Step 1.4** Commit:`chore: 音訊工作環境(venv/gitignore/目錄)`

---

### Task 2: 旁白文稿 + 雙聲 TTS + 字幕

**Files:** Create `narration/script.json`、`narration/generate.py`、`assets/narration/{yunjhe,hsiaochen}/scene{1..9}.mp3`、`assets/narration/cues.json`

- [ ] **Step 2.1** 寫 `narration/script.json`:九段口語紀錄片腔(以各幕 `p.narr` 為底稿改寫;維持史/演義分流——演義內容口播時明說「演義裡」;每段 70–120 字、預估 15–25 秒)。格式:

```json
[
  {"scene": 1, "title": "大軍南下", "text": "建安十三年秋,曹操親率大軍南下荊州。劉琮舉州投降,劉備倉皇南撤,長坂坡一戰幾乎全軍覆沒。曹操兼併荊州水軍,號稱八十萬,順江東下——目標,江東。"},
  {"scene": 2, "...": "(其餘八段同格式,實作時逐段撰寫)"}
]
```

(文稿內容在 Step 2.1 實作時完整寫出九段,不留空段;寫完先給 yazelin 過目再產音。)

- [ ] **Step 2.2** 寫 `narration/generate.py`:對每段 × 兩聲音呼叫 edge-tts,同時收 WordBoundary 事件產生句級字幕 cue:

```python
import asyncio, json, subprocess, edge_tts
VOICES = {"yunjhe": "zh-TW-YunJheNeural", "hsiaochen": "zh-TW-HsiaoChenNeural"}
RATE = "-8%"   # 紀錄片腔放慢一點
async def gen(scene, text, vkey, vname):
    out = f"assets/narration/{vkey}/scene{scene['scene']}.mp3"
    cues, cm = [], edge_tts.Communicate(text, vname, rate=RATE)
    with open(out, "wb") as f:
        async for chunk in cm.stream():
            if chunk["type"] == "audio": f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                cues.append({"t": chunk["offset"]/1e7, "w": chunk["text"]})
    dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "format=duration","-of","csv=p=0",out]))
    return {"dur": round(dur,2), "cues": cues}
```

主程式跑完輸出 `assets/narration/cues.json`:`{"1": {"text":..., "yunjhe": {dur,cues}, "hsiaochen": {dur,cues}}, ...}`(字幕顯示用 cue 把詞聚成 12–20 字一行)。

- [ ] **Step 2.3** 執行 `.venv-audio/bin/python narration/generate.py`,驗證:18 個 mp3 存在、ffprobe 全部 > 10s、cues.json 九幕齊。
- [ ] **Step 2.4** 抽一幕丟 Gemini 2.5-flash 聽寫驗證(發音/斷句正常、無爆音)。
- [ ] **Step 2.5** Commit:`feat: 九幕旁白文稿 + 雙聲 TTS 音檔與字幕 cue`

---

### Task 3: CC0 配樂海選管線

**Files:** Create `audio-work/hunt.py`、`audio-work/reports/scene{1..9}.json`

- [ ] **Step 3.1** 寫 `audio-work/hunt.py`,核心流程(key 自 `~/.config/freesound.env` 與 `/home/ct/gemini/.env` 讀):

```python
# 每幕設定:spec 的搜尋關鍵詞方向,每幕 2-4 組 query
# 1) Freesound: /apiv2/search/text/  filter='license:"Creative Commons 0" duration:[30 TO 300]'
#    fields=id,name,duration,license,previews,username  sort=rating_desc 與 downloads_desc 各取一輪
# 2) Wikimedia Commons API(list=search srnamespace=6 filetype:audio)取 extmetadata 確認 CC0/PD
# 3) 下載 preview-hq-mp3 到 audio-work/candidates/scene{n}-{id}.mp3
# 4) Gemini 2.5-flash 固定清單代聽(實測過的 prompt):
#    樂器/節奏能量弧/有無人聲/現代感(槍聲合成器電子)/可否 loop/該幕情境適配分 0-10 + 一行理由
#    模型 fallback 順序:gemini-2.5-flash → gemini-flash-latest;絕不用 flash-lite(實測誤判)
# 5) 寫 reports/scene{n}.json:[{id,name,src,url,license,dur,audition:{...},verdict}]
```

注意事項(實測踩過):Freesound license filter 必須是 `license:"Creative Commons 0"`(帶引號全名);Commons API 要帶 User-Agent;下載榜/標題不可信,一切以代聽為準;Gemini 503 要 retry/backoff。

- [ ] **Step 3.2** 逐幕跑,目標每幕 ≥ 2 首適配分 ≥ 7 的入圍曲;query 撈不到就換關鍵詞再跑(例:scene 5 試 `dizi solo` / `xiao flute` / `erhu melancholy`)。連換 3 輪仍無 → 該幕標記 `fallback: synth`。
- [ ] **Step 3.3** 同場加映 SFX 真檔海選(同管線、改 duration 篩 `[3 TO 60]`):
  - 喊殺/軍陣吶喊:`battle cry crowd`、`army shouting crowd roar`、`medieval battle crowd`
  - 鐵索(備援,合成不像再用):`heavy chain clank metal`
  - 入圍標準:無現代語言可辨識字句、無槍砲、可疊在配樂下。
- [ ] **Step 3.4** Commit(只 commit `hunt.py`;candidates/reports 在 gitignore 內):`feat: CC0 配樂/音效海選管線`

---

### Task 4: 試聽頁 + 用戶終審【BLOCKING GATE】

**Files:** Create `audition.html`(暫存,定稿後刪)

- [ ] **Step 4.1** 產 `audition.html`:逐幕一個區塊——幕名/情緒方向、每首候選:播放鍵(`<audio controls>` 指向 `audio-work/candidates/`)、來源連結、授權、Gemini 代聽筆記、適配分。SFX 候選同列一區。
- [ ] **Step 4.2** 起 `python3 -m http.server 8137`,把 `http://localhost:8137/audition.html` 給 yazelin。
- [ ] **Step 4.3** **等 yazelin 逐幕點選**(回覆格式自由,例「一幕 A、二幕 B、五幕用合成」)。等待期間可先做 Task 7–9 的引擎(不依賴選曲結果)。

---

### Task 5: 定稿音檔後製

**Files:** Create `assets/music/scene{1..9}.mp3`(或該幕標 synth 則無檔)、`assets/sfx/*.mp3`、`audio-work/finalize.sh`

- [ ] **Step 5.1** 對每首定稿曲:Freesound 抓原始檔(preview 已是 128k mp3 可直接用;原檔更高品質就用 `/apiv2/sounds/<id>/download/` — 需 OAuth2,不值得,**直接用 preview-hq**)。處理鏈:

```bash
ffmpeg -i in.mp3 -af "loudnorm=I=-18:TP=-1.5:LRA=11,afade=t=in:d=1.5,areverse,afade=t=in:d=2,areverse" -ar 44100 -b:a 128k assets/music/sceneN.mp3
```

(統一響度 -18 LUFS、頭尾 fade 以利 crossfade/loop。)

- [ ] **Step 5.2** SFX 真檔同樣 loudnorm(I=-16)進 `assets/sfx/`(檔名:`battlecry.mp3`、`chains.mp3`…)。
- [ ] **Step 5.3** 記錄授權:`assets/CREDITS.md` 逐檔列「檔名 | 來源 URL | 作者 | CC0」。
- [ ] **Step 5.4** Commit:`feat: 定稿配樂/音效音檔 + CC0 來源記錄`

---

### Task 6: index.html 音訊引擎核心(buses / unlock / UI)

**Files:** Modify `index.html`(`</script>` 前新增 `/* ════════ audio engine ════════ */` 區塊;控制列 HTML;CSS)

- [ ] **Step 6.1** 核心物件(新增於 PHASES 定義後):

```js
const AudioEngine = (() => {
  let ctx, master, music, sfx, narr;          // GainNodes
  let unlocked = false;
  function unlock(){
    if (unlocked) return; unlocked = true;
    ctx = new (window.AudioContext||window.webkitAudioContext)();
    master = ctx.createGain(); master.connect(ctx.destination);
    music = ctx.createGain(); sfx = ctx.createGain(); narr = ctx.createGain();
    [music,sfx,narr].forEach(g=>g.connect(master));
    music.gain.value=.8; sfx.gain.value=.9; narr.gain.value=1;
    Music.init(ctx, music); Sfx.init(ctx, sfx); Narration.init(ctx, narr);
  }
  function duck(on){ if(!ctx)return; music.gain.linearRampToValueAtTime(on?.32:.8, ctx.currentTime+.6); }
  return { unlock, duck, get ctx(){return ctx}, master:()=>master };
})();
```

- [ ] **Step 6.2** `start(auto)` :1193 首行加 `AudioEngine.unlock();`。
- [ ] **Step 6.3** 控制列新增(沿用既有 `.btn` 樣式):總音量滑桿(操作 `master.gain`)、`旁白` 開關、`字幕` 開關、預覽期 `男聲/女聲` 切換鈕;新增 `#subtitle` div(置底置中,金邊深底,沿用既有配色變數)。
- [ ] **Step 6.4** headless 驗證:點開場鈕後 `AudioEngine.ctx.state === 'running'`、console 無錯。Commit:`feat: 音訊引擎核心與控制列`

---

### Task 7: 配樂播放器 + 旁白 + 字幕 + ducking

**Files:** Modify `index.html`

- [ ] **Step 7.1** `Music` 模組:每幕一個 `{type:'file', url}` 或 `{type:'synth', cue}` 的 `MUSIC_MAP`;檔案曲用 fetch+decodeAudioData 快取、`AudioBufferSourceNode` loop 播放;`Music.play(sceneIdx)` 做 1.5s equal-power crossfade(舊 source ramp down 後 stop):

```js
function crossfadeTo(node){            // node = 新 source 接的 per-track gain
  const t = ctx.currentTime;
  if (cur){ cur.gain.gain.setValueAtTime(cur.gain.gain.value,t);
            cur.gain.gain.linearRampToValueAtTime(0,t+1.5);
            cur.src.stop(t+1.6); }
  node.gain.gain.setValueAtTime(0,t);
  node.gain.gain.linearRampToValueAtTime(1,t+1.5);
  cur = node;
}
```

- [ ] **Step 7.2** `Narration` 模組:單一 `new Audio()` 元素接 `MediaElementSource`;`Narration.play(sceneIdx)` 設 `src=assets/narration/${voice}/scene{n}.mp3`、`playbackRate=speed`、`preservesPitch=true`;`onplay→AudioEngine.duck(true)`、`onended/onpause→duck(false)`;字幕:`timeupdate` 時依 `cues.json`(啟動時 fetch 一次)找 `currentTime` 所在行,寫入 `#subtitle`。
- [ ] **Step 7.3** 接 `gotoPhase` 尾端:`Music.play(i); Narration.play(i);`(`phase===-1→0` 首次也走這裡,不需特例)。接 `togglePlay`:暫停時 `Narration.pause()`,恢復時 `resume()`。接 `bSpeed`:`Narration.setRate(speed)`。
- [ ] **Step 7.4** headless 驗證:逐幕 goto、`document.querySelector('#subtitle').textContent` 有字、network 面板 narration mp3 全 200、跳幕舊旁白即停。Commit:`feat: 配樂 crossfade + 旁白播放 + 同步字幕 + ducking`

---

### Task 8: 音效層(環境 + 事件)

**Files:** Modify `index.html`

- [ ] **Step 8.1** `Sfx` 合成器集(全部走 `sfx` bus;每個合成器是「建一條短節點鏈、放完自斷」或「常駐 loop + 強度參數」):

常駐環境層(`Sfx.ambient`,每幀由 `loop()` 餵強度):

```js
// 風:loop 的 white noise buffer → BiquadFilter(bandpass 400-900Hz, Q .5) → gain
//    每幀: windGain.gain.value = .05 + windCur*.5   (六幕東風自然變強)
// 江水:brown noise → lowpass 220Hz → LFO(.07Hz) 調幅 → gain .12(恆定)
// 火場:brown noise → lowpass 500Hz → gain = fireAmt*.6
//    + 嗶剝:每 80-300ms 隨機,impulse(極短 noise burst → highpass 2k) 音量 fireAmt
//    fireAmt = Math.max(campWulinFire.cur, ...U.caoNavy.ships.map(s=>s.fire?s.fire.cur:0)) — 在 loop() :1237 emitters 迴圈順手取 max
```

事件合成器(one-shot):

```js
// 戰鼓 drum(f=55→40Hz sine pitch-drop 0.3s + noise thump)— 行軍節奏、幕高潮
// 馬蹄 hooves(雙連音:2 個 8ms noise burst → bandpass 700Hz,間隔 90ms,循環 4Hz)
// 箭雨 whoosh(white noise → bandpass 1.2k→3k sweep 0.5s → gain 包絡)
// 刀劍 clash(FM:carrier 2.8kHz/mod 420Hz 0.12s + metallic noise tail)
// 鐵索 chain(3 連發 clash 變體,載波 1.6k,加 0.4s decay)
// 爆燃 boom(40Hz sine 1.2s decay + brown noise burst + 0.3s 後 debris 嗶剝×6)
// 靈光 chime(正弦 1318/1760/2637Hz 三音琶音,各 1.5s decay + noise swoosh 0.6s)
```

真檔 one-shot:`Sfx.playFile('battlecry')`(decodeAudioData 快取,同配樂)。

- [ ] **Step 8.2** 掛鉤(全部用 `audioCue` 屬性塞進既有 `pending` 機制,不另造時間軸——在 `gotoPhase` 組 `pending` 處 :1086-1091 後追加每幕的音效 cue 表 `AUDIO_CUES[i]`,格式同 `{at, fn}`):
  - `showStrat` :1039 尾加 `Sfx.chime()`
  - `fireVolley` :600 首行加 `Sfx.whoosh(n)`(n 大音量大)
  - `applySet` :1058 `d.path` 分支:`Sfx.march(id, d.dur||8)`(id 在 `CAVALRY=['caoMain','caoVan']` 內走馬蹄,否則行軍鼓步;`inst===true` 不觸發)
  - 七幕 fx :983-987:`at:4.5` 加 boom(火船點燃)、`at:10` 加 boom+battlecry、`at:12` 加 boom;三/七幕接戰時段每 2-4s 隨機 `Sfx.clash()`(寫進 `AUDIO_CUES`)
  - 四幕:`at:7` 鐵索 chain ×3
- [ ] **Step 8.3** headless 驗證 + OfflineAudioContext 單測頁 `audio-work/test-synth.html`:逐一渲染每個合成器 2s,斷言 RMS > 0.001(非靜音)且 peak < 1.0(不爆),console 輸出 PASS/FAIL 表。
- [ ] **Step 8.4** 合成 cue 整段渲染成 wav(若有 `fallback: synth` 的幕)→ Gemini 批改 →(必要時)調參重渲染。
- [ ] **Step 8.5** Commit:`feat: 環境/事件音效層(合成+CC0 真檔)`

---

### Task 9: 幕長延長 + 運鏡縮放

**Files:** Modify `index.html` PHASES :912-1014

- [ ] **Step 9.1** 由 `cues.json` 取定稿聲音的每幕旁白長 `narrDur`,新幕長 `newDur = Math.max(oldDur, ceil(narrDur)+4)`;手動改寫各幕 `dur`,同幕每個 shot 的 `dur` 乘 `newDur/oldDur`(保留一位小數,總和=newDur)。`set` 內移動 `dur` 與 `events.at` 不動。
- [ ] **Step 9.2** headless 全片走完:無提前凍鏡、最後一幕 finale 正常、`durTotal` 計算正確(:1138 自動加總,免改)。
- [ ] **Step 9.3** Commit:`feat: 幕長配合旁白延長 + 運鏡等比縮放`

---

### Task 10: 整體驗證 + README + 本機交付

**Files:** Modify `README.md`;檢查全部

- [ ] **Step 10.1** headless 完整迴歸:console 零錯誤;九幕自動播完;跳幕×5 隨機亂跳無殘留旁白/雙重配樂;0.5×/2× 旁白音高正常;靜音開關有效。
- [ ] **Step 10.2** README:新增「音訊」章節(三 bus 架構、九幕配樂表、音效一覽、旁白雙聲說明)、`assets/CREDITS.md` 連結、實驗記錄補「第二輪:音訊」(含 AI 代聽選曲管線與踩雷)。
- [ ] **Step 10.3** Commit:`docs: README 音訊章節 + 實驗記錄`
- [ ] **Step 10.4** 起 `python3 -m http.server 8137 -d /home/ct/red-cliffs-3d`,交付 `http://localhost:8137/` + 精準驗證清單(本次改了什麼→怎麼驗:開場點擊有樂聲/各幕配樂切換/旁白與字幕/七幕火攻音景/變速/靜音)。**不 push**——yazelin 看完拍板才發佈;發佈前刪 `audition.html` 與落選聲音目錄。

---

## Self-Review 記錄

- Spec 覆蓋:配樂(T3-5,7)、音效(T3,5,8)、旁白+字幕+幕長(T2,7,9)、autoplay 解鎖(T6)、變速(T7)、驗證(T8.3-8.4,9.2,10.1)、授權記錄(T5.3)、不 push(T10.4)、落選素材移除(T10.4)✓
- 型別/命名一致:`AudioEngine.unlock/duck`、`Music.play(i)`、`Narration.play/pause/setRate`、`Sfx.{chime,whoosh,march,clash,boom,playFile}`、`AUDIO_CUES[i]` 全文一致 ✓
- 已知風險:Freesound preview 128k 品質上限(可接受,網頁 BGM);`preservesPitch` 各瀏覽器前綴(Chrome OK);Gemini 503(retry 已寫進管線)。
