# Command reference

Run commands from the vault root with Python 3:

- `python3 scripts/wiki_tool.py doctor` — inspect required folders, Python, indexes, manifest, and note counts.
- `python3 scripts/wiki_tool.py build` — rebuild `Wiki/catalog.jsonl`, main index, and per-folder indexes.
- `python3 scripts/wiki_tool.py lint` — validate compiled notes and their source links.
- `python3 scripts/wiki_tool.py source-scan` — list sources; add `--update` to write the manifest and `--accept-covered` to mark covered entries processed.
- `python3 scripts/wiki_tool.py source-lint` — validate source metadata and processed coverage.
- `python3 scripts/wiki_tool.py source-delta` — list sources not in the manifest.
- `python3 scripts/wiki_tool.py source-coverage` — report source coverage.
- `python3 scripts/wiki_tool.py search-catalog --query "text"` — search compiled Wiki metadata.
- `python3 scripts/wiki_tool.py log --title "title" --details "details"` — append to `Wiki/log.md`.
- `python3 scripts/audit_public.py` — scan text files for obvious secrets and machine-local state.

`scripts/install_hooks.sh` configures `.githooks/pre-commit`, which rebuilds indexes and runs lint and public audit checks.
