from pathlib import Path

import pytest

from news_collect_validate.validate import INDEX_PATHS, article_urls, validate, validate_file, validate_text


def markdown(n=10, articles=None, unique=None):
    articles = n if articles is None else articles
    unique = articles if unique is None else unique
    return '\n'.join(
        f'**Item {i}**\n{i + 1}. [Source](' +
        (f'https://example.com/news/{i % unique}' if i < articles else 'https://example.com/') + ')'
        for i in range(n)
    )


@pytest.mark.parametrize('path', sorted(INDEX_PATHS) + ['/about', '/abc123'])
def test_indexes(path):
    url = 'https://example.com' + path
    assert article_urls(f'[Source]({url})') == ([], [url])


@pytest.mark.parametrize('url', [
    'https://example.com/news/story', 'http://example.com/a/b/',
    'https://example.com/1234', 'https://example.com/story2026',
    'https://news.ycombinator.com/item?id=12',
    'https://news.ycombinator.com/item?foo=1&id=12345',
    'https://news.ycombinator.com/?id=12',
])
def test_articles(url):
    assert article_urls(f'[Source]({url})') == ([url], [])


@pytest.mark.parametrize('url', [
    'https://news.ycombinator.com/item?id=1',
    'https://example.com/item?id=12345',
    'https://news.ycombinator.com.evil.test/item?id=12345',
])
def test_hn_exception_limits(url):
    assert article_urls(f'[Source]({url})') == ([], [url])


def test_only_inline_http_links():
    assert article_urls('https://example.com/a/b <https://example.com/a/b> [a](ftp://example.com/a/b)') == ([], [])


@pytest.mark.parametrize('articles,ok', [(7, False), (8, True), (10, True)])
def test_ratio_boundary(articles, ok):
    result = validate_text('trend', markdown(articles=articles))
    assert result['ok'] is ok
    assert result['stats']['ratio'] == articles / 10


@pytest.mark.parametrize('unique,ok', [(6, False), (7, True)])
def test_duplicate_boundary(unique, ok):
    result = validate_text('trend', markdown(unique=unique))
    assert result['ok'] is ok
    assert result['stats']['unique_articles'] == unique


@pytest.mark.parametrize('mode,n,ok', [('borders', 5, False), ('borders', 6, True), ('trend', 9, False), ('trend', 10, True)])
def test_min_items(mode, n, ok):
    assert validate_text(mode, markdown(n))['ok'] is ok


def test_mode_difference_and_count_fallbacks():
    text = '\n'.join(f'🔗 [Source](https://example.com/news/{i})' for i in range(10))
    assert validate_text('borders', text)['ok']
    assert validate_text('trend', text)['ok']
    assert validate_text('borders', '**One**\n' + text)['stats']['items'] == 1
    assert validate_text('trend', '1. [One](https://example.com/news/extra)\n' + text)['stats']['items'] == 1
    plain = text.replace('🔗 ', '')
    assert not validate_text('borders', plain)['ok']
    assert validate_text('trend', plain)['ok']
    assert validate_text('borders', markdown(6))['ok']
    assert not validate_text('trend', markdown(6))['ok']


def test_trend_fallback_counts_index_links():
    text = markdown(articles=8)
    import re
    text = re.sub(r'^\d+\. ', '', text, flags=re.M)
    assert validate_text('trend', text)['stats']['items'] == 10
    assert validate_text('trend', text)['ok']


@pytest.mark.parametrize('content', ['', '   \n', 'No links', '\n'.join(['**Heading**'] * 10)])
def test_empty_or_no_links(tmp_path, content):
    path = tmp_path / 'empty.md'
    path.write_text(content)
    assert not validate_file('borders', path)['ok']
    assert validate('borders', path)


def test_input_failures(tmp_path, monkeypatch):
    assert not validate_file('trend', tmp_path / 'missing.md')['ok']
    assert not validate_file('trend', tmp_path)['ok']
    path = tmp_path / 'bad.md'
    path.write_bytes(b'\xff')
    assert not validate_file('trend', path)['ok']
    def denied(*args, **kwargs):
        raise PermissionError('denied')
    monkeypatch.setattr(Path, 'read_text', denied)
    assert not validate_file('trend', path)['ok']


def test_malformed_url_fails_closed():
    assert not validate_text('trend', '[bad](https://[broken/a/b)')['ok']


def test_invalid_mode():
    with pytest.raises(ValueError):
        validate_text('other', markdown())
