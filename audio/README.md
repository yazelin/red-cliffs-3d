# 旁白音檔

九幕旁白（`narr_1.mp3` 〜 `narr_9.mp3`），文本即 `index.html` 內各幕的 `narr` 欄位（白話版，與語音一字對應）。

- 音色：志玲 voice clone（CosyVoice 3 / Fun-CosyVoice3-0.5B，zero-shot）
- 種子：`ref4.wav`（10 秒純中文片段；A/B 後人耳選定，淘汰混英文的 peak_10s_seed）
- 文本：文言原稿改寫為白話（文言版 CV3 唸不順，A/B 確認白話明顯較好）
- 生成：`build_audiobook.py` baseline 參數（speed 1.0、whisper-auto ref text、loudnorm -16 LUFS）
- 品檢：拼音級 CER ≤ 0.15 雙引擎（whisper-small + qwen-asr）全文驗證；字級 CER 會被三國專名同音字干擾，不作 gate
- 格式：mp3 mono 24 kHz 64 kbps
