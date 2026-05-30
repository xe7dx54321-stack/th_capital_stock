#!/usr/bin/env python3
"""Phase 71: Fallback text normalizer."""
from typing import Any

def normalize_fallback_text(text: str, source_type: str) -> dict[str, Any]:
    """Normalize fallback text: clean HTML, trim, check quality."""
    if not text or len(text) < 50:
        return {"text": "", "normalized": False, "reason": "text_too_short", "usable": False}

    # Basic HTML cleanup
    import re
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"&[a-z]+;", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    usable = len(cleaned) >= 100
    return {"text": cleaned, "normalized": True, "length": len(cleaned), "usable": usable, "source_type": source_type, "quality_hint": "management_commentary" if source_type == "irm" else "business_context"}
