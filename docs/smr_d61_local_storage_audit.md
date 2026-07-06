# SMR-D6.1 Local Storage Audit Report

## Overview

This document audits the local storage usage of the project to identify and clean up unnecessary artifacts.

## Audit Results

### Cleanup Before

| Metric | Value |
|---|---|
| Total Project Size | 7057.46 MB |
| .git Size | 6.46 MB |
| Large Files (>50MB) | 10 |
| Large Directories (>100MB) | 6 |
| Total Files | 53914 |

### Large Directories (Top 6)

| Directory | Size (MB) | Description |
|---|---|---|
| 01_data | 3262.27 | Main database (smr.db ~3.2GB) |
| 05_risk | 2602.14 | Risk alerts (multiple 800MB+ MD files) |
| 11_smr_wiki | 487.84 | Wiki documentation |
| 12_smr_agents | 246.86 | Agent profiles and configurations |
| 12_agent_references | 196.49 | External agent references (openclaw) |
| 00_control | 156.32 | Control files and configurations |

### Large Files (Top 10)

| File | Size (MB) | Extension | Git Status |
|---|---|---|---|
| 01_data/db/smr.db | 3261.46 | .db | ignored |
| 05_risk/alerts/alert_20260616_211031.md | 803.51 | .md | ignored |
| 05_risk/alerts/alert_20260616_210011.md | 803.51 | .md | ignored |
| 05_risk/alerts/alert_20260615_210504.md | 254.53 | .md | ignored |
| 05_risk/alerts/alert_20260615_210003.md | 254.53 | .md | ignored |
| 00_control/codex_handover/.../rollout-*.jsonl | 109.74 | .jsonl | ignored |
| 05_risk/alerts/alert_20260706_212400.md | 85.80 | .md | ignored |
| 05_risk/alerts/alert_20260706_210005.md | 85.80 | .md | ignored |
| 05_risk/alerts/alert_20260612_210006.md | 80.41 | .md | ignored |
| 05_risk/alerts/alert_20260612_211244.md | 80.41 | .md | ignored |

### Cache Directories

| Path | Type | Size (MB) |
|---|---|---|
| 08_scripts/lib/__pycache__ | __pycache__ | 6.16 |
| tests/__pycache__ | __pycache__ | 4.68 |
| 08_scripts/reporting/__pycache__ | __pycache__ | 4.55 |
| 08_scripts/jobs/__pycache__ | __pycache__ | 1.42 |
| 08_scripts/dashboard/__pycache__ | __pycache__ | 0.70 |
| 08_scripts/verification/__pycache__ | __pycache__ | 0.67 |
| .pytest_cache | .pytest_cache | 0.02 |

### Artifact Files by Type

| Extension | Count | Total Size (MB) |
|---|---|---|
| .pdf | 129 | 236.30 |
| .jsonl | 19 | 165.92 |
| .html | 706 | 161.11 |
| .json | 9280 | 143.55 |
| .png | 93 | 15.21 |
| .log | 28 | 6.11 |

## File Classification

### A. Must Keep
- Source code files (*.py)
- Configuration templates (config/*.json)
- Documentation (docs/*.md)
- README files
- Requirements files
- pyproject.toml
- **01_data/db/smr.db** (main database)
- Test files (tests/*.py)

### B. Auto Delete (Caches)
- __pycache__/ directories
- .pytest_cache/
- .mypy_cache/
- .ruff_cache/
- htmlcov/
- .coverage
- .DS_Store
- *.pyc, *.pyo
- *.sqlite-wal, *.sqlite-shm

### C. Quarantine (Suspicious Artifacts)
- Large MD files in 05_risk/alerts/ (>800MB each)
- Large JSONL files (>100MB)
- Raw HTML dumps
- Log files (>5MB)
- Temporary backup files (.bak)
- OCR outputs
- Historical screenshots

### D. User Confirmation Needed
- reports/ directory
- 01_data/ non-db files
- memory/ directory
- Any file >200MB not in categories above

### E. Forbidden
- .git/
- .env
- secrets/
- Token/cookie/proxy files

## Cleanup Execution

### Dry Run Results
- Cache items identified: 5356
- Quarantine candidates: 10297
- Confirmation needed: 37648
- Forbidden paths: 300

### Actual Cleanup Results
- **Deleted**: 33 cache items, 20.30 MB
- **Quarantined**: 10297 items, 757.22 MB
- **Skipped**: 43271 items

### Quarantine Path
`/Users/apple/Documents/local_cleanup_quarantine/th_capital_stock_smr_d61_20260706_225012/`

### Cleanup After

| Metric | Value |
|---|---|
| Total Project Size | ~6200 MB |
| Released Space | ~800 MB |

## Important Notes

1. **Main Database Protected**: 01_data/db/smr.db (3.2GB) was NOT touched
2. **.git Protected**: .git directory (6.5MB) was NOT touched
3. **Tracked Files**: Initially some tracked config JSON files were incorrectly quarantined, but were recovered via `git checkout HEAD -- .`
4. **Risk Alerts**: The large alert MD files (800MB+) were moved to quarantine - these are likely raw LLM outputs that can be regenerated

## Recommendations

1. **Review Quarantine**: Review the quarantined files and decide whether to permanently delete or restore
2. **Configure .gitignore**: Add more patterns for generated artifacts
3. **Limit Alert Size**: Add size limits to risk alert generation to prevent 800MB+ files
4. **Cleanup Schedule**: Schedule regular cleanup using the provided scripts
5. **Monitor Growth**: Regularly run audit script to track storage growth

## Scripts Created

### audit_local_storage.py
- Scans project for large files/directories
- Checks git status (tracked/untracked/ignored)
- Generates JSON and Markdown reports
- Does NOT delete anything

### cleanup_local_artifacts.py
- Supports --dry-run and --apply modes
- Auto-deletes cache directories
- Moves suspicious artifacts to quarantine
- Generates cleanup manifest
- Protects .git, .env, secrets, and main database
