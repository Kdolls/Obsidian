---
tags:
  - project
topics:
  - LLM Wiki
status: seed
created: 2026-10-22
updated: 2026-10-22
sources:
  - Raw/Sources/wanderloots-llm-wiki-core-setup-guide.md
source_count: 1
aliases: []
---

# LLM Wiki Core

## Summary

An LLM Wiki is a source-grounded knowledge system with separate raw and compiled layers. The core setup includes templates, agent rules, a machine-readable catalog, indexes, deterministic validation tools, and source coverage tracking.

## Workflow

Capture source material in `Raw/Sources/`, compile reusable notes in `Wiki/`, and keep each compiled note traceable to its sources. Agents should search the catalog and read relevant compiled notes before opening broad raw context. Run the maintenance checks after changes.

## Sources

- [[Raw/Sources/wanderloots-llm-wiki-core-setup-guide]]
