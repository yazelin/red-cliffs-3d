# 旁白音檔

九幕旁白（`narr_1.mp3` 〜 `narr_9.mp3`），文本即 `index.html` 內各幕的 `narr` 欄位（白話版，與語音一字對應）。

- 音色：AI 合成女聲（CosyVoice 3 / Fun-CosyVoice3-0.5B，zero-shot voice clone）
- 文本：文言原稿改寫為白話（TTS 唸文言不順，A/B 確認白話明顯較好）
- 品檢：拼音級 CER ≤ 0.15 雙引擎（whisper-small + qwen-asr）全文驗證；字級 CER 會被三國專名同音字干擾，不作 gate
- 格式：mp3 mono 24 kHz VBR（~32 kbps，九檔共 ~712 KB）
- 重生流程：白話文本 → CosyVoice 3 zero-shot（loudnorm -16 LUFS）→ 雙引擎驗證 → ffmpeg 壓 mp3
