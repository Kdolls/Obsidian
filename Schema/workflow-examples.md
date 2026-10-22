# Workflow examples

## Ingest

1. Add cleaned Markdown to `Raw/Sources/` using `_templates/source-note.md`.
2. Search related Wiki notes with `python3 scripts/wiki_tool.py search-catalog --query "topic"`.
3. Read the relevant Wiki notes, then create or update focused notes under `Wiki/` with source links.
4. Run `build`, `lint`, `source-scan --update --accept-covered`, and `source-lint`.

## Query

Start at `Wiki/index.md`, search the catalog, and read relevant compiled notes. Read Raw sources only if the compiled notes lack detail or source-level verification is requested.
