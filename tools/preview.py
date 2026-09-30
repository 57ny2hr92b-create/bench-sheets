"""Preview provenance and recoverable publication; no changes to printed content."""
import datetime
import hashlib
import importlib.metadata
import json
import pathlib
import platform
import shutil

import yaml

RENDERER_VERSION = '1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(root, recipe, references):
    """Hash content, not local paths or Git state (also works in downloaded ZIPs)."""
    root = pathlib.Path(root)
    renderer_files = [root / 'build.py', root / 'requirements.txt']
    for directory, pattern in [('tools', '*.py'), ('templates', '*.j2'), ('fonts', '*.woff2')]:
        renderer_files.extend((root / directory).rglob(pattern))
    renderer_files = {str(p.relative_to(root)): digest(p.read_bytes()) for p in sorted(renderer_files)}
    runtime = dict(python=platform.python_version(), **{
        name: importlib.metadata.version(name) for name in ('Jinja2', 'PyYAML', 'playwright')})
    renderer = dict(version=RENDERER_VERSION, sha256=digest(json.dumps(renderer_files, sort_keys=True).encode()), runtime=runtime)
    assets = {}
    for r in [recipe, *references.values()]:
        for item in [*(r.get('figures') or {}).get('items', []), r.get('schedule') or {}]:
            if item.get('svg') and not item.get('gen'):
                name = item['svg']
                assets[name] = digest((root / 'recipes' / 'figures' / name).read_bytes())
    source = yaml.safe_dump(dict(recipe=recipe, references=references), sort_keys=True, allow_unicode=True)
    inputs = dict(recipe_sha256=digest(source.encode()), assets=assets,
                  library_sha256=digest((root / 'library.yaml').read_bytes()), renderer=renderer)
    return dict(inputs_sha256=digest(json.dumps(inputs, sort_keys=True).encode()), **inputs)


def write_record(stage, recipe, inputs, pdfs):
    record = dict(record_version=1, code=recipe['code'], schema_version=recipe.get('schema_version', 1),
                  generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  **inputs, pdfs=[p.as_posix() for p in pdfs],
                  outputs={p.relative_to(stage).as_posix(): digest(p.read_bytes())
                           for p in sorted(stage.rglob('*')) if p.is_file()})
    (stage / 'preview.json').write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def recover(destination):
    """Recover an interrupted replacement on the next run. Run one preview per code at a time."""
    backup = destination.with_name(f'.{destination.name}.previous')
    if backup.exists():
        if destination.exists():
            shutil.rmtree(backup)
        else:
            backup.replace(destination)
    return backup


def publish(stage, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = recover(destination)
    if destination.exists():
        destination.replace(backup)
    try:
        stage.replace(destination)
    except BaseException:
        if backup.exists():
            backup.replace(destination)
        raise
    # The new preview is committed; leftover backups can be recovered/cleaned next run.
    if backup.exists():
        try:
            shutil.rmtree(backup)
        except OSError:
            pass


def is_current(destination, inputs):
    try:
        record = json.loads((destination / 'preview.json').read_text(encoding='utf-8'))
        if record['record_version'] != 1 or record['inputs_sha256'] != inputs['inputs_sha256']:
            return False
        outputs = record['outputs']
        if not outputs or not record['pdfs'] or not all(p in outputs for p in record['pdfs']):
            return False
        for name, expected in outputs.items():
            path = destination / name
            if not path.resolve().is_relative_to(destination.resolve()) or digest(path.read_bytes()) != expected:
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False
