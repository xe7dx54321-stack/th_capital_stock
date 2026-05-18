#!/usr/bin/env python3
"""Shared path helpers for locating the SMR project across machines."""

import os
from functools import lru_cache
from pathlib import Path


LEGACY_ROOT_HINTS = [
    Path("/Users/apple/Documents/同行资本二级市场"),
]


@lru_cache(maxsize=1)
def project_root():
    env_root = os.environ.get("SMR_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


ROOT = project_root()


def project_path(*parts):
    return ROOT.joinpath(*parts)


def env_or_project_path(env_name, *default_parts):
    env_value = os.environ.get(env_name)
    if env_value:
        return normalize_project_path(env_value)
    return project_path(*default_parts)


def normalize_project_path(path_value):
    if path_value in (None, ""):
        return None

    path = Path(str(path_value)).expanduser()
    if not path.is_absolute():
        return (ROOT / path).resolve(strict=False)

    for base in (ROOT, *LEGACY_ROOT_HINTS):
        try:
            relative = path.relative_to(base)
            return (ROOT / relative).resolve(strict=False)
        except ValueError:
            continue

    return path.resolve(strict=False)


def relative_to_project(path_value):
    normalized = normalize_project_path(path_value)
    if normalized is None:
        return None
    try:
        return str(normalized.relative_to(ROOT))
    except ValueError:
        return str(normalized)
