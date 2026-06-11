#!/usr/bin/env python3
"""CC0 配樂/音效海選:Freesound 搜尋 → 下載 preview → Gemini 2.5-flash 代聽 → 報告。

用法:
  python3 hunt.py            # 跑全部(music scene1-9 + sfx)
  python3 hunt.py scene5     # 只跑某幕
  python3 hunt.py sfx        # 只跑音效
已代聽過的候選(reports 內有同 id)會跳過,可疊代加 query 重跑。
"""
import base64, json, pathlib, subprocess, sys, time, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CAND = HERE / "candidates"
REPORTS = HERE / "reports"


def load_env(path):
    env = {}
    for line in pathlib.Path(path).read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"')
    return env

FS_KEY = load_env(pathlib.Path.home() / ".config/freesound.env")["FREESOUND_API_KEY"]
GM_KEY = load_env("/home/ct/gemini/.env")["NANOBANANA_GEMINI_API_KEY"]

# ── 每幕搜尋設定 ──────────────────────────────────────────
MUSIC = {
 1: {"mood": "heavy war drums march, ominous, an overwhelming army advancing south",
     "q": ["war drums", "battle drums", "taiko", "tribal drums dark", "percussion ominous"]},
 2: {"mood": "Chinese traditional strings (guzheng/zither), diplomatic, stately, calm resolve",
     "q": ["guzheng", "chinese zither", "chinese traditional music", "koto melody", "erhu"]},
 3: {"mood": "tense standoff, strings ostinato with percussion, first clash of two armies",
     "q": ["tension music", "suspense strings", "battle tension", "cinematic tension percussion"]},
 4: {"mood": "dark brooding drone with metallic accents, ships chained together, uneasy calm",
     "q": ["dark drone", "ominous drone", "dark ambient loop", "drone metallic"]},
 5: {"mood": "melancholy solo Chinese flute (dizi/xiao) at dusk, sacrifice and hidden schemes",
     "q": ["chinese flute", "dizi", "bamboo flute sad", "xiao flute", "flute melancholy solo"]},
 6: {"mood": "rising anticipation, wind swelling, strings climbing, the night before the storm",
     "q": ["crescendo build", "rising tension", "suspense build", "cinematic riser long"]},
 7: {"mood": "full-on epic battle climax: furious drums, cymbals, racing strings, fire attack",
     "q": ["epic battle music", "epic drums", "battle music intense", "epic percussion orchestral"]},
 8: {"mood": "broken slow lament, mournful solo flute or erhu, defeated army retreating at dawn",
     "q": ["mournful flute", "sad flute slow", "lament", "sad ambient slow", "erhu sad"]},
 9: {"mood": "majestic open resolution, theme restated, history settling into three kingdoms",
     "q": ["epic orchestral", "majestic theme", "cinematic finale", "triumphant orchestral"]},
}
SFX = {
 "battlecry": {"mood": "large ancient army battle cries / crowd war shouts, no modern words, no guns",
               "q": ["battle cry crowd", "army shouting battle", "medieval battle crowd roar"],
               "dur": "[3 TO 60]"},
 "chains":    {"mood": "heavy iron chain clanks, shipboard, no modern machinery",
               "q": ["heavy chain clank metal", "iron chains rattle"],
               "dur": "[1 TO 30]"},
 "swords":    {"mood": "real metal sword clash / blade impact for an ancient battle, single hits or short flurry, no modern foley branding, no gunfire",
               "q": ["sword clash", "sword fight metal clang", "blade clash battle", "metal sword hit"],
               "dur": "[1 TO 30]"},
}
MUSIC_DUR = "[20 TO 300]"


def http_json(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "red-cliffs-audio/0.1"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def fs_search(query, dur_filter, sort, n=8):
    params = urllib.parse.urlencode({
        "query": query,
        "filter": f'license:"Creative Commons 0" duration:{dur_filter}',
        "fields": "id,name,duration,license,previews,username,url",
        "sort": sort, "page_size": n, "token": FS_KEY})
    return http_json("https://freesound.org/apiv2/search/text/?" + params).get("results", [])


def download(url, dest, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "red-cliffs-audio/0.1"})
            dest.write_bytes(urllib.request.urlopen(req, timeout=120).read())
            return True
        except Exception:
            time.sleep(3 * (i + 1))
    return False


def audition_clip(path):
    """前 90 秒轉 64k mono 給 Gemini 聽(省 token、夠判斷)。"""
    tmp = path.with_suffix(".audition.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path),
                    "-t", "90", "-ac", "1", "-ar", "22050", "-b:a", "64k", str(tmp)],
                   check=True)
    return tmp


def gemini_audition(path, mood):
    prompt = f"""You are auditioning audio for a historical documentary about the Battle of Red Cliffs (ancient China, 208 AD).
Target mood for this slot: {mood}
Listen to the clip (first 90s only) and answer in STRICT JSON, no markdown fence.
All string values MUST be written in Traditional Chinese (zh-TW):
{{"instruments": "...", "energy": "...", "vocals": true/false, "vocal_detail": "...",
 "anachronistic": true/false, "anachronistic_detail": "...",
 "loopable_guess": "...", "fit": 0-10, "reason": "one line"}}
Vocals = any human voice incl. choir/shouts. Anachronistic = guns, synths, electric instruments, modern genre feel."""
    b64 = base64.b64encode(path.read_bytes()).decode()
    body = json.dumps({"contents": [{"parts": [
        {"text": prompt}, {"inline_data": {"mime_type": "audio/mp3", "data": b64}}]}]}).encode()
    for model in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash",
                  "gemini-2.5-flash", "gemini-flash-latest"]:
        try:
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GM_KEY}",
                data=body, headers={"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=180))
            txt = r["candidates"][0]["content"]["parts"][0]["text"].strip()
            if txt.startswith("```"):
                txt = txt.strip("`").lstrip("json").strip()
            return json.loads(txt)
        except Exception as e:
            print(f"    audition retry ({model}): {str(e)[:80]}")
            time.sleep(8)
    return None


def hunt_slot(slot, cfg, dur_filter):
    rpt_path = REPORTS / f"{slot}.json"
    report = json.loads(rpt_path.read_text()) if rpt_path.exists() else []
    seen = {c["id"] for c in report}
    cands = []
    for q in cfg["q"]:
        for sort in ["rating_desc", "downloads_desc"]:
            for s in fs_search(q, dur_filter, sort):
                if s["id"] not in seen and s["id"] not in {c["id"] for c in cands}:
                    cands.append(s)
    cands = cands[:8]  # 每輪最多代聽 8 個新候選
    print(f"[{slot}] {len(cands)} new candidates")
    for s in cands:
        dest = CAND / f"{slot}-{s['id']}.mp3"
        if not dest.exists():
            if not download(s["previews"]["preview-hq-mp3"], dest):
                print(f"    {s['id']} download FAIL"); continue
        aud = gemini_audition(audition_clip(dest), cfg["mood"])
        if aud is None:
            print(f"    {s['id']} audition FAIL"); continue
        verdict = "shortlist" if (aud["fit"] >= 7 and not aud["vocals"] and not aud["anachronistic"]) else \
                  ("maybe" if aud["fit"] >= 6 else "reject")
        # battlecry 例外:人聲就是重點
        if slot == "battlecry":
            verdict = "shortlist" if (aud["fit"] >= 7 and not aud["anachronistic"]) else verdict
        report.append({"id": s["id"], "name": s["name"], "dur": s["duration"],
                       "src": s["url"], "by": s["username"], "license": "CC0",
                       "file": dest.name, "preview": s["previews"]["preview-hq-mp3"],
                       "audition": aud, "verdict": verdict})
        print(f"    [{s['id']}] fit={aud['fit']} vocals={aud['vocals']} -> {verdict} | {s['name'][:40]}")
        rpt_path.write_text(json.dumps(report, ensure_ascii=False, indent=1))
    ok = [c for c in report if c["verdict"] == "shortlist"]
    print(f"[{slot}] shortlist now: {len(ok)}")


targets = sys.argv[1:] or [f"scene{i}" for i in MUSIC] + list(SFX)
for t in targets:
    if t.startswith("scene"):
        n = int(t[5:])
        hunt_slot(t, MUSIC[n], MUSIC_DUR)
    elif t in SFX:
        hunt_slot(t, SFX[t], SFX[t]["dur"])
print("done")
