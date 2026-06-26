#!/usr/bin/env python3
"""讀正規化資料 + config，產出分析結果到 data/analysis/。

輸出（皆為聚合統計，不含個人可回推資料）：
  nps_by_event.csv          每場 NPS 與推薦/中立/貶損人數
  composition_occupation.csv 職業組成（canonical）
  composition_channel.csv    管道組成（canonical）
  composition_first_time.csv 新舊參與者
  wish_topics_tagged.csv     每筆許願 + 主題標籤（多標）
  wish_demand_vs_held.csv    ★功能②決策表：主題需求強度 × 是否已辦
  summary.json               首頁用的彙總數字
"""
import csv
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
ANALYSIS = os.path.join(DATA, "analysis")
CONFIG = os.path.join(ROOT, "config")
os.makedirs(ANALYSIS, exist_ok=True)

NOISE = ("無", "沒有", "暫無", "暫時沒有", "沒特定", "沒有特定", "目前暫無",
         "see you", "謝謝", "n/a", "na", "-")


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(name, fieldnames, rows):
    with open(os.path.join(ANALYSIS, name), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def is_noise(text):
    t = text.strip().lower()
    return (len(t) <= 3) or any(t == n or t.startswith(n) for n in NOISE)


def nps_value(scores):
    n = len(scores)
    if not n:
        return None, 0, 0, 0
    prom = sum(1 for s in scores if s >= 9)
    pas = sum(1 for s in scores if 7 <= s <= 8)
    det = sum(1 for s in scores if s <= 6)
    return round((prom - det) / n * 100, 1), prom, pas, det


def main():
    rows = read_csv(os.path.join(DATA, "responses_normalized.csv"))
    taxonomy = read_csv(os.path.join(CONFIG, "wish_taxonomy.csv"))
    themes = read_csv(os.path.join(CONFIG, "event_themes.csv"))
    # 人工校訂分類（優先採用）：{原文: "分類;分類" 或 "(排除)"}
    labels_path = os.path.join(CONFIG, "wish_labels.csv")
    wish_labels = {}
    if os.path.exists(labels_path):
        for r in read_csv(labels_path):
            wish_labels[r["wish"].strip()] = r["categories"].strip()

    # 排序 event（依 config 順序）
    order = {t["event"]: i for i, t in enumerate(themes)}

    # ---- NPS by event + 整體 ----
    by_event = defaultdict(list)
    all_scores = []
    for r in rows:
        try:
            s = float(r["nps"])
        except (ValueError, TypeError):
            continue
        if 0 <= s <= 10:
            by_event[r["event"]].append(s)
            all_scores.append(s)
    nps_rows = []
    theme_map = {t["event"]: t["theme_label"] for t in themes}
    for ev in sorted(by_event, key=lambda e: order.get(e, 999)):
        v, p, pa, d = nps_value(by_event[ev])
        nps_rows.append({"event": ev, "theme": theme_map.get(ev, ""),
                         "n": len(by_event[ev]), "nps": v,
                         "promoters": p, "passives": pa, "detractors": d})
    write_csv("nps_by_event.csv",
              ["event", "theme", "n", "nps", "promoters", "passives", "detractors"], nps_rows)
    overall_nps, op, opa, od = nps_value(all_scores)

    # ---- 組成 ----
    def composition(field):
        c = Counter(r[field] for r in rows if r[field].strip())
        total = sum(c.values())
        return [{"value": k, "count": v, "pct": round(v / total * 100, 1)}
                for k, v in c.most_common()], total

    occ, occ_total = composition("occupation_canon")
    chan, chan_total = composition("channel_canon")
    ft, ft_total = composition("is_first_time_canon")
    write_csv("composition_occupation.csv", ["value", "count", "pct"], occ)
    write_csv("composition_channel.csv", ["value", "count", "pct"], chan)
    write_csv("composition_first_time.csv", ["value", "count", "pct"], ft)

    # ---- 許願主題標籤（多標；維度化） ----
    cat2dim = {t["category"]: t.get("dimension", "其他") for t in taxonomy}
    tax = [(t["category"], [k.strip() for k in t["keywords"].split("|") if k.strip()])
           for t in taxonomy]
    tagged = []
    cat_count = Counter()
    n_curated = n_auto = 0
    for r in rows:
        w = r["wish_topic"].strip()
        if not w:
            continue
        if w in wish_labels:                       # 人工校訂優先
            lab = wish_labels[w]
            if lab == "(排除)":
                continue
            cats = [c.strip() for c in lab.split(";") if c.strip()]
            source = "curated"
            n_curated += 1
        else:                                       # 新資料：關鍵字自動標
            if is_noise(w):
                continue
            cats = [cat for cat, kws in tax if any(kw.lower() in w.lower() for kw in kws)]
            if not cats:
                cats = ["未分類"]
            source = "auto"
            n_auto += 1
        for c in cats:
            cat_count[c] += 1
        tagged.append({"event": r["event"], "wish": w,
                       "categories": ";".join(cats), "source": source})
    write_csv("wish_topics_tagged.csv", ["event", "wish", "categories", "source"], tagged)

    # ---- 需求排行（依維度分組；已辦場次僅作參考，不做決策判定） ----
    held = Counter()
    for t in themes:
        for c in [x.strip() for x in t["covered_categories"].split(";") if x.strip()]:
            held[c] += 1
    DIM_ORDER = {"主題": 0, "活動形式": 1, "工具建議": 2, "其他": 3}
    demand_rows = [{"dimension": cat2dim.get(c, "其他"), "category": c,
                    "demand": cat_count[c], "held_ref": held.get(c, 0)}
                   for c in cat_count]
    demand_rows.sort(key=lambda r: (DIM_ORDER.get(r["dimension"], 9),
                                    -r["demand"], r["category"]))
    write_csv("wish_demand.csv",
              ["dimension", "category", "demand", "held_ref"], demand_rows)

    # ---- summary.json ----
    summary = {
        "events": len(themes),
        "total_responses": len(rows),
        "overall_nps": overall_nps,
        "promoters": op, "passives": opa, "detractors": od,
        "nps_sample": len(all_scores),
        "first_time_pct": next((x["pct"] for x in ft if x["value"] == "首次參加"), None),
        "returning_pct": next((x["pct"] for x in ft if x["value"] == "回流參加"), None),
        "wish_responses": len(tagged),
        "top_topics": [d["category"] for d in demand_rows if d["dimension"] == "主題"][:5],
    }
    with open(os.path.join(ANALYSIS, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"整體 NPS={overall_nps} (n={len(all_scores)}) | 許願有效={len(tagged)}"
          f"（人工校訂 {n_curated} / 自動 {n_auto}）")
    print(f"主題需求 Top: {summary['top_topics']}")
    print(f"輸出於 data/analysis/")


if __name__ == "__main__":
    main()
