# news-collect-validate

ニュース収集Markdownの「創作見出し／index URL事故」を後工程に流さないための、
**現場の収集品質ゲート**。収集直後、[x-jev-gate](https://github.com/hrtaym1114-github/x-jev-gate)
の上流で使う小さなオフラインCLIです。

An offline quality gate for collected news Markdown, upstream of x-jev-gate.
It flags index-page substitutions that can accompany fabricated headlines, low
article-link ratios, repeated URLs, and insufficient item counts.

## Install / インストール

Python 3.10+。このディレクトリで実行 / From this directory:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Runtime uses only the Python standard library; pytest is a development dependency.
実行時は標準ライブラリのみ。LLM、ライブ取得、X投稿、ネットワーク通信は使いません。

## Run / 実行

```sh
news-collect-validate borders examples/pass.md
# PASS: examples/pass.md (borders)
# exit 0

news-collect-validate borders examples/fail.md
# FAIL: examples/fail.md (borders)
#   - 記事URLの比率が低い: 0/6 (0%)。...
# exit 1

news-collect-validate borders examples/pass.md --json
python -m news_collect_validate borders examples/pass.md
news-collect-validate trend --text '1. [Source](https://example.com/news/1234)' --json
# FAIL / exit 1: trend requires at least 10 items
```

PASS JSON:

```json
{"ok": true, "mode": "borders", "path": "examples/pass.md", "problems": [], "stats": {"articles": 6, "indexes": 0, "ratio": 1.0, "items": 6, "unique_articles": 6}}
```

`--text` sets `path` to `null`. JSON failures use the same shape and include
problem messages. Missing, empty, invalid UTF-8, and unreadable files fail closed.
入力ファイルの欠落・空・読み取り失敗も FAIL になります。

| Exit | Meaning / 意味 |
| --- | --- |
| 0 | PASS |
| 1 | FAIL: validation or input-read failure / 検証・読み取り失敗 |
| 2 | CLI usage error / 引数エラー |

## Rules / 判定ルール

Extracted from the original `validate-news-collection.py`; the URL heuristics,
thresholds, duplicate check, and counting fallbacks are preserved.

- Only inline Markdown HTTP(S) links matching `](https://...)` are counted.
- Index paths: empty path, `/`, `/news`, `/news/`, `/aiplus`, `/aiplus/`, `/index.html`.
- Article URLs: non-index paths with at least two segments, or paths containing
  at least four consecutive digits. The original HN exception accepts the exact
  host `news.ycombinator.com` with an `id` query matching two or more digits
  (including `item?id=...`); it does not restrict the path to `/item`.
- Article ratio must be **at least 80%**. Index links count against the ratio;
  a single index link does not necessarily fail the collection.
- Unique article URLs must be **at least 70%** of article-link occurrences.
- `borders`: at least **6** items; count lines matching `^\*\*.+\*\*$`,
  or, only if none match, lines starting with `🔗`.
- `trend`: at least **10** items; count lines matching `^\d+\. \[`,
  or, only if none match, use total link count (including indexes).

これはURL形状のヒューリスティックであり、見出しの真偽・記事の実在は検証しません。
サンプルの見出しとexample.comリンクはテスト専用です。
This checks URL shapes, not headline truth or whether articles exist. The example
headlines and example.com links are synthetic test fixtures.

MIT © 2026 hrtaym1114
