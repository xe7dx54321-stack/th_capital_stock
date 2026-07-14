#!/usr/bin/env python3
"""Build a read-only inventory and conservative cleanup classification.

The scanner intentionally has no delete or move operation.  A file classified as
DELETE_CANDIDATE is still emitted with ``approved=false`` and must pass the
separate removal gates documented in the MVP implementation plan.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


class Classification(str, Enum):
    KEEP = "KEEP"
    CONSOLIDATE = "CONSOLIDATE"
    FREEZE = "FREEZE"
    GENERATED = "GENERATED"
    SECRET = "SECRET"
    DELETE_CANDIDATE = "DELETE_CANDIDATE"


@dataclass(frozen=True)
class ClassificationResult:
    category: Classification
    rationale: str
    approved: bool = False


TEXT_SUFFIXES = {
    ".cjs",
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".ps1",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

SCAN_EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "venv",
}

MANIFEST_OUTPUT_PATHS = {
    "legacy_manifest/inventory.json",
    "legacy_manifest/classifications.csv",
}

AUDIT_REFERENCE_PREFIXES = (
    "legacy/",
    "legacy_manifest/",
)

GENERATED_PREFIXES = (
    "01_data/",
    "02_research/",
    "03_stock_pool/",
    "04_portfolio/",
    "05_risk/",
    "06_reports/",
    "07_publish/",
    "10_logs/",
    "11_smr_wiki/raw/",
    "11_smr_wiki/drafts/",
    "11_smr_wiki/wiki/",
    "12_smr_agents/handoffs/",
    "12_smr_agents/workspaces/",
    "09_runbooks/generated/",
)

CORE_PREFIXES = (
    "00_control/",
    "08_scripts/agents/",
    "08_scripts/backtest/",
    "08_scripts/data_harvester/",
    "08_scripts/dev/",
    "08_scripts/events/",
    "08_scripts/factor_engine/",
    "08_scripts/jobs/",
    "08_scripts/lib/",
    "08_scripts/maintenance/",
    "08_scripts/opportunity/",
    "08_scripts/portfolio/",
    "08_scripts/registry/",
    "08_scripts/reporting/",
    "08_scripts/research/",
    "08_scripts/risk_engine/",
    "08_scripts/scheduler/",
    "08_scripts/stock_pool/",
    "09_runbooks/",
    "12_smr_agents/profiles/",
    "12_smr_agents/schedules/",
    "api/",
    "docs/",
    "legacy_manifest/",
    "public/",
    "src/",
    "tools/",
)

SECRET_NAME_RE = re.compile(
    r"(^|/)(\.env($|\.)|secrets?(/|$)|credentials?(/|$))|"
    r"(token|secret|credential|private[_-]?key)",
    re.IGNORECASE,
)
PHASE_RE = re.compile(r"(^|[/_.-])(smr_)?(run_)?phase\d+", re.IGNORECASE)
SCRATCH_RE = re.compile(
    r"(^|/)(_(debug|tmp|check|inspect|test|verify)[^/]*|"
    r"(debug|query)_[^/]*)$",
    re.IGNORECASE,
)
QUOTED_PATH_RE = re.compile(
    r"[\"'`]([^\"'`]+(?:\.py|\.js|\.mjs|\.cjs|\.ts|\.tsx|\.json|\.md))[\"'`]"
)
JS_IMPORT_RE = re.compile(
    r"(?:from\s+|import\s*\(|require\s*\()\s*[\"']([^\"']+)[\"']"
)
MARKDOWN_LINK_PATH_RE = re.compile(
    r"\]\(([^)\s]+(?:\.py|\.js|\.mjs|\.cjs|\.ts|\.tsx|\.json|\.md))\)"
)


def normalize_path(value: str | Path) -> str:
    normalized = str(value).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def _is_secret(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    if name.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    return bool(SECRET_NAME_RE.search(path))


def _is_generated(path: str) -> bool:
    lowered = path.lower()
    if lowered.startswith(GENERATED_PREFIXES):
        return True
    parts = set(PurePosixPath(lowered).parts)
    if parts.intersection({"__pycache__", ".pytest_cache", "node_modules", "dist"}):
        return True
    return lowered.endswith((".db", ".sqlite", ".sqlite3", ".pyc", ".log"))


def _is_scratch(path: str) -> bool:
    posix = PurePosixPath(path)
    stem_path = str(posix.with_suffix(""))
    return bool(SCRATCH_RE.search(stem_path))


def classify_path(
    path: str,
    *,
    tracked: bool,
    size: int,
    reference_count: int,
    runtime_evidence: dict[str, Any] | None,
) -> ClassificationResult:
    """Classify one path conservatively; never approve deletion."""

    path = normalize_path(path)
    runtime_success = bool(runtime_evidence and runtime_evidence.get("success_count", 0))

    if _is_secret(path):
        return ClassificationResult(
            Classification.SECRET,
            "credential-like path; keep outside Git and runtime logs",
        )

    if _is_generated(path):
        return ClassificationResult(
            Classification.GENERATED,
            "runtime/build output governed by retention and ignore rules",
        )

    if _is_scratch(path):
        if runtime_success or reference_count > 0:
            return ClassificationResult(
                Classification.KEEP,
                "scratch-like name retained because it has a reference or recent runtime evidence",
            )
        return ClassificationResult(
            Classification.DELETE_CANDIDATE,
            "temporary investigation naming pattern; requires manual approval",
        )

    if PHASE_RE.search(path):
        if runtime_success or reference_count > 0:
            return ClassificationResult(
                Classification.KEEP,
                "legacy Phase asset still has a reference or recent runtime evidence",
            )
        return ClassificationResult(
            Classification.FREEZE,
            "unreferenced Phase-era asset; remove from default runtime before deletion",
        )

    if size >= 100_000 and PurePosixPath(path).suffix.lower() in {".py", ".js", ".ts", ".tsx"}:
        return ClassificationResult(
            Classification.CONSOLIDATE,
            "large source module should be split behind stable contracts",
        )

    if runtime_success or reference_count > 0:
        return ClassificationResult(
            Classification.KEEP,
            "has a code/config reference or recent runtime evidence",
        )

    if path.startswith(CORE_PREFIXES) or path in {
        ".gitignore",
        "README.md",
        "package.json",
        "package-lock.json",
        "requirements.txt",
    }:
        return ClassificationResult(
            Classification.KEEP,
            "belongs to a current application, domain, configuration or documentation path",
        )

    if tracked:
        return ClassificationResult(
            Classification.KEEP,
            "tracked asset retained by default until a stronger removal signal exists",
        )

    return ClassificationResult(
        Classification.DELETE_CANDIDATE,
        "untracked and without a current reference or runtime signal; manual review required",
    )


def _run_git(root: Path, args: list[str], timeout: int = 120) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def load_tracked_paths(root: Path) -> set[str]:
    output = _run_git(root, ["ls-files", "-z"])
    return {normalize_path(item) for item in output.split("\0") if item}


def load_latest_git_changes(root: Path) -> dict[str, str]:
    """Read history once and keep the newest timestamp seen for each path."""

    output = _run_git(root, ["log", "--format=@@%cI", "--name-only", "--no-renames"])
    latest: dict[str, str] = {}
    current_time = ""
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("@@"):
            current_time = line[2:]
        elif line and current_time:
            latest.setdefault(normalize_path(line), current_time)
    return latest


def load_runtime_evidence(
    log_path: Path | None,
    *,
    now: datetime | None = None,
    days: int = 30,
) -> dict[str, dict[str, Any]]:
    if not log_path or not log_path.exists():
        return {}

    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    evidence: dict[str, dict[str, Any]] = {}
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                continue
            script = str(row.get("script") or "").strip()
            if not script:
                continue
            parsed_time = _parse_timestamp(row.get("time"))
            if parsed_time and parsed_time < cutoff:
                continue
            key = PurePosixPath(normalize_path(script)).name
            item = evidence.setdefault(
                key,
                {
                    "run_count": 0,
                    "success_count": 0,
                    "latest_status": None,
                    "latest_time": None,
                },
            )
            item["run_count"] += 1
            if str(row.get("status", "")).lower() == "success":
                item["success_count"] += 1
            timestamp_text = parsed_time.isoformat() if parsed_time else str(row.get("time") or "")
            if not item["latest_time"] or timestamp_text > item["latest_time"]:
                item["latest_time"] = timestamp_text
                item["latest_status"] = row.get("status")
    return evidence


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    candidates = [text, text.replace(" ", "T", 1)]
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def load_baseline_untracked(path: Path | None) -> list[str]:
    if not path or not path.exists():
        return []
    result: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            result.append(normalize_path(value))
    return result


def load_manual_approvals(path: Path | None) -> set[str]:
    """Preserve explicit approvals without allowing them to override a new category."""

    if not path or not path.exists():
        return set()
    approved: set[str] = set()
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for row in csv.DictReader(handle):
                if str(row.get("approved", "")).strip().lower() in {"true", "yes", "1"}:
                    approved.add(normalize_path(row.get("path", "")))
    except OSError:
        return set()
    return approved


def _iter_present_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SCAN_EXCLUDED_PARTS for part in relative.parts):
            continue
        normalized = relative.as_posix()
        if normalized in MANIFEST_OUTPUT_PATHS:
            continue
        yield path


def _read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        if path.stat().st_size > max_bytes or path.suffix.lower() not in TEXT_SUFFIXES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _extract_import_tokens(path: Path, text: str) -> list[str]:
    tokens: set[str] = set()
    if path.suffix.lower() == ".py" and text:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    tokens.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    tokens.add(node.module)
    for match in QUOTED_PATH_RE.finditer(text):
        tokens.add(match.group(1))
    for match in JS_IMPORT_RE.finditer(text):
        tokens.add(match.group(1))
    for match in MARKDOWN_LINK_PATH_RE.finditer(text):
        tokens.add(match.group(1))
    return sorted(tokens)


def _resolve_token(
    source_path: str,
    token: str,
    known_paths: set[str],
    stems: dict[str, list[str]],
) -> list[str]:
    normalized = normalize_path(token)
    suffix = PurePosixPath(normalized).suffix

    if normalized in known_paths:
        return [normalized]

    if normalized.startswith("."):
        base = PurePosixPath(source_path).parent
        candidate = normalize_path(base.joinpath(normalized))
        candidate = str(PurePosixPath(candidate))
        variants = [candidate]
        if not suffix:
            variants.extend(f"{candidate}{ext}" for ext in (".js", ".mjs", ".ts", ".tsx", ".py"))
        return [item for item in variants if item in known_paths]

    module_stem = PurePosixPath(normalized).stem if suffix else normalized.rsplit(".", 1)[-1]
    return stems.get(module_stem, [])


def build_reference_graph(
    root: Path,
    paths: Iterable[str],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    known_paths = set(paths)
    stems: dict[str, list[str]] = defaultdict(list)
    for path in sorted(known_paths):
        stems[PurePosixPath(path).stem].append(path)

    imports: dict[str, list[str]] = {}
    referenced_by: dict[str, set[str]] = defaultdict(set)
    for relative in sorted(known_paths):
        absolute = root / Path(relative)
        if not absolute.is_file():
            imports[relative] = []
            continue
        text = _read_text(absolute)
        tokens = _extract_import_tokens(absolute, text)
        imports[relative] = tokens
        if relative.startswith(AUDIT_REFERENCE_PREFIXES):
            continue
        for token in tokens:
            for target in _resolve_token(relative, token, known_paths, stems):
                if target != relative:
                    referenced_by[target].add(relative)

    return imports, {key: sorted(value) for key, value in referenced_by.items()}


def _stable_fingerprint(files: list[dict[str, Any]]) -> str:
    stable_rows = [
        {
            key: row[key]
            for key in (
                "path",
                "present",
                "tracked",
                "size",
                "category",
                "approved",
                "rationale",
                "imports",
                "referenced_by",
                "last_git_change",
                "runtime_evidence",
            )
        }
        for row in files
    ]
    payload = json.dumps(stable_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_inventory(
    root: Path,
    *,
    tracked_paths: set[str] | None = None,
    git_changes: dict[str, str] | None = None,
    runtime_evidence: dict[str, dict[str, Any]] | None = None,
    baseline_untracked: list[str] | None = None,
    approved_paths: set[str] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    tracked_paths = tracked_paths if tracked_paths is not None else load_tracked_paths(root)
    git_changes = git_changes if git_changes is not None else load_latest_git_changes(root)
    runtime_evidence = runtime_evidence or {}
    baseline_untracked = baseline_untracked or []
    approved_paths = approved_paths or set()

    present_paths = {path.relative_to(root).as_posix() for path in _iter_present_files(root)}
    all_paths = (present_paths | tracked_paths | set(baseline_untracked)) - MANIFEST_OUTPUT_PATHS
    all_paths.add("config/ifind_refresh_token.txt")
    imports, referenced_by = build_reference_graph(root, all_paths)

    rows: list[dict[str, Any]] = []
    for relative in sorted(all_paths):
        absolute = root / Path(relative)
        present = absolute.is_file()
        size = absolute.stat().st_size if present else 0
        runtime = runtime_evidence.get(PurePosixPath(relative).name)
        references = referenced_by.get(relative, [])
        result = classify_path(
            relative,
            tracked=relative in tracked_paths,
            size=size,
            reference_count=len(references),
            runtime_evidence=runtime,
        )
        approval_allowed = result.category in {
            Classification.FREEZE,
            Classification.DELETE_CANDIDATE,
        }
        rows.append(
            {
                "path": relative,
                "present": present,
                "tracked": relative in tracked_paths,
                "size": size,
                "category": result.category.value,
                "approved": bool(
                    result.approved
                    or (relative in approved_paths and relative in tracked_paths and approval_allowed)
                ),
                "rationale": result.rationale,
                "imports": imports.get(relative, []),
                "referenced_by": references,
                "last_git_change": git_changes.get(relative),
                "runtime_evidence": runtime,
            }
        )

    category_counts = Counter(row["category"] for row in rows)
    inventory = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": ".",
        "files": rows,
        "summary": {
            "file_count": len(rows),
            "present_count": sum(1 for row in rows if row["present"]),
            "tracked_count": sum(1 for row in rows if row["tracked"]),
            "categories": dict(sorted(category_counts.items())),
            "delete_approved_count": sum(
                1
                for row in rows
                if row["category"] == Classification.DELETE_CANDIDATE.value and row["approved"]
            ),
        },
    }
    inventory["content_fingerprint"] = _stable_fingerprint(rows)
    return inventory


def write_manifests(inventory: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = output_dir / "inventory.json"
    csv_path = output_dir / "classifications.csv"
    inventory_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fields = [
        "path",
        "present",
        "tracked",
        "size",
        "category",
        "approved",
        "reference_count",
        "runtime_success_count",
        "last_git_change",
        "rationale",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in inventory["files"]:
        runtime = row.get("runtime_evidence") or {}
        writer.writerow(
            {
                "path": row["path"],
                "present": str(row["present"]).lower(),
                "tracked": str(row["tracked"]).lower(),
                "size": row["size"],
                "category": row["category"],
                "approved": str(row["approved"]).lower(),
                "reference_count": len(row.get("referenced_by") or []),
                "runtime_success_count": runtime.get("success_count", 0),
                "last_git_change": row.get("last_git_change") or "",
                "rationale": row["rationale"],
            }
        )
    csv_path.write_text(buffer.getvalue(), encoding="utf-8")


def verify_manifest(current: dict[str, Any], inventory_path: Path) -> bool:
    if not inventory_path.exists():
        return False
    try:
        stored = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return stored.get("content_fingerprint") == current.get("content_fingerprint")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--runtime-log", type=Path, default=None)
    parser.add_argument("--baseline-untracked", type=Path, default=None)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--verify-manifest", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    output = (args.output or root / "legacy_manifest").resolve()
    runtime_log = args.runtime_log or root / "10_logs" / "script_runs.jsonl"
    baseline_path = args.baseline_untracked or root / "legacy_manifest" / "untracked-files.txt"

    inventory = build_inventory(
        root,
        runtime_evidence=load_runtime_evidence(runtime_log),
        baseline_untracked=load_baseline_untracked(baseline_path),
        approved_paths=load_manual_approvals(output / "classifications.csv"),
    )
    print(json.dumps(inventory["summary"], ensure_ascii=False, sort_keys=True))

    if args.verify_manifest:
        return 0 if verify_manifest(inventory, output / "inventory.json") else 1
    if not args.check_only:
        write_manifests(inventory, output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
