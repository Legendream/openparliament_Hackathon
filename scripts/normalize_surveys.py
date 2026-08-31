#!/usr/bin/env python3
"""把歷次問卷 xlsx（每分頁一場）正規化成統一結構，並套用同義詞對照。

原則：raw data 只從 ~/Downloads 讀取，輸出只寫到本機 data/（已 gitignore）。
此 script 不含任何受訪者資料，可進版控。

可持續擴充：未來新增月份 = 在 xlsx 多一個分頁（或換新檔），重跑即可。
表頭以關鍵字比對，欄位順序/微調文字不影響。新出現、未對應的職業/管道值
會寫進 data/analysis/unmapped_values.csv 供人工補進 config/value_synonyms.csv
（含新格式職業兩題的 occupation_org / occupation_role 自由填答；
 表單既有選項的分類規則則放可進版控的 config/occupation_crosswalk.csv）。
"""
import csv
import os
import unicodedata

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.expanduser("~/Downloads/歷次問卷＿去識別化後整合.xlsx")
OUT_DIR = os.path.join(ROOT, "data")
ANALYSIS_DIR = os.path.join(OUT_DIR, "analysis")
SYNONYMS = os.path.join(ROOT, "config", "value_synonyms.csv")
CROSSWALK = os.path.join(ROOT, "config", "occupation_crosswalk.csv")
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# 標準欄位 -> 比對表頭的關鍵字（命中即對應）
# 職業有新舊兩種問法：
#   舊（～2026.7）：單題「請問你的職業背景是？」   -> occupation
#   新（2026.8～）：兩題「你在哪一類組織工作或就學？」-> occupation_org
#                        「你的工作內容最接近哪一類？」-> occupation_role
# 三個關鍵字彼此互斥，同一份表頭不會互相搶欄位。
FIELD_KEYWORDS = {
    "nps": ["願意向朋友推薦"],
    "is_first_time": ["第一次參加"],
    "occupation": ["職業背景"],
    # 多給幾個同義關鍵字，題目文字微調時比較不會整欄漏抓
    "occupation_org": ["哪一類組織", "組織工作或就學", "類組織"],
    "occupation_role": ["工作內容"],
    "channel": ["哪個管道"],
    "join_reason": ["為什麼想參加"],
    "wish_topic": ["徵集各式", "好奇、想瞭解的主題", "好奇"],
    "impressed": ["印象最深刻", "印象深刻"],
    "timestamp": ["時間戳記"],
}
STD_FIELDS = ["event", "timestamp", "nps", "is_first_time",
              "occupation", "occupation_org", "occupation_role",
              "channel", "join_reason", "wish_topic", "impressed"]
CANON_FIELDS = ["occupation", "channel", "is_first_time"]


def load_synonyms():
    """回傳 {(field, raw): canonical}。"""
    m = {}
    if os.path.exists(SYNONYMS):
        with open(SYNONYMS, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                m[(r["field"], r["raw"].strip())] = r["canonical"].strip()
    return m


def squash(s):
    """比對用：全半形正規化後去掉所有空白。

    表單選項的標點可能是全形（「政府機關／公營事業」），而對照表寫成半形
    （「政府機關 / 公營事業」），兩者看起來一樣但碼位不同，會整批對不到。
    NFKC 會把全形斜線、括號等收斂成半形，兩側都套用即可互相對上；
    中文標點（、。）不受影響。
    """
    return "".join(unicodedata.normalize("NFKC", s or "").split())


def load_crosswalk():
    """回傳 (rules, known_roles)。

    rules       {(squash(org) or '*', squash(role) or '*'): canonical}
    known_roles 表單既有的工作內容選項（squash 過），用來分辨自由填答。
    """
    rules, known_roles = {}, set()
    if not os.path.exists(CROSSWALK):
        return rules, known_roles
    with open(CROSSWALK, encoding="utf-8-sig") as f:
        lines = [ln for ln in f if not ln.lstrip().startswith("#")]
    for r in csv.DictReader(lines):
        org = r["org"].strip()
        role = r["role"].strip()
        okey = "*" if org == "*" else squash(org)
        rkey = "*" if role == "*" else squash(role)
        if (okey, rkey) in rules:
            # NFKC 之後全形／半形寫法會收斂成同一個鍵，兩列看起來不同卻會互相
            # 覆蓋。這種覆蓋一定要吵出來，否則分類結果會取決於檔案的列順序。
            print(f"  ⚠ occupation_crosswalk.csv 重複規則："
                  f"「{org} × {role}」正規化後與前面某列相同，後者覆蓋前者")
        rules[(okey, rkey)] = r["canonical"].strip()
        if rkey != "*":
            known_roles.add(rkey)
    return rules, known_roles


def syn_lookup(syn, field, value):
    """查同義詞表：先精確比對，再用 squash 後的寬鬆比對。

    寬鬆比對是為了跟 crosswalk 用同一把尺——否則自由填答補了半形寫法、
    受訪者填的是全形，這裡查不到，該筆就會莫名其妙落回「其他/未提供」。
    只用在新格式的職業兩題，不影響舊格式既有的精確比對行為。
    """
    v = value.strip()
    if (field, v) in syn:
        return syn[(field, v)]
    key = squash(v)
    if key:
        for (f, raw), canon in syn.items():
            if f == field and squash(raw) == key:
                return canon
    return value


def resolve_occupation(org, role, rules, known_roles, syn):
    """新格式（兩題）-> canonical。回傳 (canonical, [unmapped_notes])。

    自由填答先查本機同義詞表歸一，再依
    (組織, 工作內容) → (*, 工作內容) → (組織, *) 的順序查交叉表。
    canonical 為 "-" 代表「已知選項但不覆寫」，continue 往下一個規則找。
    對不到的值一律回報，不靜默吞掉。
    """
    notes = []
    if not org.strip() and not role.strip():
        return "", notes          # 兩題皆空＝舊格式或未填，不是未對應
    org = syn_lookup(syn, "occupation_org", org)
    role = syn_lookup(syn, "occupation_role", role)
    o, r = squash(org), squash(role)

    if r and r not in known_roles:
        notes.append(("occupation_role", role))
    if not o:
        # 只答了工作內容、或表頭沒抓到組織別欄位——無法分類，但要留下痕跡
        notes.append(("occupation_org", "(缺組織別)"))
        return "", notes

    for key in ((o, r), ("*", r), (o, "*")):
        val = rules.get(key)
        if val and val != "-":
            return val, notes
    notes.append(("occupation_org", org))
    return "其他/未提供", notes


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
    cross, known_roles = load_crosswalk()
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
        # 職業兩題是一組的，只抓到一題通常代表題目文字被改過（否則會整欄靜默漏掉）
        found = set(col_map.values())
        if ("occupation_org" in found) != ("occupation_role" in found):
            print(f"  ⚠ 分頁「{ws.title}」只辨識到職業兩題中的一題，請檢查題目文字")

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
                # 新格式的職業改走兩題交叉對照
                if fld == "occupation" and (rec["occupation_org"] or rec["occupation_role"]):
                    canon, notes = resolve_occupation(
                        rec["occupation_org"], rec["occupation_role"],
                        cross, known_roles, syn)
                    rec["occupation_canon"] = canon
                    unmapped.update(notes)
                    continue
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
    # 「缺組織別」是結構問題（沒有值可以對照），跟一般的未對應值分開報
    n_missing = sum(1 for _, v in unmapped if v == "(缺組織別)")
    print(f"未對應值（需補 config/value_synonyms.csv）: {len(unmapped) - n_missing} 個")
    if n_missing:
        print("  ⚠ 有回覆缺組織別（只答了工作內容，或表頭沒抓到該欄），這些筆職業無法分類")
    print(f"輸出: data/responses_normalized.csv, data/events.csv, data/analysis/unmapped_values.csv")


if __name__ == "__main__":
    main()
