import json
from pathlib import Path
import subprocess
import sys

import pytest

from news_collect_validate.cli import main

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('name,code', [('pass', 0), ('fail', 1)])
def test_json_file(name, code, capsys):
    path = str(ROOT / 'examples' / f'{name}.md')
    assert main(['borders', path, '--json']) == code
    result = json.loads(capsys.readouterr().out)
    assert set(result) == {'ok', 'mode', 'path', 'problems', 'stats'}
    assert result['ok'] is (code == 0)
    assert result['mode'] == 'borders'
    assert result['path'] == path
    assert isinstance(result['problems'], list)
    assert set(result['stats']) == {'articles', 'indexes', 'ratio', 'items', 'unique_articles'}
    if code == 0:
        assert result['stats'] == dict(articles=6, indexes=0, ratio=1.0, items=6, unique_articles=6)


def test_text_and_missing_json(capsys, tmp_path):
    assert main(['trend', '--text', '', '--json']) == 1
    assert json.loads(capsys.readouterr().out)['path'] is None
    assert main(['trend', str(tmp_path / 'missing'), '--json']) == 1
    result = json.loads(capsys.readouterr().out)
    assert not result['ok'] and result['problems']


@pytest.mark.parametrize('name,code', [('pass', 0), ('fail', 1)])
def test_module(name, code):
    process = subprocess.run([sys.executable, '-m', 'news_collect_validate', 'borders', str(ROOT / 'examples' / f'{name}.md')], capture_output=True, text=True)
    assert process.returncode == code
    assert process.stdout.startswith('PASS' if code == 0 else 'FAIL')
    assert not process.stderr


@pytest.mark.parametrize('args', [[], ['other', 'a.md'], ['trend'], ['trend', 'a.md', '--text', 'x']])
def test_usage_errors(args):
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2
