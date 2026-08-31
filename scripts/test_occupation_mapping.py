#!/usr/bin/env python3
"""職業兩題（組織別 × 工作內容）對照邏輯的情境測試。

跑法：python3 scripts/test_occupation_mapping.py
不讀任何 raw data，所以可進版控、可隨時重跑。會讀本機的 value_synonyms.csv
（若存在），但所有測試案例都不依賴它，缺檔時同樣全數通過。

重點在於「表單選項的標點寫法不該影響分類」——2026.8 的實際資料用全形「／」，
對照表一度寫成半形「 / 」，碼位不同導致 10 筆有 7 筆分類錯誤。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize_surveys import load_crosswalk, load_synonyms, resolve_occupation  # noqa: E402

# (組織別, 工作內容, 預期分類, 這組在測什麼)
CASES = [
    ("政府機關／公營事業", "政治幕僚（立委、議員助理等）", "公務人員",
     "全形斜線（2026.8 實際資料的寫法）"),
    ("政府機關 / 公營事業", "政治幕僚（立委、議員助理等）", "公務人員",
     "半形斜線加空格"),
    ("政府機關/公營事業", "政治幕僚(立委、議員助理等)", "公務人員",
     "半形無空格＋半形括號"),
    ("企業", "軟體開發 / 資料工程", "資訊科技/開發",
     "工作內容寫成半形"),
    ("企業", "軟體開發／資料工程", "資訊科技/開發",
     "交叉規則命中：企業的工程師不算一般上班族"),
    ("學校／學術研究機構", "教學", "教育/教師",
     "交叉規則優先於組織別預設"),
    ("學校／學術研究機構", "議題研究", "學術研究",
     '(*,議題研究)="-" 時退回組織別預設'),
    ("企業", "教學", "一般民眾/上班族",
     '(*,教學)="-" 時退回組織別預設，不誤判成老師'),
    ("未就業（含退休、待業、家管）", "未就業", "其他/未提供",
     "未就業是表單既有選項，不該被當成自由填答"),
    ("", "軟體開發／資料工程", "",
     "只答工作內容→無法分類，但要留下痕跡"),
    ("", "", "",
     "兩題皆空＝舊格式或未填，不算未對應"),
]

# 只答工作內容時，必須留下「缺組織別」的痕跡，不能靜默吞掉
EXPECT_NOTE = {9: "occupation_org"}
# 表單既有選項不該被誤報成「其他」自由填答，否則會一直出現在待補清單上
EXPECT_NO_NOTE = {8: "occupation_role"}


def main():
    cross, roles = load_crosswalk()
    syn = load_synonyms()
    failed = 0
    for i, (org, role, expected, desc) in enumerate(CASES):
        got, notes = resolve_occupation(org, role, cross, roles, syn)
        ok = got == expected
        if i in EXPECT_NOTE:
            ok = ok and any(f == EXPECT_NOTE[i] for f, _ in notes)
        if i in EXPECT_NO_NOTE:
            ok = ok and not any(f == EXPECT_NO_NOTE[i] for f, _ in notes)
        if not ok:
            failed += 1
        print(f"{'✓' if ok else '✗'} {desc}")
        if not ok:
            print(f"    得到 {got!r}，預期 {expected!r}；notes={notes}")

    print(f"\n{len(CASES) - failed}/{len(CASES)} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
