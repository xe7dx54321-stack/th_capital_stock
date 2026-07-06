"""Cleanup local artifacts safely.

Classifies files into:
- A: Must keep (source, config, main DB)
- B: Auto-delete (caches)
- C: Quarantine (suspicious artifacts)
- D: User confirmation needed
- E: Forbidden (secrets, .git, main DB)

Supports --dry-run and --apply modes.
"""

import os
import shutil
import argparse
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
QUARANTINE_BASE = Path("/Users/apple/Documents/local_cleanup_quarantine")

CACHE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    ".coverage",
    ".DS_Store",
]

CACHE_FILE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.sqlite-wal",
    "*.sqlite-shm",
]

QUARANTINE_EXTENSIONS = [
    ".log", ".tmp", ".bak", ".cache",
    ".html", ".jsonl", ".json", ".csv",
    ".pkl", ".pickle", ".h5", ".hdf5", ".npy", ".npz",
    ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".pdf", ".docx", ".xlsx", ".pptx",
]

FORBIDDEN_PATHS = [
    ".git",
    ".env",
    "secrets",
    "01_data/db/smr.db",
]

MUST_KEEP_PATHS = [
    "01_data/db/smr.db",
]

IGNORE_PATTERNS = [
    ".git",
    ".env",
    "secrets",
    "01_data/db/smr.db",
]


def is_ignored(path: Path) -> bool:
    path_str = str(path.relative_to(PROJECT_ROOT))
    for pattern in IGNORE_PATTERNS:
        if pattern in path_str or path.name == pattern:
            return True
    return False


def is_forbidden(path: Path) -> bool:
    path_str = str(path.relative_to(PROJECT_ROOT))
    parts = path_str.split(os.sep)
    
    if parts[0] == ".git":
        return True
    
    if parts[0] == ".env":
        return True
    
    if parts[0] == "secrets":
        return True
    
    if path_str == "01_data/db/smr.db":
        return True
    
    return False


def is_must_keep(path: Path) -> bool:
    path_str = str(path.relative_to(PROJECT_ROOT))
    for pattern in MUST_KEEP_PATHS:
        if path_str == pattern or path.name == pattern:
            return True
    return False


def is_cache(path: Path) -> bool:
    if path.is_dir() and path.name in CACHE_PATTERNS:
        return True
    if path.is_file():
        for pattern in CACHE_FILE_PATTERNS:
            if path.match(pattern):
                return True
        if path.name in CACHE_PATTERNS:
            return True
    return False


def is_quarantine_candidate(path: Path) -> bool:
    if is_ignored(path):
        return False
    if is_forbidden(path):
        return False
    if is_must_keep(path):
        return False
    if path.is_file() and path.suffix.lower() in QUARANTINE_EXTENSIONS:
        return True
    if path.name.startswith("_archive") or path.name == "archive":
        return True
    return False


def is_user_confirmation_needed(path: Path) -> bool:
    if is_ignored(path):
        return False
    if is_forbidden(path):
        return False
    if is_must_keep(path):
        return False
    if is_cache(path):
        return False
    if is_quarantine_candidate(path):
        return False
    return True


def scan_project() -> dict:
    cache_items = []
    quarantine_items = []
    confirmation_items = []
    forbidden_items = []
    must_keep_items = []

    for path in PROJECT_ROOT.rglob("*"):
        if not path.exists():
            continue

        if is_forbidden(path):
            forbidden_items.append({
                "path": str(path.relative_to(PROJECT_ROOT)),
                "type": "file" if path.is_file() else "dir",
            })
            continue

        if is_must_keep(path):
            must_keep_items.append({
                "path": str(path.relative_to(PROJECT_ROOT)),
                "type": "file" if path.is_file() else "dir",
            })
            continue

        if is_cache(path):
            try:
                if path.is_dir():
                    size_bytes = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                else:
                    size_bytes = path.stat().st_size
                cache_items.append({
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "type": "file" if path.is_file() else "dir",
                    "size_bytes": size_bytes,
                })
            except Exception:
                pass
            continue

        if is_quarantine_candidate(path):
            try:
                size_bytes = path.stat().st_size if path.is_file() else 0
                quarantine_items.append({
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "type": "file" if path.is_file() else "dir",
                    "size_bytes": size_bytes,
                })
            except Exception:
                pass
            continue

        if is_user_confirmation_needed(path):
            confirmation_items.append({
                "path": str(path.relative_to(PROJECT_ROOT)),
                "type": "file" if path.is_file() else "dir",
            })

    return {
        "cache": cache_items,
        "quarantine": quarantine_items,
        "confirmation": confirmation_items,
        "forbidden": forbidden_items,
        "must_keep": must_keep_items,
    }


def execute_cleanup(scan_result: dict, dry_run: bool = True) -> dict:
    quarantine_dir = QUARANTINE_BASE / f"th_capital_stock_smr_d61_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    deleted_count = 0
    deleted_size_bytes = 0
    quarantined_count = 0
    quarantined_size_bytes = 0

    manifest = {
        "timestamp": datetime.now().isoformat(),
        "dry_run": dry_run,
        "quarantine_dir": str(quarantine_dir),
        "deleted": [],
        "quarantined": [],
        "skipped": [],
    }

    print(f"\n{'[DRY RUN]' if dry_run else '[EXECUTING]'}")
    print(f"Quarantine directory: {quarantine_dir}")

    for item in scan_result["cache"]:
        path = PROJECT_ROOT / item["path"]
        if dry_run:
            print(f"[DELETE] {item['path']} ({item['size_bytes'] / (1024*1024):.2f} MB)")
        else:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                deleted_count += 1
                deleted_size_bytes += item["size_bytes"]
            except Exception as e:
                manifest["skipped"].append({
                    "path": item["path"],
                    "reason": str(e),
                })
        manifest["deleted"].append(item)

    if not dry_run:
        quarantine_dir.mkdir(parents=True, exist_ok=True)

    for item in scan_result["quarantine"]:
        path = PROJECT_ROOT / item["path"]
        dest = quarantine_dir / item["path"]
        if dry_run:
            print(f"[QUARANTINE] {item['path']} -> {dest}")
        else:
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if path.is_dir():
                    shutil.move(str(path), str(dest))
                else:
                    shutil.move(str(path), str(dest))
                quarantined_count += 1
                quarantined_size_bytes += item.get("size_bytes", 0)
            except Exception as e:
                manifest["skipped"].append({
                    "path": item["path"],
                    "reason": str(e),
                })
        manifest["quarantined"].append(item)

    for item in scan_result["confirmation"]:
        print(f"[SKIP - CONFIRMATION NEEDED] {item['path']}")
        manifest["skipped"].append({
            "path": item["path"],
            "reason": "requires user confirmation",
        })

    for item in scan_result["forbidden"]:
        print(f"[SKIP - FORBIDDEN] {item['path']}")
        manifest["skipped"].append({
            "path": item["path"],
            "reason": "forbidden path",
        })

    manifest["summary"] = {
        "deleted_count": deleted_count,
        "deleted_size_bytes": deleted_size_bytes,
        "quarantined_count": quarantined_count,
        "quarantined_size_bytes": quarantined_size_bytes,
        "skipped_count": len(manifest["skipped"]),
    }

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Cleanup local artifacts")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode")
    parser.add_argument("--apply", action="store_true", help="Execute cleanup")
    parser.add_argument("--output", help="Output manifest path")
    args = parser.parse_args()

    if args.apply:
        dry_run = False
    else:
        dry_run = True

    print("Scanning project for artifacts...")
    scan_result = scan_project()

    print(f"\nScan results:")
    print(f"- Cache items: {len(scan_result['cache'])}")
    print(f"- Quarantine candidates: {len(scan_result['quarantine'])}")
    print(f"- Confirmation needed: {len(scan_result['confirmation'])}")
    print(f"- Forbidden paths: {len(scan_result['forbidden'])}")
    print(f"- Must keep: {len(scan_result['must_keep'])}")

    manifest = execute_cleanup(scan_result, dry_run=dry_run)

    print(f"\n{'Dry run' if dry_run else 'Execution'} complete!")
    print(f"Summary:")
    print(f"- Deleted: {manifest['summary']['deleted_count']} items, "
          f"{manifest['summary']['deleted_size_bytes'] / (1024*1024):.2f} MB")
    print(f"- Quarantined: {manifest['summary']['quarantined_count']} items, "
          f"{manifest['summary']['quarantined_size_bytes'] / (1024*1024):.2f} MB")
    print(f"- Skipped: {manifest['summary']['skipped_count']} items")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    else:
        manifest_path = PROJECT_ROOT / "tmp" / "cleanup_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"\nManifest saved to: {manifest_path}")


if __name__ == "__main__":
    main()
