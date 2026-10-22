# LLM Wiki Agent Rules

- Treat `Raw/Sources/` as source material, not compiled notes. Preserve its meaning and do not silently rewrite evidence.
- Write reusable knowledge only under `Wiki/`.
- Keep every compiled note linked to one or more existing files in `Raw/Sources/` using the `sources` frontmatter field.
- Search `Wiki/catalog.jsonl` before opening broad Raw context. Read the most relevant compiled notes first.
- Do not invent citations or make claims unsupported by cited sources. Keep source wording and your synthesis distinguishable.
- Keep compiled notes focused, concise, and useful across more than one question. Use the templates in `_templates/`.
- Before committing, run `build`, `lint`, and source checks with `scripts/wiki_tool.py`, plus `scripts/audit_public.py`.
- Do not include secrets, machine-local paths, private keys, or Obsidian cache/plugin state in the public wiki.
