#!/usr/bin/env python3
"""Deterministic, standard-library tooling for the LLM Wiki."""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "Wiki"
SOURCE_DIR = ROOT / "Raw" / "Sources"
MANIFEST = ROOT / "Schema" / "source-manifest.jsonl"
ALLOWED = {"topic", "concept", "entity", "project", "log"}
FOLDERS = ("Topics", "Concepts", "Entities", "Projects", "Logs")

def md_files(folder):
    return sorted(p for p in folder.rglob("*.md") if p.is_file() and p.name.lower() != "index.md")

def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, re.S)
    if not match:
        return {}, text, "missing or malformed YAML frontmatter"
    data = {}
    active_list = None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.match(r"^(\w[\w-]*):\s*(.*?)\s*$", line)
        if item:
            key, val = item.groups()
            if val:
                if val.startswith("[") and val.endswith("]"):
                    data[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
                elif (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    data[key] = val[1:-1]
                elif val.lower() in {"true", "false"}:
                    data[key] = val.lower() == "true"
                elif re.fullmatch(r"-?\d+", val):
                    data[key] = int(val)
                else:
                    data[key] = val.strip("\"'")
                active_list = None
            else:
                data[key] = []
                active_list = key
        else:
            li = re.match(r"^\s+-\s*(.*?)\s*$", line)
            if li and active_list:
                data[active_list].append(li.group(1).strip("\"'"))
    return data, text, None

def rel(path):
    return path.relative_to(ROOT).as_posix()

def notes():
    return [p for folder in FOLDERS for p in md_files(WIKI / folder)]

def entries():
    result = []
    for path in notes():
        fm, text, _ = frontmatter(path)
        title_match = re.search(r"^#\s+(.+)$", text, re.M)
        tags = fm.get("tags", [])
        result.append({"path": rel(path), "title": title_match.group(1).strip() if title_match else path.stem,
                       "tag": tags[0] if isinstance(tags, list) and tags else "",
                       "topics": fm.get("topics", []) if isinstance(fm.get("topics", []), list) else [],
                       "sources": fm.get("sources", []) if isinstance(fm.get("sources", []), list) else [],
                       "updated": fm.get("updated", "")})
    return result

def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

def build():
    rows = entries()
    write_jsonl(WIKI / "catalog.jsonl", rows)
    lines = ["# Wiki index", "", "Compiled notes in this vault. Search them before opening broad Raw context.", ""]
    for row in rows:
        lines.append(f"- [{row['title']}]({row['path']}) — `{row['tag']}`")
    (WIKI / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for folder in FOLDERS:
        directory = WIKI / folder
        own = [r for r in rows if r["path"].startswith(f"Wiki/{folder}/")]
        text = [f"# {folder}", ""] + [f"- [{r['title']}]({Path(r['path']).name})" for r in own]
        (directory / "index.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(f"Built catalog and indexes for {len(rows)} Wiki notes.")

def source_rows():
    out = []
    for path in sorted(SOURCE_DIR.rglob("*.md")):
        if path.name.lower() == "index.md":
            continue
        fm, _, _ = frontmatter(path)
        processed = fm.get("Processed") is True or str(fm.get("Processed", "")).lower() == "true"
        out.append({"path": rel(path), "title": fm.get("Title", path.stem), "processed": processed, "covered_by": [], "updated": fm.get("updated", "")})
    return out

def manifest_rows():
    if not MANIFEST.exists():
        return []
    rows = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: pass
    return rows

def coverage_map():
    mapping = {row["path"]: [] for row in source_rows()}
    for note in notes():
        fm, _, _ = frontmatter(note)
        for source in fm.get("sources", []) if isinstance(fm.get("sources", []), list) else []:
            if source in mapping: mapping[source].append(rel(note))
    return mapping

def valid_source_path(source):
    if not isinstance(source, str):
        return False
    relative = PurePosixPath(source)
    if relative.is_absolute() or ".." in relative.parts or not source.startswith("Raw/Sources/"):
        return False
    try:
        resolved = (ROOT / Path(*relative.parts)).resolve(strict=True)
        resolved.relative_to(SOURCE_DIR.resolve(strict=True))
        return resolved.is_file()
    except (OSError, ValueError):
        return False

def valid_date(value):
    if not isinstance(value, str):
        return False
    try:
        dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False

def lint():
    errors = []
    required = ("tags", "topics", "status", "created", "updated", "sources", "source_count", "aliases")
    for path in notes():
        fm, _, err = frontmatter(path)
        if err: errors.append(f"{rel(path)}: {err}"); continue
        for key in required:
            if key not in fm:
                errors.append(f"{rel(path)}: missing {key}")
        tags, sources = fm.get("tags"), fm.get("sources")
        if not isinstance(tags, list) or len(tags) != 1 or tags[0] not in ALLOWED: errors.append(f"{rel(path)}: tags must contain exactly one allowed Wiki type")
        if not isinstance(fm.get("topics"), list): errors.append(f"{rel(path)}: topics must be a list")
        if not isinstance(fm.get("status"), str) or not fm.get("status", "").strip(): errors.append(f"{rel(path)}: status must be a non-empty string")
        if not valid_date(fm.get("created")): errors.append(f"{rel(path)}: created must use YYYY-MM-DD")
        if not valid_date(fm.get("updated")): errors.append(f"{rel(path)}: updated must use YYYY-MM-DD")
        if not isinstance(fm.get("aliases"), list): errors.append(f"{rel(path)}: aliases must be a list")
        if not isinstance(sources, list) or not sources: errors.append(f"{rel(path)}: sources must contain at least one Raw source path")
        else:
            for source in sources:
                if not valid_source_path(source): errors.append(f"{rel(path)}: invalid or missing source link {source!r}")
        try: count = int(fm.get("source_count", -1))
        except (TypeError, ValueError): count = -1
        if count != len(sources) if isinstance(sources, list) else True: errors.append(f"{rel(path)}: source_count does not match sources")
    return errors

def source_lint():
    errors = []
    mapping = coverage_map()
    for path in sorted(SOURCE_DIR.rglob("*.md")):
        if path.name.lower() == "index.md": continue
        fm, _, err = frontmatter(path)
        if err: errors.append(f"{rel(path)}: {err}"); continue
        for key in ("Title", "Reference", "Created", "Processed", "tags"):
            if key not in fm: errors.append(f"{rel(path)}: missing {key}")
        if not isinstance(fm.get("Title"), str) or not fm.get("Title", "").strip(): errors.append(f"{rel(path)}: Title must be a non-empty string")
        if not isinstance(fm.get("Reference"), str) or not fm.get("Reference", "").strip(): errors.append(f"{rel(path)}: Reference must be a non-empty string")
        if not valid_date(fm.get("Created")): errors.append(f"{rel(path)}: Created must use YYYY-MM-DD")
        if not isinstance(fm.get("Processed"), bool): errors.append(f"{rel(path)}: Processed must be true or false")
        if not isinstance(fm.get("tags"), list) or not fm.get("tags"): errors.append(f"{rel(path)}: tags must be a non-empty list")
        processed = fm.get("Processed") is True
        if processed and not mapping.get(rel(path)): errors.append(f"{rel(path)}: marked processed but has no Wiki coverage")
    return errors

def cmd_doctor():
    required = ["Raw/Sources", "Raw/Files", "Wiki/Topics", "Wiki/Concepts", "Wiki/Entities", "Wiki/Projects", "Wiki/Logs", "Schema", "_templates", "scripts", "tutorial"]
    missing = [p for p in required if not (ROOT / p).is_dir()]
    print(f"Python: {sys.version.split()[0]}")
    print(f"Compiled notes: {len(notes())}; Raw sources: {len(source_rows())}")
    print(f"Catalog: {'present' if (WIKI / 'catalog.jsonl').exists() else 'missing'}; source manifest: {'present' if MANIFEST.exists() else 'missing'}")
    if missing: print("Missing folders: " + ", ".join(missing)); return 1
    if sys.version_info < (3, 8): print("Python 3.8 or newer is required.", file=sys.stderr); return 1
    data_errors = []
    expected = {
        WIKI / "catalog.jsonl": ({"path", "title", "tag", "topics", "sources", "updated"}, {row["path"] for row in entries()}),
        MANIFEST: ({"path", "title", "processed", "covered_by", "updated"}, {row["path"] for row in source_rows()}),
    }
    for path, (required_keys, expected_paths) in expected.items():
        if not path.exists():
            continue
        rows = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                data_errors.append(f"{rel(path)}:{line_number}: invalid JSON")
                continue
            if not isinstance(row, dict) or not required_keys.issubset(row):
                data_errors.append(f"{rel(path)}:{line_number}: missing required fields")
                continue
            rows.append(row)
        actual_paths = {row["path"] for row in rows}
        if actual_paths != expected_paths or len(rows) != len(expected_paths):
            data_errors.append(f"{rel(path)}: entries do not match current notes or sources")
        print(f"{rel(path)} entries: {len(rows)}")
    for error in data_errors:
        print(error, file=sys.stderr)
    if data_errors:
        return 1
    return 0

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor"); sub.add_parser("build"); sub.add_parser("lint"); sub.add_parser("source-lint"); sub.add_parser("source-delta"); sub.add_parser("source-coverage")
    scan = sub.add_parser("source-scan"); scan.add_argument("--update", action="store_true"); scan.add_argument("--accept-covered", action="store_true")
    search = sub.add_parser("search-catalog"); search.add_argument("--query", required=True)
    log = sub.add_parser("log"); log.add_argument("--title", required=True); log.add_argument("--details", required=True)
    args = parser.parse_args()
    if args.command == "doctor": return cmd_doctor()
    if args.command == "build": build(); return 0
    if args.command == "lint": errors = lint()
    elif args.command == "source-lint": errors = source_lint()
    elif args.command == "source-scan":
        current = source_rows(); old = {r.get("path"): r for r in manifest_rows()}; mapping = coverage_map()
        for row in current:
            row["covered_by"] = sorted(mapping.get(row["path"], []))
            if row["covered_by"] and args.accept_covered: row["processed"] = True
            elif row["path"] in old and not args.accept_covered: row["processed"] = old[row["path"]].get("processed", row["processed"])
            previous = old.get(row["path"])
            unchanged = previous and all(previous.get(key) == row.get(key) for key in ("title", "processed", "covered_by"))
            row["updated"] = previous.get("updated", "") if unchanged else dt.date.today().isoformat()
        if args.update: write_jsonl(MANIFEST, current)
        print("\n".join(json.dumps(r, sort_keys=True) for r in current) or "No Raw sources found."); return 0
    elif args.command == "source-delta":
        known = {r.get("path") for r in manifest_rows()}; delta = [r for r in source_rows() if r["path"] not in known]
        print("\n".join(r["path"] for r in delta) or "No source delta."); return 0
    elif args.command == "source-coverage":
        mapping = coverage_map()
        for source, covered in mapping.items(): print(f"{source}: {', '.join(sorted(covered)) if covered else 'uncovered'}")
        return 0
    elif args.command == "search-catalog":
        query = args.query.casefold(); catalog = WIKI / "catalog.jsonl"
        if not catalog.exists(): print("Catalog missing; run build first.", file=sys.stderr); return 1
        hits = []
        for line in catalog.read_text(encoding="utf-8").splitlines():
            try: row = json.loads(line)
            except json.JSONDecodeError: continue
            if query in json.dumps(row, ensure_ascii=False).casefold(): hits.append(row)
        print("\n".join(f"{r['path']} — {r['title']}" for r in hits) or "No matches."); return 0
    elif args.command == "log":
        path = WIKI / "log.md"; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f: f.write(f"\n## {dt.date.today().isoformat()} — {args.title}\n\n{args.details}\n")
        print(f"Added entry to {rel(path)}"); return 0
    for error in errors: print(error, file=sys.stderr)
    if not errors: print("Checks passed.")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
