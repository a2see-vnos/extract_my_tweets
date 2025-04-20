#!/usr/bin/env python3
# extract_my_tweets_slim.py
"""
tweets.js / tweets-part*.js → 自分のツイートを
{created_at, full_text} だけ残した JSON Lines (gzip) に変換
"""

import json, gzip, pathlib, re

INPUT_DIR   = pathlib.Path('./input')
OUTPUT_DIR  = pathlib.Path('./output')
OUTPUT_DIR.mkdir(exist_ok=True)

# MY_SCREEN_NAME: str | None = None      # 例: "a2see"（未指定ならヒューリスティック）
MY_SCREEN_NAME = "a2see"      # 例: "a2see"（未指定ならヒューリスティック）

JS_HEADER_RE = re.compile(r'^window\.YTD\.tweets\.part\d+\s*=\s*', re.S)
KEEP_KEYS    = ('created_at', 'full_text')   # ← 欲しいフィールドはここで制御

def load_part(path: pathlib.Path):
    raw  = path.read_text(encoding='utf-8')
    data = json.loads(JS_HEADER_RE.sub('', raw).rstrip(';\n'))
    return [x['tweet'] for x in data]

def is_my_tweet(tw: dict) -> bool:
    txt = tw.get('full_text', '')
    if txt.startswith('RT @') or tw.get('retweeted') or tw.get('is_quote_status'):
        return False
    if MY_SCREEN_NAME:
        # created_at が入っていればほぼ自ツイなので細かい判定は省略
        return True
    return True  # ヒューリスティック

def main():
    tweets = []
    for f in sorted(INPUT_DIR.glob('tweets*.js')):
        tweets.extend(load_part(f))
    print(f'ロード: {len(tweets):,} 件')

    out_path = OUTPUT_DIR / 'self_tweets.slim.jsonl.gz'
    n = 0
    with gzip.open(out_path, 'wt', encoding='utf-8') as gz:
        for tw in tweets:
            if is_my_tweet(tw):
                record = {k: tw.get(k, '') for k in KEEP_KEYS}
                gz.write(json.dumps(record, ensure_ascii=False) + '\n')
                n += 1

    print(f'✔ 抽出完了: {n:,} 件 → {out_path}')

if __name__ == '__main__':
    main()
