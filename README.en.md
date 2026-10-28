日本語: [README.md](README.md)
# news-collect-validate

This tool is an **offline quality gate for collected news Markdown**. It catches index-page URLs used in place of article links before they reach downstream tools. The CLI runs upstream of [x-jev-gate](https://github.com/hrtaym1114-github/x-jev-gate).

It flags low article-link ratios, excessive URL reuse, and too few items. These checks can reveal collection problems associated with fabricated headlines, but they do not verify headlines. **It uses no LLM, makes no network requests, and does not post content.**

[![Comparison of PASS and FAIL validation results](docs/media/news-collect-validate-strip.png)](docs/media/news-collect-validate-howto.gif)

- 🎞️ [GIF (PASS ↔ FAIL)](docs/media/news-collect-validate-howto.gif)
- Release: [v0.1.0](https://github.com/hrtaym1114-github/news-collect-validate/releases/tag/v0.1.0)

## Quick start (4 steps)

1. **Install** — `pip install git+https://github.com/hrtaym1114-github/news-collect-validate.git`
2. **Prepare** — Use Markdown you have already collected. Validation runs entirely offline and requires no API keys.
3. **Run** — `news-collect-validate borders your.md`
4. **Check the result** — **PASS** (exit 0) or **FAIL** (exit 1).

From a checkout of this repository:

```sh
news-collect-validate borders examples/pass.md
# PASS: examples/pass.md (borders)

news-collect-validate borders examples/fail.md
# FAIL: examples/fail.md (borders)
#   - 記事URLの比率が低い: 0/6 (0%)。トップページURLで代用している疑い（創作の兆候）。例: ['https://example.com/', 'https://example.com/', 'https://example.com/']
```

Diagnostic messages are currently in Japanese. The failure above says that the article URL ratio is too low (0 out of 6 links), suggesting that homepage URLs may have been substituted for article URLs.

## Installation

Requires Python ≥ 3.10. Uses only the Python standard library at runtime.

```sh
# Install directly from GitHub
pip install git+https://github.com/hrtaym1114-github/news-collect-validate.git

# Development (from a checkout of this repository)
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Validation does not use an LLM, fetch live content, post to X, or make network requests.

The two modes are `borders` for a bold-heading or 🔗 item list and `trend` for a numbered list whose items begin with `1. [` (then `2. [`, and so on).

## Usage

```sh
news-collect-validate borders examples/pass.md
news-collect-validate borders examples/fail.md
news-collect-validate borders examples/pass.md --json
python -m news_collect_validate borders examples/pass.md
news-collect-validate trend --text '1. [Source](https://example.com/news/1234)' --json
# Exit 1; JSON has "ok": false and "problems": ["件数が少なすぎる: 1件（最低 10件）"] (too few items; minimum 10)
```

Example PASS JSON:

```json
{"ok": true, "mode": "borders", "path": "examples/pass.md", "problems": [], "stats": {"articles": 6, "indexes": 0, "ratio": 1.0, "items": 6, "unique_articles": 6}}
```

Supply either a UTF-8 Markdown file path or `--text`, but not both. With `--text`, the JSON `path` is `null`. Missing files, empty input, invalid UTF-8, and file read failures produce FAIL (the validator fails closed: reports FAIL rather than passing). Omitting both input arguments is a CLI argument error.

| Exit code | Meaning |
| --- | --- |
| 0 | PASS |
| 1 | FAIL: validation or input read failure |
| 2 | CLI argument error |

## Validation rules

Derived from an earlier internal validation script, preserving its URL heuristics, thresholds, duplicate checks, and fallback item counts.

- Only inline Markdown HTTP(S) links matching `](https://...)` or `](http://...)` are counted.
- Index paths include an empty path, `/`, `/news`, `/news/`, `/aiplus`, `/aiplus/`, and `/index.html`.
- A URL counts as an article link if its path is not an index path and has at least two segments, or if its path contains at least four consecutive digits. Hacker News URLs also count when the network location is exactly `news.ycombinator.com` and the URL contains `?id=` or `&id=` followed by at least two digits; the path does not have to be `/item`. The Hacker News exception also applies to index paths. All other matched URLs count as index links.
- **Article URL ratio ≥ 80%**, measured against all matched links. Index links reduce the ratio; a single index link does not necessarily cause FAIL.
- **Unique article URL ratio ≥ 70%**, measured against article-link occurrences. Uniqueness uses exact URL strings.
- **`borders`: at least 6 items.** Counts lines matching `^\*\*.+\*\*$`; if there are none, counts lines beginning with `🔗`.
- **`trend`: at least 10 items.** Counts lines matching `^\d+\. \[`; if there are none, uses the total number of matched links, including index links.

These are URL-shape heuristics. They do not verify whether a headline is true or an article exists. Sample headlines and example.com links are test fixtures only.

## Related

- Downstream gate: [x-jev-gate](https://github.com/hrtaym1114-github/x-jev-gate) (PASS/BLOCK checks for X drafts).

MIT © 2026 hrtaym1114
