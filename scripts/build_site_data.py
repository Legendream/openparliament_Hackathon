#!/usr/bin/env python3
"""把 data/analysis/ 的聚合結果 + config/event_themes.csv 轉成網站用 JSON。

隱私：只輸出聚合統計（人數、百分比、NPS、主題需求數），
不含任何逐筆資料、不含逐字許願文字。輸出檔可公開部署。
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(ROOT, "data", "analysis")
CONFIG = os.path.join(ROOT, "config")
OUT = os.path.join(ROOT, "assets", "data")
os.makedirs(OUT, exist_ok=True)


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return int(v)
    except (ValueError, TypeError):
        try:
            return float(v)
        except (ValueError, TypeError):
            return v


def main():
    with open(os.path.join(ANALYSIS, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)

    nps = [{"event": r["event"], "theme": r["theme"], "n": num(r["n"]),
            "nps": num(r["nps"]), "promoters": num(r["promoters"]),
            "passives": num(r["passives"]), "detractors": num(r["detractors"])}
           for r in read_csv(os.path.join(ANALYSIS, "nps_by_event.csv"))]

    def comp(name):
        return [{"value": r["value"], "count": num(r["count"]), "pct": num(r["pct"])}
                for r in read_csv(os.path.join(ANALYSIS, name))]

    wd = read_csv(os.path.join(ANALYSIS, "wish_demand.csv"))

    def wish_group(dim):
        return [{"category": r["category"], "demand": num(r["demand"]),
                 "held": num(r["held_ref"])} for r in wd if r["dimension"] == dim]

    wish = {"topics": wish_group("主題"), "formats": wish_group("活動形式"),
            "tools": wish_group("工具建議"), "valid_n": summary.get("wish_responses")}

    themes = read_csv(os.path.join(CONFIG, "event_themes.csv"))
    nps_map = {r["event"]: r["nps"] for r in nps}
    events = [{"event": t["event"], "date": t["date"], "term": t.get("term", ""),
               "theme": t["theme_label"], "hackmd": t.get("hackmd_url", ""),
               "video": t.get("video_url", ""), "event_url": t.get("event_url", ""),
               "nps": nps_map.get(t["event"], "")}
              for t in themes]

    site = {
        "summary": summary,
        "nps_by_event": nps,
        "occupation": comp("composition_occupation.csv"),
        "channel": comp("composition_channel.csv"),
        "first_time": comp("composition_first_time.csv"),
        "wish": wish,
        "events": events,
        "links": {
            "site": "https://g0vcongressthon.oen.tw/",
            "register": "https://g0vcongressthon.oen.tw/",
            "newsletter": "https://g0vcongressthon.oen.tw/",
        },
    }
    payload = json.dumps(site, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT, "site_data.json"), "w", encoding="utf-8") as f:
        f.write(payload)
    # JS 包裝版：用 <script> 直接載入，瀏覽器開檔即可（免 fetch / 免 server）
    with open(os.path.join(OUT, "site_data.js"), "w", encoding="utf-8") as f:
        f.write("window.SITE_DATA = " + payload + ";\n")
    print(f"輸出 assets/data/site_data.json + site_data.js（{len(events)} 場、僅聚合值）")


if __name__ == "__main__":
    main()
