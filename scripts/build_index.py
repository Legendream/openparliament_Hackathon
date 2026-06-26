#!/usr/bin/env python3
"""把 src/index.src.html 的外部 <script src> 內嵌，產出自包含的 index.html。

目的：使用者用任何方式開檔（雙擊 file://、預覽面板、離線）都能完整呈現，
不依賴相對路徑或網路。Chart.js、資料、main.js 全部內嵌成單一檔案。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "index.src.html")
OUT = os.path.join(ROOT, "index.html")

# 內嵌對應：src 屬性 -> 實際檔案
INLINE = {
    "assets/js/chart.umd.min.js": os.path.join(ROOT, "assets", "js", "chart.umd.min.js"),
    "assets/data/site_data.js": os.path.join(ROOT, "assets", "data", "site_data.js"),
    "assets/js/main.js": os.path.join(ROOT, "assets", "js", "main.js"),
    "assets/js/vote.js": os.path.join(ROOT, "assets", "js", "vote.js"),
}


def main():
    with open(SRC, encoding="utf-8") as f:
        html = f.read()

    for src_attr, path in INLINE.items():
        with open(path, encoding="utf-8") as f:
            code = f.read()
        # 避免內容中的 </script> 提前關閉標籤
        code = code.replace("</script>", "<\\/script>")
        tag = '<script src="' + re.escape(src_attr) + '"></script>'
        replacement = "<script>\n" + code + "\n</script>"
        html, n = re.subn(tag, lambda _m: replacement, html, count=1)
        if n == 0:
            raise SystemExit("找不到要內嵌的標籤: " + src_attr)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size_kb = round(os.path.getsize(OUT) / 1024)
    print(f"產出自包含 index.html（{size_kb} KB，所有資源已內嵌）")


if __name__ == "__main__":
    main()
