# Lint checklist

- Compiled notes have valid required frontmatter and exactly one allowed type tag.
- Every compiled note has at least one source, all source links exist under `Raw/Sources/`, and `source_count` matches.
- Source notes have `Title`, `Reference`, `Created`, `Processed`, and `tags`.
- A processed source has Wiki coverage.
- Catalog, manifest, indexes, and folder indexes are rebuilt.
- Public audit finds no obvious secrets, private keys, local paths, or plugin/cache state.
