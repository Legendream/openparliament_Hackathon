#!/usr/bin/env bash
# 國會松問卷分析 pipeline。新月份資料進來後，重跑這支即可更新所有分析。
# 用法：bash scripts/run_pipeline.sh
set -e
cd "$(dirname "$0")/.."
echo "[1/2] 正規化 raw 問卷 ..."
python3 scripts/normalize_surveys.py
echo "[2/4] 產出分析 ..."
python3 scripts/build_analysis.py
echo "[3/4] 產出網站資料 JSON/JS ..."
python3 scripts/build_site_data.py
echo "[4/4] 打包自包含 index.html ..."
python3 scripts/build_index.py
echo "完成。分析在 data/（不上傳）；網站 index.html 可直接開啟。"
