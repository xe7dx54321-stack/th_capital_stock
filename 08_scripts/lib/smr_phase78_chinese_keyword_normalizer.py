#!/usr/bin/env python3
import unicodedata, re

def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text or "")
    result = []
    for ch in text:
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E and code != 0xFF0D:
            result.append(chr(code - 0xFEE0))
        elif 0x3000 == code:
            result.append(" ")
        elif ch in "()<>[]{}/|":
            result.append(ch)
        else:
            result.append(ch)
    text = "".join(result)
    text = re.sub(r"[\u2000-\u200F\u2028-\u202F\u205F\u2060\uFEFF]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def casefold_english(text):
    return text.casefold() if text else ""

def extract_context_window(text, keyword, window_chars=80):
    if not text or not keyword:
        return ""
    idx = text.find(keyword)
    if idx < 0:
        idx = casefold_english(text).find(casefold_english(keyword))
    if idx < 0:
        return ""
    start = max(0, idx - window_chars)
    end = min(len(text), idx + len(keyword) + window_chars)
    return text[start:end]

def match_with_negatives(text, keywords, negative_keywords=None):
    if not text or not keywords:
        return []
    normalized = normalize_text(text)
    cf = casefold_english(normalized)
    hits = []
    for kw in keywords:
        kw_norm = normalize_text(kw)
        kw_cf = casefold_english(kw_norm)
        if kw_cf in cf:
            if negative_keywords:
                neg_hit = False
                for nk in negative_keywords:
                    if casefold_english(normalize_text(nk)) in cf:
                        neg_hit = True
                        break
                if neg_hit:
                    continue
            context = extract_context_window(normalized, kw_norm)
            hits.append({"keyword": kw, "matched": True, "context_window": context[:200]})
    return hits

def build_normalizer_report():
    return {
        "phase78_chinese_keyword_normalizer": {
            "capabilities": [
                "unicode_normalization",
                "full_width_to_half_width",
                "chinese_punctuation_cleanup",
                "casefold",
                "context_window_extraction",
                "negative_keyword_exclusion"
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
