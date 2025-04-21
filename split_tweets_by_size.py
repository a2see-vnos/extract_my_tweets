#!/usr/bin/env python3
"""
split_tweets_by_size.py
────────────────────────────────────────────────────────────
デフォルト:  年を跨いで 5 MiB 単位で連結 (output/aggregate)
--yearly-only: 年ごとに 5 MiB 分割して終了 (output/split)
"""

import argparse
import gzip
import json
import os
import pathlib
import re
import shutil
from typing import TextIO

INPUT_GZ   = pathlib.Path("output/self_tweets.slim.jsonl.gz")
TMP_DIR    = pathlib.Path("tmp_years")
SPLIT_DIR  = pathlib.Path("output/split")
AGG_DIR    = pathlib.Path("output/aggregate")
MAX_BYTES  = 5 * 1024 * 1024  # 5 MiB

YEAR_FILE_RE = re.compile(r"self_tweets_(\d{4})_p(\d{2})\.jsonl$")


# ── 共通 ──────────────────────────────────────────
def parse_year(created_at: str) -> int:
    return int(created_at.rsplit(" ", 1)[-1])


def ensure_dirs(*dirs):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# ── STEP‑1: 年別バケツ ─────────────────────────────
def bucket_by_year():
    writers: dict[int, TextIO] = {}
    with gzip.open(INPUT_GZ, "rt", encoding="utf-8") as src:
        for ln in src:
            y = parse_year(json.loads(ln)["created_at"])
            if y not in writers:
                writers[y] = open(TMP_DIR / f"{y}.jsonl", "w", encoding="utf-8", newline="\n")
            writers[y].write(ln)
    for fh in writers.values():
        fh.close()
    print(f"[1/3] {len(writers)} 年に振り分け完了 → {TMP_DIR}")


# ── STEP‑2: 年ごと 5 MiB 分割 ───────────────────────
def split_year_file(path: pathlib.Path, year: int):
    part_no, size = 1, 0
    tmp = None
    out_fh = None

    def open_tmp():
        nonlocal tmp, out_fh, size
        tmp = SPLIT_DIR / f"tmp_{year}_p{part_no:02d}.jsonl"
        out_fh = open(tmp, "w", encoding="utf-8", newline="\n")
        size = 0

    def close_and_rename():
        nonlocal tmp, out_fh
        if out_fh is None:
            return
        out_fh.close()
        final = SPLIT_DIR / f"self_tweets_{year}_p{part_no:02d}.jsonl"
        os.replace(tmp, final)
        tmp, out_fh = None, None

    open_tmp()
    with open(path, "r", encoding="utf-8") as src:
        for ln in src:
            b = len(ln.encode())
            if size + b > MAX_BYTES:
                close_and_rename()
                part_no += 1
                open_tmp()
            out_fh.write(ln)
            size += b
    close_and_rename()
    print(f"    {year}: p{part_no:02d} まで生成")

def split_all_years():
    for p in sorted(TMP_DIR.glob("*.jsonl")):
        split_year_file(p, int(p.stem))
    shutil.rmtree(TMP_DIR)
    print(f"[2/3] 年ごと 5 MiB 分割完了 → {SPLIT_DIR}")


# ── STEP‑3: 集約 (デフォルト) ──────────────────────
def aggregate_files():
    files = sorted(
        SPLIT_DIR.glob("self_tweets_*.jsonl"),
        key=lambda p: (int(YEAR_FILE_RE.match(p.name)[1]),
                       int(YEAR_FILE_RE.match(p.name)[2])),
    )
    if not files:
        print("[3/3] 集約対象がありません。")
        return

    ensure_dirs(AGG_DIR)
    part_no, size = 1, 0
    start_year = end_year = None
    tmp = None
    out_fh = None

    def open_tmp():
        nonlocal tmp, out_fh, size
        tmp = AGG_DIR / f"tmp_p{part_no:02d}.jsonl"
        out_fh = open(tmp, "w", encoding="utf-8", newline="\n")
        size = 0

    def close_and_rename():
        nonlocal tmp, out_fh
        if out_fh is None:
            return
        out_fh.close()
        final = AGG_DIR / f"self_tweets_{start_year}-{end_year}_p{part_no:02d}.jsonl"
        os.replace(tmp, final)
        tmp, out_fh = None, None

    open_tmp()
    for fp in files:
        with open(fp, "r", encoding="utf-8") as src:
            for ln in src:
                y = parse_year(json.loads(ln)["created_at"])
                start_year = y if start_year is None else start_year
                end_year = y
                b = len(ln.encode())
                if size + b > MAX_BYTES:
                    close_and_rename()
                    part_no += 1
                    open_tmp()
                    start_year = end_year = y
                out_fh.write(ln)
                size += b
    close_and_rename()
    print(f"[3/3] 年代横断 5 MiB 分割完了 → {AGG_DIR}")


# ── メイン ──────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="自ツイ JSONL を 5 MiB 単位で分割します "
                    "(デフォルト: 年代横断で再集約)"
    )
    parser.add_argument(
        "--yearly-only",
        action="store_true",
        help="年ごとの 5 MiB 分割までで終了 (output/split のみ)"
    )
    args = parser.parse_args()

    if not INPUT_GZ.exists():
        raise SystemExit("self_tweets.slim.jsonl.gz が見つかりません。")

    ensure_dirs(TMP_DIR, SPLIT_DIR)
    bucket_by_year()
    split_all_years()

    if not args.yearly_only:
        aggregate_files()


if __name__ == "__main__":
    main()
