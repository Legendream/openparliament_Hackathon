# g0v 國會松展示網站

展示 g0v 國會松的活動資訊、會後問卷，以及大家想聽的主題。

## 目標功能

- 歷次活動滿意度問卷分析（NPS、參與者組成）
- 大家許願想聽的主題 × 歷次國會松主題對照分析
- 歷次國會松活動資訊（共筆、回放影片）
- 下一期活動預告與報名入口
- 國會松電子報訂閱入口

## 參考資料

- 歷次活動：https://g0vcongressthon.oen.tw/
- 歷次共筆：https://g0v.hackmd.io/@SA7CD7VRSp6Fcqw9CaElcQ/SJ93ZW5XR/

## 資料隱私原則

- 問卷 **raw data 不進此資料夾、不上傳 GitHub**（放 `~/Downloads`）。
- 所有整理／分析輸出只留本機 `data/`（已被 `.gitignore` 排除）。
- `config/value_synonyms.csv` 含受訪者逐字答案，亦僅留本機；其餘 config 為純方法論可公開。

## 分析 pipeline（可持續擴充）

程式碼固定，人工判斷都在 `config/`，新月份資料進來重跑即可：

```
scripts/
  normalize_surveys.py  # raw xlsx（每分頁一場）→ data/responses_normalized.csv + events.csv
  build_analysis.py     # 正規化資料 + config → data/analysis/*
  run_pipeline.sh       # 一鍵重跑全流程
config/
  value_synonyms.csv        # 職業/管道同義詞歸一（本機）
  occupation_crosswalk.csv  # 職業兩題（組織×工作內容）→ 舊分類對照
  wish_taxonomy.csv         # 許願主題分類關鍵字
  event_themes.csv          # 每場主題與已涵蓋分類
```

**職業題有新舊兩種格式，pipeline 都吃得下**

| 期間 | 問法 | 對應欄位 | 走哪張表 |
|---|---|---|---|
| ～2026.7 | 單題「請問你的職業背景是？」 | `occupation` | `value_synonyms.csv` |
| 2026.8～ | 兩題「你在哪一類組織工作或就學？」＋「你的工作內容最接近哪一類？」 | `occupation_org`、`occupation_role` | `occupation_crosswalk.csv` |

兩種格式最後都收斂成同一組 `occupation_canon`（13 類），網站的職業圖不必改。
自由填答（兩題的「其他」）補在本機的 `value_synonyms.csv`，`field` 用
`occupation_org` / `occupation_role`；`occupation_crosswalk.csv` 只放表單既有選項的
分類規則，因此可進版控。對不到的值一律寫進 `unmapped_values.csv`，不會靜默吞掉。

> ⚠ **跨期比較請留意口徑變動。** 新格式以「組織別」為主軸，舊格式是受訪者自述
> （選項本身混了組織與職業）。例如在 NGO 寫程式的人，舊格式可能自選「資訊科技公司」，
> 新格式則會落在「公民團體/倡議」。13 類都還在、圖表照舊，但 2026.8 前後的組成
> 變化有一部分來自定義改變，不能全部解讀成參與者輪廓真的變了。

**更新流程（每月新增一場後）**

1. 把該月回覆，在 `~/Downloads/歷次問卷＿去識別化後整合.xlsx` 新增一個分頁（沿用既有題目最省事）。
2. 在 `config/event_themes.csv` 補一列該場主題。
3. 執行 `bash scripts/run_pipeline.sh`。
4. 若 `data/analysis/unmapped_values.csv` 出現新的職業/管道寫法，補進 `config/value_synonyms.csv` 再跑一次。
   （新格式職業兩題的自由填答同樣補在這裡，`field` 用 `occupation_org` / `occupation_role`。）

表頭以關鍵字比對，欄位順序不影響整併。題目文字可以小幅調整，但**不要動到關鍵字本身**
（如職業兩題的「哪一類組織」「工作內容」）；若只辨識到兩題中的一題，normalize 會在
該分頁印出警告。

### 主要分析產出（`data/analysis/`）

- `nps_by_event.csv`／整體 NPS、推薦/中立/貶損
- `composition_occupation.csv`、`composition_channel.csv`、`composition_first_time.csv`
- `wish_topics_tagged.csv`、`wish_demand_vs_held.csv`（功能②：主題需求強度 × 是否已辦）
- `summary.json`（首頁彙總數字）

## 授權

- 程式碼：[MIT](LICENSE)
- 網站內容（文字、聚合統計圖表）：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.zh-hant)
- 問卷 raw data 不在此 repo、不適用上述授權（見資料隱私原則）

## 狀態

籌備中（g0v 國會松籌備工作小組）
