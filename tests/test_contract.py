"""Public recipe and command contracts, shared by human and agent editors."""
import copy
import json
import pathlib
import subprocess
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
from tools import schema


@pytest.mark.parametrize('version', [2, '1', True, None, 0])
def test_unsupported_versions_are_rejected_before_rendering(version):
    recs = build.load_recipes()
    r = copy.deepcopy(recs['FR-003'])
    r['schema_version'] = version
    lint = schema.Lint()
    schema.lint_recipe(r, build.load_library(), recs, lint, build.FIGS)
    assert any('schema_version' in e for e in lint.errors)


def test_explicit_v1_and_legacy_recipe_render_identically():
    recs = build.load_recipes()
    old = copy.deepcopy(recs['FR-003'])
    new = copy.deepcopy(old)
    new['schema_version'] = 1
    assert build.render_recipe(build.env(), build.derive(old, recs)) == build.render_recipe(build.env(), build.derive(new, recs))


def test_new_recipes_declare_the_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(build, 'RECIPES', tmp_path)
    build.scaffold('FR', 'Example', build.load_recipes())
    assert yaml.safe_load(next(tmp_path.glob('*.yaml')).read_text())['schema_version'] == 1


def test_json_cli_outputs_one_machine_readable_report():
    run = subprocess.run([sys.executable, str(ROOT / 'build.py'), 'lint', '--json'], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    report = json.loads(run.stdout)
    assert report['ok'] is True and report['diagnostics'] == []
    assert report['checked'] == len(build.load_recipes())


def test_invalid_draft_is_a_failure_with_an_exact_json_location(monkeypatch, capsys):
    recs = build.load_recipes()
    recs['FR-003']['status'] = 'draft'
    recs['FR-003']['formula']['rows'][0]['g'] = '250'
    monkeypatch.setattr(build, 'load_recipes', lambda: recs)
    monkeypatch.setattr(sys, 'argv', ['build.py', 'lint', '--json'])
    with pytest.raises(SystemExit) as exc:
        build.main()
    assert exc.value.code == 1
    report = json.loads(capsys.readouterr().out)
    problem = next(d for d in report['diagnostics'] if d['path'] == 'formula.rows[0].g')
    assert problem['code'] == 'FR-003' and problem['severity'] == 'error'
    assert problem['file'] == 'recipes/FR-003.yaml'
    assert 'quotes' in problem['message'] and report['ok'] is False


def test_yaml_parse_failure_is_still_json(tmp_path, monkeypatch, capsys):
    (tmp_path / 'FR-003.yaml').write_text('code: [unterminated')
    monkeypatch.setattr(build, 'RECIPES', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['build.py', 'lint', '--json'])
    with pytest.raises(SystemExit) as exc:
        build.main()
    assert exc.value.code == 1
    report = json.loads(capsys.readouterr().out)
    assert report['ok'] is False and report['diagnostics'][0]['severity'] == 'error'


def test_human_lint_also_fails_invalid_drafts(monkeypatch):
    recs = build.load_recipes()
    recs['FR-003']['status'] = 'draft'
    recs['FR-003']['formula']['rows'][0]['g'] = '250'
    monkeypatch.setattr(build, 'load_recipes', lambda: recs)
    monkeypatch.setattr(sys, 'argv', ['build.py', 'lint'])
    with pytest.raises(SystemExit) as exc:
        build.main()
    assert exc.value.code == 1


@pytest.mark.parametrize('contents', ['code: [unterminated', '[]', 'name: Missing code'])
def test_input_errors_identify_the_source_file(tmp_path, monkeypatch, capsys, contents):
    source = tmp_path / 'FR-003.yaml'
    source.write_text(contents)
    monkeypatch.setattr(build, 'RECIPES', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['build.py', 'lint', '--json'])
    with pytest.raises(SystemExit):
        build.main()
    report = json.loads(capsys.readouterr().out)
    assert report['diagnostics'][0]['file'] == str(source)
