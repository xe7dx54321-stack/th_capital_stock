#!/usr/bin/env python3
"""Safe output helper for Windows GBK terminal Unicode issues."""

import json
import sys


_SAFE_MODE = False


def enable_safe_output() -> None:
    global _SAFE_MODE
    _SAFE_MODE = True
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass


def safe_print_json(data: object, indent: int = 2) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=indent, default=str)
    try:
        print(text)
    except UnicodeEncodeError:
        print(
            json.dumps(data, ensure_ascii=True, indent=indent, default=str)
        )


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="backslashreplace").decode("ascii"))
