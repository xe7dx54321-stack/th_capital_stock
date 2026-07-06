"""Audit local storage usage in the project.

Scans the project directory for:
- Large files (>50MB)
- Large directories (>100MB)
- Cache directories
- Generated artifacts
- Git tracked/untracked status

Does NOT delete anything.
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
OUTPUT_DIR = PROJECT_ROOT / "tmp" / "local_storage_audit"


def run_cmd(cmd: str, cwd: Path) -> str:
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip()


def get_git_status() -> dict:
    tracked_files = set()
    untracked_files = set()
    ignored_files = set()

    try:
        tracked_out = run_cmd("git ls-files", PROJECT_ROOT)
        tracked_files = set(tracked_out.splitlines())
    except Exception:
        pass

    try:
        untracked_out = run_cmd("git ls-files --others --exclude-standard", PROJECT_ROOT)
        untracked_files = set(untracked_out.splitlines())
    except Exception:
        pass

    try:
        ignored_out = run_cmd("git ls-files --others --ignored --exclude-standard", PROJECT_ROOT)
        ignored_files = set(ignored_out.splitlines())
    except Exception:
        pass

    return {
        "tracked": list(tracked_files),
        "untracked": list(untracked_files),
        "ignored": list(ignored_files),
    }


def get_directory_sizes(limit_mb: int = 100) -> list[dict]:
    results = []
    for path in PROJECT_ROOT.iterdir():
        if not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        try:
            size_bytes = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            size_mb = size_bytes / (1024 * 1024)
            if size_mb > limit_mb:
                results.append({
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "size_mb": round(size_mb, 2),
                    "size_bytes": size_bytes,
                })
        except Exception:
            continue
    return sorted(results, key=lambda x: x["size_mb"], reverse=True)


def get_large_files(limit_mb: int = 50) -> list[dict]:
    results = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in str(path):
            continue
        try:
            size_bytes = path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            if size_mb > limit_mb:
                results.append({
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "size_mb": round(size_mb, 2),
                    "size_bytes": size_bytes,
                    "extension": path.suffix.lower(),
                })
        except Exception:
            continue
    return sorted(results, key=lambda x: x["size_mb"], reverse=True)


def get_cache_directories() -> list[dict]:
    cache_patterns = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        ".coverage",
    ]
    results = []
    for pattern in cache_patterns:
        for path in PROJECT_ROOT.rglob(pattern):
            if not path.exists():
                continue
            try:
                if path.is_dir():
                    size_bytes = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                else:
                    size_bytes = path.stat().st_size
                size_mb = size_bytes / (1024 * 1024)
                results.append({
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "type": pattern,
                    "size_mb": round(size_mb, 2),
                    "size_bytes": size_bytes,
                    "is_dir": path.is_dir(),
                })
            except Exception:
                continue
    return results


def get_artifact_files() -> list[dict]:
    artifact_extensions = [
        ".log", ".tmp", ".bak", ".cache", ".sqlite-wal", ".sqlite-shm",
        ".html", ".jsonl", ".json", ".csv", ".parquet", ".feather",
        ".pkl", ".pickle", ".h5", ".hdf5", ".npy", ".npz",
        ".pdf", ".docx", ".xlsx", ".pptx",
        ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ]
    results = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in str(path):
            continue
        if path.suffix.lower() in artifact_extensions:
            try:
                size_bytes = path.stat().st_size
                size_mb = size_bytes / (1024 * 1024)
                results.append({
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "extension": path.suffix.lower(),
                    "size_mb": round(size_mb, 2),
                    "size_bytes": size_bytes,
                })
            except Exception:
                continue
    return sorted(results, key=lambda x: x["size_bytes"], reverse=True)


def classify_file(path_str: str, git_status: dict) -> str:
    if path_str in git_status["tracked"]:
        return "tracked"
    elif path_str in git_status["ignored"]:
        return "ignored"
    elif path_str in git_status["untracked"]:
        return "untracked"
    else:
        return "unknown"


def generate_report(audit_data: dict) -> str:
    lines = []
    lines.append("# SMR-D6.1 Local Storage Audit Report")
    lines.append(f"\n**Generated:** {audit_data['metadata']['timestamp']}")
    lines.append(f"**Project:** {audit_data['metadata']['project_root']}")
    lines.append(f"**Total Size:** {audit_data['summary']['total_size_mb']:.2f} MB")
    lines.append(f"**.git Size:** {audit_data['summary']['git_size_mb']:.2f} MB")

    lines.append("\n## Summary")
    lines.append(f"- Total files: {audit_data['summary']['total_files']}")
    lines.append(f"- Large files (>50MB): {len(audit_data['large_files'])}")
    lines.append(f"- Large directories (>100MB): {len(audit_data['large_directories'])}")
    lines.append(f"- Cache directories: {len(audit_data['cache_directories'])}")
    lines.append(f"- Artifact files: {len(audit_data['artifact_files'])}")

    lines.append("\n## Large Directories (Top 30)")
    lines.append("\n| Directory | Size (MB) |")
    lines.append("|---|---|")
    for d in audit_data["large_directories"][:30]:
        lines.append(f"| {d['path']} | {d['size_mb']:.2f} |")

    lines.append("\n## Large Files (Top 50)")
    lines.append("\n| File | Size (MB) | Extension | Git Status |")
    lines.append("|---|---|---|---|")
    for f in audit_data["large_files"][:50]:
        git_status = classify_file(f["path"], audit_data["git_status"])
        lines.append(f"| {f['path']} | {f['size_mb']:.2f} | {f['extension']} | {git_status} |")

    lines.append("\n## Cache Directories")
    lines.append("\n| Path | Type | Size (MB) |")
    lines.append("|---|---|---|")
    for c in audit_data["cache_directories"]:
        lines.append(f"| {c['path']} | {c['type']} | {c['size_mb']:.2f} |")

    lines.append("\n## Artifact Files by Type")
    type_groups = {}
    for a in audit_data["artifact_files"]:
        ext = a["extension"] or "no_extension"
        if ext not in type_groups:
            type_groups[ext] = {"count": 0, "total_size_mb": 0}
        type_groups[ext]["count"] += 1
        type_groups[ext]["total_size_mb"] += a["size_mb"]

    lines.append("\n| Extension | Count | Total Size (MB) |")
    lines.append("|---|---|---|")
    for ext, stats in sorted(type_groups.items(), key=lambda x: x[1]["total_size_mb"], reverse=True):
        lines.append(f"| {ext} | {stats['count']} | {stats['total_size_mb']:.2f} |")

    return "\n".join(lines)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Collecting git status...")
    git_status = get_git_status()

    print("Calculating directory sizes...")
    large_dirs = get_directory_sizes()

    print("Finding large files...")
    large_files = get_large_files()

    print("Finding cache directories...")
    cache_dirs = get_cache_directories()

    print("Finding artifact files...")
    artifact_files = get_artifact_files()

    print("Calculating total size...")
    try:
        total_size_bytes = sum(f.stat().st_size for f in PROJECT_ROOT.rglob("*") if f.is_file())
    except Exception:
        total_size_bytes = 0

    try:
        git_dir = PROJECT_ROOT / ".git"
        git_size_bytes = sum(f.stat().st_size for f in git_dir.rglob("*") if f.is_file())
    except Exception:
        git_size_bytes = 0

    audit_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(PROJECT_ROOT),
        },
        "summary": {
            "total_size_mb": total_size_bytes / (1024 * 1024),
            "git_size_mb": git_size_bytes / (1024 * 1024),
            "total_files": len(list(PROJECT_ROOT.rglob("*"))),
        },
        "git_status": git_status,
        "large_directories": large_dirs,
        "large_files": large_files,
        "cache_directories": cache_dirs,
        "artifact_files": artifact_files,
    }

    json_path = OUTPUT_DIR / "audit_data.json"
    with open(json_path, "w") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)

    md_path = OUTPUT_DIR / "audit_report.md"
    with open(md_path, "w") as f:
        f.write(generate_report(audit_data))

    print(f"\nAudit complete!")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    print(f"\nTotal project size: {audit_data['summary']['total_size_mb']:.2f} MB")
    print(f".git size: {audit_data['summary']['git_size_mb']:.2f} MB")
    print(f"Large files (>50MB): {len(large_files)}")
    print(f"Large directories (>100MB): {len(large_dirs)}")


if __name__ == "__main__":
    main()
