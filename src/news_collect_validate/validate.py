"""Offline checks extracted from validate-news-collection.py."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

# サイトのトップや一覧ページ。記事を特定できないURL。
INDEX_PATHS = {"", "/", "/news", "/news/", "/aiplus", "/aiplus/", "/index.html"}
MIN_ITEMS = {"borders": 6, "trend": 10}
MIN_ARTICLE_URL_RATIO = 0.8

def article_urls(text: str) -> tuple[list[str], list[str]]:
    """Markdown中のリンクURLを、記事URLとインデックスURLに分ける。"""
    urls = re.findall(r"\]\((https?://[^)\s]+)\)", text)
    articles, indexes = [], []
    for url in urls:
        parsed = urlparse(url)
        path = parsed.path or "/"
        # 記事URLの条件: パスがトップ/一覧でなく、階層かファイル名を持つ
        if path.rstrip("/") and path not in INDEX_PATHS and len(path.strip("/").split("/")) >= 2:
            articles.append(url)
        elif re.search(r"\d{4,}", path):  # /news/12345 のような単層でも数値IDなら記事
            articles.append(url)
        elif parsed.netloc == "news.ycombinator.com" and re.search(r"[?&]id=\d{2,}", url):
            # HNのコメントページURL（item?id=NNN）はスキル指定の正しい形式で、
            # IDがクエリ側にあるため単層パス判定に掛からない。記事URLとして扱う。
            articles.append(url)
        else:
            indexes.append(url)
    return articles, indexes


def _result(kind: str, path: str | None, problems: list[str], stats: dict | None = None) -> dict:
    if stats is None:
        stats = dict(articles=0, indexes=0, ratio=0.0, items=0, unique_articles=0)
    return {
        "ok": not problems, "mode": kind, "path": path,
        "problems": problems, "stats": stats,
    }

def _check_mode(kind: str) -> None:
    if kind not in MIN_ITEMS:
        raise ValueError(f"Unsupported mode: {kind}")

def validate_text(kind: str, text: str, *, path: str | None = None) -> dict:
    """Validate Markdown with the original classification and counting rules."""
    _check_mode(kind)
    problems: list[str] = []
    try:
        articles, indexes = article_urls(text)
    except ValueError as exc:
        return _result(kind, path, [f"URLを解析できません: {exc}"])
    total = len(articles) + len(indexes)

    # 件数（見出し行の数でざっくり数える）
    if kind == "borders":
        items = len(re.findall(r"^\*\*.+\*\*$", text, re.M)) or len(re.findall(r"^🔗", text, re.M))
    else:
        items = len(re.findall(r"^\d+\. \[", text, re.M)) or total
    ratio = len(articles) / total if total else 0.0
    stats = dict(
        articles=len(articles), indexes=len(indexes), ratio=ratio,
        items=items, unique_articles=len(set(articles)),
    )
    if total == 0:
        problems.append("リンクが1本も無い。収集できていない。")
        return _result(kind, path, problems, stats)

    if ratio < MIN_ARTICLE_URL_RATIO:
        problems.append(
            f"記事URLの比率が低い: {len(articles)}/{total} ({ratio:.0%})。"
            f"トップページURLで代用している疑い（創作の兆候）。例: {indexes[:3]}"
        )

    if len(set(articles)) < len(articles) * 0.7:
        problems.append(f"同じURLの使い回しが多い: ユニーク {len(set(articles))}/{len(articles)}")

    if items < MIN_ITEMS.get(kind, 5):
        problems.append(f"件数が少なすぎる: {items}件（最低 {MIN_ITEMS.get(kind, 5)}件）")

    return _result(kind, path, problems, stats)


def validate_file(kind: str, path: str | Path) -> dict:
    """Read UTF-8 input and fail closed on missing, empty or unreadable files."""
    _check_mode(kind)
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        return _result(kind, str(path), [f"ファイルを読めません: {path}: {exc}"])
    if not text:
        return _result(kind, str(path), [f"ファイルが無い、または空: {path}"])
    return validate_text(kind, text, path=str(path))

def validate(kind: str, path: Path) -> list[str]:
    """Compatibility wrapper returning the original list of problems."""
    return validate_file(kind, path)["problems"]
