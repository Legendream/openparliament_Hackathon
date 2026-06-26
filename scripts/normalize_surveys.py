#!/usr/bin/env python3
"""把歷次問卷 xlsx（每分頁一場）正規化成統一結構，並套用同義詞對照。

原則：raw data 只從 ~/Downloads 讀取，輸出只寫到本機 data/（已 gitignore）。
此 script 不含任何受訪者資料，可進版控。

可持續擴充：未來新增月份 = 在 xlsx 多一個分頁（或換新檔），重跑即可。
表頭以關鍵字比對，欄位順序/微調文字不影響。新出現、未對應的職業/管道值
會寫進 data/analysis/unmapped_values.csv 供人工補進 config/value_synonyms.csv。
"""
import csv
import os
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.expanduser("~/Downloads/歷次問卷＿去識別化後整合.xlsx")
OUT_DIR = os.path.join(ROOT, "data")
ANALYSIS_DIR = os.path.join(OUT_DIR, "analysis")
SYNONYMS = os.path.join(ROOT, "config", "value_synonyms.csv")
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# 標準欄位 -> 比對表頭的關鍵字（命中即對應）
FIELD_KEYWORDS = {
    "nps": ["願意向朋友推薦"],
    "is_first_time": ["第一次參加"],
    "occupation": ["職業背景"],
    "channel": ["哪個管道"],
    "join_reason": ["為什麼想參加"],
    "wish_topic": ["徵集各式", "好奇、想瞭解的主題", "好奇"],
    "impressed": ["印象最深刻", "印象深刻"],
    "timestamp": ["時間戳記"],
}
STD_FIELDS = ["event", "timestamp", "nps", "is_first_time",
              "occupation", "channel", "join_reason", "wish_topic", "impressed"]
CANON_FIELDS = ["occupation", "channel", "is_first_time"]


def load_synonyms():
    """回傳 {(field, raw): canonical}。"""
    m = {}
    if os.path.exists(SYNONYMS):
        with open(SYNONYMS, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                m[(r["field"], r["raw"].strip())] = r["canonical"].strip()
    return m


def match_field(header):
    h = (header or "").strip()
    if not h:
        return None
    for field, kws in FIELD_KEYWORDS.items():
        for kw in kws:
            if kw in h:
                return field
    return None


def clean(v):
    return "" if v is None else str(v).strip().replace("\n", " ")


def main():
    syn = load_synonyms()
    wb = openpyxl.load_workbook(SRC, data_only=True)
    all_rows, events, unmapped = [], [], set()

    for ws in wb.worksheets:
        rows = [r for r in ws.iter_rows(values_only=True)
                if any(c is not None and str(c).strip() for c in r)]
        if not rows:
            continue
        header = rows[0]
        col_map = {}
        for i, h in enumerate(header):
            fld = match_field(h)
            if fld and fld not in col_map.values():
                col_map[i] = fld
        extra_headers = [clean(h) for i, h in enumerate(header)
                         if i not in col_map and clean(h)]

        nps_scores = []
        for r in rows[1:]:
            rec = {f: "" for f in STD_FIELDS}
            rec["event"] = ws.title
            for i, val in enumerate(r):
                fld = col_map.get(i)
                if fld:
                    rec[fld] = clean(val)
            # 套用同義詞對照（保留原值，新增 *_canon）
            for fld in CANON_FIELDS:
                raw = rec[fld]
                if raw:
                    if (fld, raw) in syn:
                        rec[fld + "_canon"] = syn[(fld, raw)]
                    else:
                        rec[fld + "_canon"] = raw   # 沒對應先沿用原值
                        unmapped.add((fld, raw))
                else:
                    rec[fld + "_canon"] = ""
            try:
                s = float(rec["nps"])
                if 0 <= s <= 10:
                    nps_scores.append(s)
            except (ValueError, TypeError):
                pass
            all_rows.append(rec)

        n = len(nps_scores)
        if n:
            prom = sum(1 for s in nps_scores if s >= 9)
            det = sum(1 for s in nps_scores if s <= 6)
            nps_val = round((prom - det) / n * 100, 1)
        else:
            nps_val = ""
        events.append({"event": ws.title, "n_responses": len(rows) - 1,
                       "n_nps": n, "nps": nps_val,
                       "topic_questions": " | ".join(extra_headers)})

    out_fields = STD_FIELDS + [f + "_canon" for f in CANON_FIELDS]
    with open(os.path.join(OUT_DIR, "responses_normalized.csv"), "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()
        w.writerows(all_rows)

    with open(os.path.join(OUT_DIR, "events.csv"), "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["event", "n_responses", "n_nps", "nps", "topic_questions"])
        w.writeheader()
        w.writerows(events)

    with open(os.path.join(ANALYSIS_DIR, "unmapped_values.csv"), "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["field", "raw_value"])
        for fld, raw in sorted(unmapped):
            w.writerow([fld, raw])

    print(f"場次數: {len(events)}  逐筆回覆數: {len(all_rows)}")
    print(f"未對應值（需補 config/value_synonyms.csv）: {len(unmapped)} 個")
    print(f"輸出: data/responses_normalized.csv, data/events.csv, data/analysis/unmapped_values.csv")


if __name__ == "__main__":
    main()
