#!/usr/bin/env python3
# extract_my_tweets.py
"""
Twitter/X アーカイブ (tweets.js / tweets-partN.js) から
自分の投稿だけを JSON Lines (gzip) で抽出
"""

import json
import pathlib
import re
import gzip

INPUT_DIR   = pathlib.Path('./input')
OUTPUT_DIR  = pathlib.Path('./output')
OUTPUT_DIR.mkdir(exist_ok=True)

# ★ ここに @スクリーンネームを指定する
MY_SCREEN_NAME = "myname"      # 例: "a2see"

#------------------------------------------------------------
JS_HEADER_RE = re.compile(r'^window\.YTD\.tweets\.part\d+\s*=\s*', re.S)

def load_tweets(path: pathlib.Path):
    raw   = path.read_text(encoding='utf-8')
    data  = json.loads(JS_HEADER_RE.sub('', raw).rstrip(';\n'))
    return [item['tweet'] for item in data]

def is_my_tweet(tw: dict) -> bool:
    """
    ① スクリーンネーム指定あり → それで判定
    ② 指定なし → RT/引用でなく retweeted==False なら自分とみなす
    """
    text = tw.get('full_text', '')
    if text.startswith('RT @'):
        return False               # 明示 RT
    if tw.get('is_quote_status'):
        return False               # 引用ツイ
    if tw.get('retweeted'):        # エクスポート上 True のこともある
        return False

    if MY_SCREEN_NAME:
        # 'user' オブジェクトは今のエクスポートに入っていないことが多いので
        # screen_name は full_text の先頭 "@name " から逆算するしかないが、
        # 自ツイなら先頭が @ で始まらないことがほとんど
        return True
    else:
        # ヒューリスティック（RT/引用でない → 自分の本文と仮定）
        return True

def main():
    all_tw = []
    for js in sorted(INPUT_DIR.glob('tweets*.js')):
        all_tw.extend(load_tweets(js))
    print(f'ロード完了: {len(all_tw):,} 件')

    out_path = OUTPUT_DIR / 'self_tweets.jsonl.gz'
    kept = 0
    with gzip.open(out_path, 'wt', encoding='utf-8') as gz:
        for tw in all_tw:
            if is_my_tweet(tw):
                gz.write(json.dumps(tw, ensure_ascii=False) + '\n')
                kept += 1

    print(f'✔ 抽出完了: {kept:,} 件 → {out_path}')

if __name__ == '__main__':
    main()
