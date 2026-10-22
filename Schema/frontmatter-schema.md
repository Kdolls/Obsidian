# Frontmatter schema

## Raw source notes

Required keys: `Title`, `Reference`, `Created` (`YYYY-MM-DD`), `Processed` (boolean), and `tags` (list). Templates also include `Author` and `ContentType`.

## Compiled Wiki notes

Required keys: `tags` (exactly one of `topic`, `concept`, `entity`, `project`, `log`), `topics` (list), `status`, `created`, `updated`, `sources` (list of vault-relative Markdown paths under `Raw/Sources/`), `source_count` (equal to the number of sources), and `aliases` (list). Dates use `YYYY-MM-DD`.
