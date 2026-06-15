# 音訊 manifest 外部化(P2b)Implementation Plan

> Workflow: author core (audio.json + engine) + audio.md SOP in parallel → adversarial URL/cue/dispatcher-equivalence verify → integrate.

**Goal:** 音訊設定 → `data/audio.json`(music/narration/sfx 檔對應 + AUDIO_CUES 宣告式 cue);引擎讀 manifest;`dispatchAudioCue` 取代閉包。與 main 行為等價(URL/cue/呼叫等價),`battlefield.json` pending 清空。

**Spec:** `docs/superpowers/specs/2026-06-16-audio-manifest-design.md`

**Source of truth:** index.html 音訊引擎(Music SRC :1156、Narration :1214-1262、Sfx playFile :1409-1411、AUDIO_CUES :1477-1493、onScene :1494-1500)。

---

### Task 1: data/audio.json + 引擎讀 manifest + dispatchAudioCue + battlefield/schema(core)
- [ ] `data/audio.json`:music.scenes(scene1-9 路徑)+ theme;narration(voices/default/pathPattern/cues);sfx(dir/files);cues(AUDIO_CUES 轉宣告式,見 spec 詞彙;複合閉包拆多事件;burst 第七幕 23.4)。
- [ ] index.html:Music SRC 讀 AUDIO.music.scenes;主題曲讀 theme;Narration 路徑/voices 讀 AUDIO.narration(pathPattern{voice}{n} 等價原式);cues.json 路徑讀 manifest;Sfx playFile dir 讀 AUDIO.sfx.dir;AUDIO_CUES 讀 AUDIO.cues;加 `dispatchAudioCue(e)`(synth/sfx/sword/burst)於 Sfx 內;onScene forEach 改走 dispatchAudioCue。合成器/ducking/字幕不動。載入:併入既有 top-level await 或 audio init。
- [ ] battlefield.json:加 data.audio;pending=[]。schema/audio.schema.json + validator(audio 存在、cue.type enum、路徑存在性)。
- [ ] 驗:node parse、node --check、`node tools/validate-data.mjs` PASS(加 audio);URL 等價 + cue≡閉包 自查。

### Task 2: docs/authoring/audio.md(SOP,parallel)
- [ ] 對照 audio.json 寫:music/narration/sfx manifest 欄位、cue 詞彙(synth/sfx/sword/burst)、怎麼換配樂/加旁白聲線/加音效 cue;範例 + 驗收。只用真欄位/詞彙。

### Task 3: 整合驗證
- [ ] URL 等價(music×9+theme、narration 2聲×9、sfx 各檔)逐一 === 原內聯。
- [ ] cue≡閉包(每幕每事件 inst/name/v/at;burst n/interval;拆分正確);dispatchAudioCue 呼叫等價。
- [ ] 路徑存在性(assets 檔都在);zero 其他變動(合成器/ducking 不動);validator PASS;node --check。

## Self-Review
- Spec 覆蓋:audio.json(T1)、引擎 manifest 讀取+dispatchAudioCue(T1)、schema/validator(T1)、SOP(T2)、URL/cue 等價驗(T3)✓。
- 風險:URL 拼錯/cue 漏→T3 逐一比對 + 路徑存在性;合成器誤動→T3 diff;burst/sword 特殊→spec 詞彙明列。
