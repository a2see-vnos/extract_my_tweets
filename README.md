README.md
=========

> **extract_my_tweets** ― Twitter/X アーカイブを  
> 自分の投稿だけに絞り、軽量化・年別分割する 3 ステップツール

---

## 0. 準備

| 必要なもの | 説明 |
|------------|------|
| **Python 3.9 以上** | Windows / macOS / Linux いずれも動作 |
| **Twitter/X アーカイブ** | `tweets.js`, `tweets-part1.js`, … が入った一式 |

推奨ディレクトリ構成
```
extract_my_tweets/       ← リポジトリ（この README と *.py 3 本）
├─ input/                ← Twitterアーカイブ JS をここへ
├─ output/               ← 自動生成（空で OK）
├─ extract_my_tweets.py
├─ extract_my_tweets_slim.py
└─ split_tweets_by_size.py
```

ターミナルでルートに移動
```bash
cd path/to/extract_my_tweets
```

---

## 1. 自分のツイートだけ抽出

```
python extract_my_tweets.py
```

生成物  
```
output/self_tweets.jsonl.gz    # メタ情報込み・圧縮
```

> **注意**  
> `extract_my_tweets.py` 内の `MY_SCREEN_NAME` に自分の @名を設定してください。

---

## 2. 本文＋日付だけにスリム化

```
python extract_my_tweets_slim.py
```

生成物  
```
output/self_tweets.slim.jsonl.gz
```

> **注意**  
> `extract_my_tweets_slim.py` 内の `MY_SCREEN_NAME` に自分の @名を設定してください。

---

## 3. 5 MB 未満で分割

```
python split_tweets_by_size.py
```

生成物（例）
```
output/split/
 ├─ self_tweets_2018-2019_p01.jsonl
 ├─ self_tweets_2020-2021_p01.jsonl
 └─ self_tweets_2020-2021_p02.jsonl
```
* ファイル名: `self_tweets_<最小年>-<最大年>_pXX.jsonl`
* 1 ファイルのサイズは **5 MiB 未満**  
  （変更したい場合は `MAX_BYTES` を編集）

---

## ワークフローまとめ

```
input/*.js
   │  extract_my_tweets.py
   ▼
self_tweets.jsonl.gz
   │  extract_my_tweets_slim.py
   ▼
self_tweets.slim.jsonl.gz
   │  split_tweets_by_size.py
   ▼
split/*.jsonl  （5 MB 未満＆年範囲付き）
```

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `WinError 32` が出る | 最新版 `split_tweets_by_size.py` を使用（リネーム前に close 済） |
| 出力が空・少ない | `input/` フォルダに正しいファイル名 (`tweets.js` など) が置かれているか確認 |
| サイズ上限を変えたい | `split_tweets_by_size.py` の `MAX_BYTES` を変更して再実行 |

---

Happy archiving! 🎉