# Your first checked preview

Reading/printing published sheets requires neither Python nor AI. These steps are for editing source in a downloaded copy or checkout. Run commands from its root. CI uses Python 3.12; use that for the closest match. Other versions need separate verification.

## Set up once

On macOS/Linux with Python 3.12 installed:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Windows PowerShell: create with `py -3.12 -m venv .venv`, then use `.venv\Scripts\python.exe` instead of `python`; activation is optional. Linux may need browser OS libraries; CI uses `python -m playwright install --with-deps chromium`. Installation requires downloads; reading a saved PDF does not.

## Preview, then edit

```sh
python build.py list
python build.py preview FR-003
python build.py preview-status FR-003
```

Open `out/preview/FR-003/pdf/FR-003.pdf` and `out/preview/FR-003/shots/`. Failure can leave the previous successful preview present; that old PDF does not prove the new edit passed.

Read [the shared workflow](../CONTRIBUTING.md#shared-editing-workflow). Change a short ingredient note in your working copy, rerun preview and inspect the line. Grams are unquoted numbers (`g: 113`); unknown weights use `g: —` and a note. Append a revision for a retained change; preserve earlier rows. Do not commit a practice edit unless you intend to keep it.

Complete copyable sources: [component card](../tests/fixtures/recipes/FR-003.yaml), [two-page sheet](../tests/fixtures/recipes/CA-011.yaml). These demonstrate the format, not kitchen testing. To create a recipe run `python build.py new FR "Your recipe name"`, retain the fresh code/draft status, then adapt example fields and provide its own source/revision history. Do not reuse another recipe's identity/history.

## Troubleshooting

| Symptom | Next step |
|---|---|
| Missing Python module | Use the environment where requirements were installed. |
| Missing Chromium | Run `python -m playwright install chromium` there. |
| Invalid grams/list | Follow the field path; indexes start at zero. See [contract](recipe-contract.md). |
| Wrapped line/overflow | Shorten prose or move a section; never shrink type. See [design](design-system.md). |
| Stale preview | Rerun preview and inspect its new output. |
| Unrelated draft error | Preview only your recipe; all YAML must still parse. |

These commands do not publish. Drafts are **not private** once the repository/site is published. For diagrams see [the handbook](figures.md). Before contributing, lint and report what you actually verified.
