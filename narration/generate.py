#!/usr/bin/env python3
"""產九幕旁白:edge-tts 雙聲 mp3 + 句級字幕 cue(WordBoundary 聚行)。"""
import asyncio, json, pathlib, subprocess
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOICES = {"yunjhe": "zh-TW-YunJheNeural", "hsiaochen": "zh-TW-HsiaoChenNeural"}
RATE = "-8%"  # 紀錄片腔放慢
LINE_MAX = 18  # 字幕一行最多字數

# 破音字 TTS 替身:餵 TTS 用右邊(目標讀音的同音字),字幕顯示左邊原字。
# 同音字替代對唸對的字無害(替身=目標讀音),錯了會被修正。
SUBS = {
    "不戰而降": "不戰而祥",   # xiáng
    "詐降書":   "詐祥書",     # xiáng
    "天衣無縫": "天衣無鳳",   # fèng
    "北還":     "北環",       # huán
    "揹草":     "杯草",       # bēi(TTS 連「揹」都唸 bèi,實測確認)
    "率三萬":   "帥三萬",     # shuài(單用「率」字 TTS 會唸 lǜ,「率領/親率」反而正確)
}
def to_tts(text):
    for k, v in SUBS.items():
        text = text.replace(k, v)
    return text
def to_display(text):
    for k, v in SUBS.items():
        text = text.replace(v, k)
    return text


def probe_dur(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)]))


def words_to_lines(words, text):
    """SentenceBoundary:一句一 cue;過長句在中段標點切兩行(時間內插)。"""
    lines = []
    for w in words:
        txt = w["w"].strip("。;")
        if len(txt) > 26:
            mid = len(txt) // 2
            cut = max((txt.rfind(c, 0, mid + 6) for c in ",、——"), default=-1)
            if cut > 4:
                est = w.get("d", 4.0) * (cut / len(txt))
                lines.append({"t": round(w["t"], 2), "text": txt[:cut]})
                lines.append({"t": round(w["t"] + est, 2), "text": txt[cut + 1:]})
                continue
        lines.append({"t": round(w["t"], 2), "text": txt})
    for l in lines:
        l["text"] = to_display(l["text"])
    return lines


async def gen(scene, vkey, vname):
    out = ROOT / "assets" / "narration" / vkey / f"scene{scene['scene']}.mp3"
    words = []
    cm = edge_tts.Communicate(to_tts(scene["text"]), vname, rate=RATE)  # 7.x 預設 SentenceBoundary
    with open(out, "wb") as f:
        async for chunk in cm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"].endswith("Boundary"):
                words.append({"t": chunk["offset"] / 1e7, "w": chunk["text"],
                              "d": chunk.get("duration", 4e7) / 1e7})
    dur = probe_dur(out)
    print(f"  scene{scene['scene']} {vkey}: {dur:.1f}s, {len(words)} words")
    return {"dur": round(dur, 2), "lines": words_to_lines(words, scene["text"])}


async def gen_retry(sc, vkey, vname, tries=4):
    for i in range(tries):
        try:
            return await gen(sc, vkey, vname)
        except Exception as e:
            print(f"  scene{sc['scene']} {vkey} retry {i+1}: {str(e)[:60]}")
            await asyncio.sleep(15 * (i + 1))
    raise RuntimeError(f"scene{sc['scene']} {vkey} failed after {tries} tries")


async def main():
    import sys
    only = {int(a) for a in sys.argv[1:]} if len(sys.argv) > 1 else None
    script = json.loads((ROOT / "narration" / "script.json").read_text())
    out = ROOT / "assets" / "narration" / "cues.json"
    cues = json.loads(out.read_text()) if out.exists() else {}
    for sc in script:
        if only and sc["scene"] not in only:
            continue
        entry = {"title": sc["title"], "text": sc["text"]}
        for vkey, vname in VOICES.items():
            entry[vkey] = await gen_retry(sc, vkey, vname)
        cues[str(sc["scene"])] = entry
        out.write_text(json.dumps(cues, ensure_ascii=False, indent=1))
    print("wrote", out)

asyncio.run(main())
