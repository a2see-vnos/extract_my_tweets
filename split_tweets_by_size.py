#!/usr/bin/env python3
"""
split_tweets_by_size.py
────────────────────────────────────────────────────────────
gzip 圧縮された JSONL（created_at / full_text のみ）を読み込み、
  • 出力は “圧縮なし .jsonl”
  • 1 ファイル 5 MiB 未満
  • ファイル名に {最小年}-{最大年}_pXX サフィックス

例）
  output/split/self_tweets_2018-2019_p01.jsonl
  output/split/self_tweets_2020-2021_p01.jsonl
  output/split/self_tweets_2020-2021_p02.jsonl
"""

import gzip
import json
import os
import pathlib
from typing import TextIO

# ---------- 設定 ----------
INPUT_FILE = pathlib.Path("output/self_tweets.slim.jsonl.gz")
OUT_DIR    = pathlib.Path("output/split")
MAX_BYTES  = 5 * 1024 * 1024          # 5 MiB

OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------- ヘルパ ----------
def parse_year(created_at: str) -> int:
    """
    Twitter 'created_at' 文字列 → 年 (int)
      例: 'Fri Mar 14 18:16:18 +0000 2025' -> 2025
    """
    return int(created_at.rsplit(" ", 1)[-1])


def open_writer(min_year: int, max_year: int, part_no: int) -> tuple[str, TextIO]:
    """
    書き込み用ファイルハンドルを開く（暫定名 = プレフィックス _tmp_pXX.jsonl）
    ファイル完成時に rename で確定名へ変更する。
    """
    tmp_name = f"tmp_p{part_no:02d}.jsonl"
    fh = open(OUT_DIR / tmp_name, "w", encoding="utf-8", newline="\n")
    return tmp_name, fh


# ---------- メイン ----------
def main() -> None:
    if not INPUT_FILE.exists():
        raise SystemExit(f"入力ファイルが見つかりません: {INPUT_FILE}")

    current_size: int | None = None
    year_min = year_max = None
    part_no = 1
    out_tmp_name: str | None = None
    out_fh: TextIO | None = None

    def rotate(new_year: int) -> None:
        """現在のファイルを閉じてリネームし、次ファイルを準備"""
        nonlocal part_no, out_tmp_name, out_fh, year_min, year_max, current_size
        if out_fh is not None:
            out_fh.close()  # Windows の WinError 32 対策
            final_name = f"self_tweets_{year_min}-{year_max}_p{part_no:02d}.jsonl"
            os.replace(OUT_DIR / out_tmp_name, OUT_DIR / final_name)
            part_no += 1

        # 新しいファイルを開く
        year_min = year_max = new_year
        out_tmp_name, out_fh = open_writer(year_min, year_max, part_no)
        current_size = 0

    with gzip.open(INPUT_FILE, "rt", encoding="utf-8") as src:
        for line_raw in src:
            obj = json.loads(line_raw)
            year = parse_year(obj["created_at"])

            # 初回または rotate 直後にファイルを開く
            if out_fh is None:
                rotate(year)

            # 年範囲更新
            year_min = min(year_min, year)
            year_max = max(year_max, year)

            # 追加後サイズを試算
            line_json = json.dumps(obj, ensure_ascii=False) + "\n"
            line_bytes = len(line_json.encode("utf-8"))
            if current_size + line_bytes > MAX_BYTES:
                # 現在ファイルを確定 → 新ファイル開始
                rotate(year)

            out_fh.write(line_json)
            current_size += line_bytes

    # ループ終了後のファイル確定
    if out_fh is not None:
        out_fh.close()
        final_name = f"self_tweets_{year_min}-{year_max}_p{part_no:02d}.jsonl"
        os.replace(OUT_DIR / out_tmp_name, OUT_DIR / final_name)

    print(f"✔ 完了: {OUT_DIR} に分割保存しました。")


if __name__ == "__main__":
    main()
