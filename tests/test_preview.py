"""The selected recipe is checked before a fresh preview is published locally."""
import copy
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
from tools import fit


@pytest.fixture
def preview_env(tmp_path, monkeypatch):
    recs = build.load_recipes()
    calls = []
    monkeypatch.setattr(build, 'OUT', tmp_path / 'out')
    monkeypatch.setattr(build, 'load_recipes', lambda: copy.deepcopy(recs))

    def check(files, screenshots=None):
        assert all(pathlib.Path(f).is_file() for f in files)
        calls.append(('fit', [pathlib.Path(f).name for f in files]))
        return 0

    def pdf(codes, source_dir=None, output_dir=None, quiet=False):
        assert calls[-1][0] == 'fit'
        assert source_dir is not None and output_dir is not None and quiet
        assert list(source_dir.glob('*.dc.html'))
        calls.append(('pdf', codes))
        output_dir.mkdir(parents=True, exist_ok=True)
        names = [codes[0]] + ([codes[0] + '-tent'] if recs[codes[0]].get('tent') else [])
        files = [output_dir / f'{name}.pdf' for name in names]
        for path in files:
            path.write_bytes(b'%PDF-preview-test')
        return files

    monkeypatch.setattr(fit, 'check', check)
    monkeypatch.setattr(build, 'pdf', pdf)
    return recs, calls


@pytest.mark.parametrize('code,expected', [
    ('ck-003', ['CK-003-1.dc.html', 'CK-003-2.dc.html', 'CK-003-3.dc.html', 'CK-003-tent.dc.html']),
    ('BR-024', ['BR-024-1.dc.html', 'BR-024-2.dc.html', 'BR-024-3.dc.html', 'BR-024-tent.dc.html']),
    ('FR-003', ['FR-003.dc.html']),
])
def test_preview_checks_all_selected_pages_before_pdf(preview_env, code, expected):
    recs, calls = preview_env
    result = build.preview(code)
    code = code.upper()
    assert calls == [('fit', expected), ('pdf', [code])]
    dest = build.OUT / 'preview' / code
    assert sorted(p.name for p in dest.glob('*.dc.html')) == expected
    assert result and all(p.is_file() and dest in p.parents for p in result)
    assert not (build.OUT / 'project').exists()
    assert not (build.OUT / 'site').exists()


def test_preview_fails_invalid_draft_instead_of_skipping_it(preview_env):
    recs, calls = preview_env
    recs['CK-003']['formula']['parts'][0]['rows'][0]['g'] = '750'
    with pytest.raises(SystemExit, match='lint'):
        build.preview('CK-003')
    assert not calls
    assert not (build.OUT / 'preview' / 'CK-003').exists()


def test_preview_does_not_lint_unrelated_recipes(preview_env):
    recs, calls = preview_env
    recs['CA-011']['formula']['parts'][0]['rows'][0]['g'] = '750'
    build.preview('FR-003')
    assert calls[-1] == ('pdf', ['FR-003'])


def test_fit_failure_stops_pdf_and_preserves_last_success(preview_env, monkeypatch):
    recs, calls = preview_env
    old = build.OUT / 'preview' / 'CK-003' / 'pdf' / 'CK-003.pdf'
    old.parent.mkdir(parents=True)
    old.write_bytes(b'previous successful preview')
    monkeypatch.setattr(fit, 'check', lambda *args, **kwargs: 1)
    with pytest.raises(SystemExit, match='fit'):
        build.preview('CK-003')
    assert not calls
    assert old.read_bytes() == b'previous successful preview'
    assert not list(build.OUT.glob('.preview-*'))


def test_pdf_failure_does_not_publish_partial_preview(preview_env, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('printer failed')
    monkeypatch.setattr(build, 'pdf', fail)
    with pytest.raises(RuntimeError, match='printer failed'):
        build.preview('CK-003')
    assert not (build.OUT / 'preview' / 'CK-003').exists()
    assert not list(build.OUT.glob('.preview-*'))


def test_success_replaces_stale_selected_preview_files(preview_env):
    dest = build.OUT / 'preview' / 'FR-003'
    dest.mkdir(parents=True)
    (dest / 'FR-003-99.dc.html').write_text('old page')
    other = build.OUT / 'preview' / 'OTHER.txt'
    other.write_text('keep')
    build.preview('FR-003')
    assert not (dest / 'FR-003-99.dc.html').exists()
    assert other.read_text() == 'keep'


def test_final_move_failure_preserves_previous_preview(preview_env, monkeypatch):
    old = build.OUT / 'preview' / 'FR-003' / 'pdf' / 'FR-003.pdf'
    old.parent.mkdir(parents=True)
    old.write_bytes(b'previous successful preview')
    replace = pathlib.Path.replace

    def fail_publish(path, target):
        if path.name.startswith('.preview-'):
            raise OSError('publication failed')
        return replace(path, target)

    monkeypatch.setattr(pathlib.Path, 'replace', fail_publish)
    with pytest.raises(OSError, match='publication failed'):
        build.preview('FR-003')
    assert old.read_bytes() == b'previous successful preview'
    assert not list(build.OUT.glob('.preview-*'))


def test_success_records_freshness_without_changing_artboards(preview_env):
    import datetime, json
    build.preview('FR-003')
    dest = build.OUT / 'preview' / 'FR-003'
    report = json.loads((dest / 'preview.json').read_text())
    assert report['code'] == 'FR-003' and report['schema_version'] == 1
    assert len(report['inputs_sha256']) == 64
    assert len(report['renderer']['sha256']) == 64
    assert report['renderer']['version']
    assert datetime.datetime.fromisoformat(report['generated_at']).tzinfo is not None
    assert report['pdfs'] == ['pdf/FR-003.pdf']
    assert report['inputs_sha256'] not in (dest / 'FR-003.dc.html').read_text()


def test_status_detects_recipe_edits_and_preserves_old_record(preview_env):
    recs, calls = preview_env
    build.preview('FR-003')
    build.preview_status('fr-003')
    record = build.OUT / 'preview' / 'FR-003' / 'preview.json'
    original = record.read_bytes()
    recs['FR-003']['formula']['rows'][0]['g'] += 1
    with pytest.raises(SystemExit) as exc:
        build.preview_status('FR-003')
    assert exc.value.code == 1
    assert record.read_bytes() == original


def test_status_detects_missing_or_changed_pdf(preview_env):
    build.preview('FR-003')
    pdf = build.OUT / 'preview' / 'FR-003' / 'pdf' / 'FR-003.pdf'
    pdf.write_bytes(b'wrong PDF')
    with pytest.raises(SystemExit):
        build.preview_status('FR-003')
    pdf.unlink()
    with pytest.raises(SystemExit):
        build.preview_status('FR-003')


def test_changed_inputs_during_render_do_not_replace_preview(preview_env, monkeypatch):
    recs, calls = preview_env
    build.preview('FR-003')
    record = build.OUT / 'preview' / 'FR-003' / 'preview.json'
    original = record.read_bytes()

    def edit_during_check(*args, **kwargs):
        recs['FR-003']['formula']['rows'][0]['g'] += 1
        calls.append(('fit', []))
        return 0

    monkeypatch.setattr(fit, 'check', edit_during_check)
    with pytest.raises(SystemExit, match='inputs changed'):
        build.preview('FR-003')
    assert record.read_bytes() == original


def test_interrupted_publication_is_recovered_even_when_next_preview_fails(preview_env):
    recs, calls = preview_env
    previous = build.OUT / 'preview' / '.FR-003.previous' / 'pdf' / 'FR-003.pdf'
    previous.parent.mkdir(parents=True)
    previous.write_bytes(b'last success')
    recs['FR-003']['formula']['rows'][0]['g'] = 'invalid'
    with pytest.raises(SystemExit, match='lint'):
        build.preview('FR-003')
    recovered = build.OUT / 'preview' / 'FR-003' / 'pdf' / 'FR-003.pdf'
    assert recovered.read_bytes() == b'last success'


@pytest.mark.parametrize('command', [build.preview, build.preview_status])
def test_recovery_precedes_loading_broken_yaml(preview_env, monkeypatch, command):
    import yaml
    previous = build.OUT / 'preview' / '.FR-003.previous' / 'pdf' / 'FR-003.pdf'
    previous.parent.mkdir(parents=True)
    previous.write_bytes(b'last success')

    def broken_yaml():
        raise yaml.YAMLError('unfinished edit')

    monkeypatch.setattr(build, 'load_recipes', broken_yaml)
    with pytest.raises(yaml.YAMLError):
        command('FR-003')
    restored = build.OUT / 'preview' / 'FR-003' / 'pdf' / 'FR-003.pdf'
    assert restored.read_bytes() == b'last success'


def test_real_preview_fit_does_not_require_a_previous_build(tmp_path, monkeypatch):
    # fit.check formerly wrote to ROOT/out even when preview used another output directory.
    monkeypatch.setattr(fit, 'ROOT', tmp_path / 'never-built')
    monkeypatch.setattr(build, 'OUT', tmp_path / 'preview-output')
    assert build.preview('FR-003')[0].read_bytes().startswith(b'%PDF-')


@pytest.mark.parametrize('code', ['../FR-003', '/FR-003', 'FR-003/extra', 'FR-003\n', 'FR-003*', ''])
def test_preview_rejects_unsafe_or_malformed_codes(preview_env, code):
    recs, calls = preview_env
    with pytest.raises(SystemExit, match='code'):
        build.preview(code)
    assert not calls and not build.OUT.exists()


@pytest.mark.parametrize('code,message', [('FR-999', 'no recipe'), ('CA-014', 'retired')])
def test_preview_rejects_unknown_or_retired_recipes(preview_env, code, message):
    with pytest.raises(SystemExit, match=message):
        build.preview(code)


def test_preview_rejects_missing_component_reference(preview_env):
    recs, calls = preview_env
    recs['FR-003']['uses'] = ['FR-999']
    with pytest.raises(SystemExit, match='lint'):
        build.preview('FR-003')
    assert not calls


@pytest.mark.parametrize('args', [[], ['FR-003', 'FR-004']])
def test_preview_cli_requires_exactly_one_code(monkeypatch, args):
    monkeypatch.setattr(sys, 'argv', ['build.py', 'preview', *args])
    with pytest.raises(SystemExit) as error:
        build.main()
    assert error.value.code == 2


def test_preview_cli_dispatches_selected_code(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, 'argv', ['build.py', 'preview', 'FR-003'])
    monkeypatch.setattr(build, 'preview', lambda code: calls.append(code), raising=False)
    build.main()
    assert calls == ['FR-003']


def test_preview_prints_draft_pdf_with_actual_renderer(tmp_path, monkeypatch):
    recs = build.load_recipes()
    recs['CA-011']['status'] = 'draft'
    monkeypatch.setattr(build, 'load_recipes', lambda: copy.deepcopy(recs))
    monkeypatch.setattr(build, 'OUT', tmp_path / 'out')
    files = build.preview('CA-011')
    assert len(files) == 1 and files[0].read_bytes().startswith(b'%PDF-')
    shots = build.OUT / 'preview' / 'CA-011' / 'shots'
    assert len(list(shots.glob('*.png'))) == 2
    assert not (files[0].parent / '_pdf.html').exists()


def test_preview_real_overflow_does_not_print_pdf(tmp_path, monkeypatch):
    recs = build.load_recipes()
    recs['CA-011']['status'] = 'draft'
    recs['CA-011']['method'][0]['text'] = 'This deliberately overlong method step must fail the fit check. ' * 40
    monkeypatch.setattr(build, 'load_recipes', lambda: copy.deepcopy(recs))
    monkeypatch.setattr(build, 'OUT', tmp_path / 'out')
    with pytest.raises(SystemExit, match='fit check failed'):
        build.preview('CA-011')
    assert not list(build.OUT.rglob('*.pdf'))
