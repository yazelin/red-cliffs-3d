#!/usr/bin/env python3
"""補丁既有 reports:1) 補 Freesound preview URL 2) 英文代聽筆記批次翻繁中。可重跑(冪等)。"""
import json, pathlib, time, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent

def load_env(path):
    env = {}
    for line in pathlib.Path(path).read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"')
    return env

FS_KEY = load_env(pathlib.Path.home() / ".config/freesound.env")["FREESOUND_API_KEY"]
GM_KEY = load_env("/home/ct/gemini/.env")["NANOBANANA_GEMINI_API_KEY"]

def has_cjk(s):
    return any('一' <= ch <= '鿿' for ch in str(s))

TEXT_FIELDS = ["instruments", "energy", "vocal_detail", "anachronistic_detail", "loopable_guess", "reason"]

for rp in sorted(HERE.glob("reports/*.json")):
    report = json.loads(rp.read_text())
    changed = False
    # 1) preview URL
    for c in report:
        if "preview" not in c:
            url = f"https://freesound.org/apiv2/sounds/{c['id']}/?fields=previews&token={FS_KEY}"
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "red-cliffs-audio/0.1"}), timeout=30))
                c["preview"] = d["previews"]["preview-hq-mp3"]
                changed = True
            except Exception as e:
                print(f"{rp.stem} #{c['id']} preview fail: {str(e)[:60]}")
            time.sleep(.3)
    # 2) 翻譯(整檔一次丟,省呼叫)
    todo = [c for c in report if not all(has_cjk(c["audition"].get(f, "無")) or not c["audition"].get(f)
                                          for f in TEXT_FIELDS)]
    if todo:
        payload = [{"id": c["id"], **{f: c["audition"].get(f, "") for f in TEXT_FIELDS}} for c in todo]
        prompt = ("把下列 JSON 陣列中每個物件的英文欄位值翻成繁體中文(zh-TW),樂器名/音樂術語用台灣慣用譯名,"
                  "id 保持不變,只回傳 STRICT JSON 陣列,無 markdown 圍欄:\n" + json.dumps(payload, ensure_ascii=False))
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        for model in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash"]:
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GM_KEY}",
                    data=body, headers={"Content-Type": "application/json"})
                r = json.load(urllib.request.urlopen(req, timeout=180))
                txt = r["candidates"][0]["content"]["parts"][0]["text"].strip()
                if txt.startswith("```"):
                    txt = txt.strip("`").lstrip("json").strip()
                trans = {t["id"]: t for t in json.loads(txt)}
                for c in todo:
                    if c["id"] in trans:
                        for f in TEXT_FIELDS:
                            if trans[c["id"]].get(f):
                                c["audition"][f] = trans[c["id"]][f]
                        changed = True
                break
            except Exception as e:
                print(f"{rp.stem} translate retry ({model}): {str(e)[:60]}")
                time.sleep(8)
    if changed:
        rp.write_text(json.dumps(report, ensure_ascii=False, indent=1))
        print(f"{rp.stem}: patched ({len(report)} entries)")
    else:
        print(f"{rp.stem}: already ok")
print("done")
