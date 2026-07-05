#!/usr/bin/env python3
import re
from pathlib import Path

SUBMIT_SCRIPT = Path("/Users/apple/Documents/同行资本内容部门/内容生产系统/09_runbooks/scripts/market_wechat_publish_submit.py")

text = SUBMIT_SCRIPT.read_text(encoding="utf-8")
original = text

# Patch: Add retry logic to request_json_call
old_func = '''def request_json_call(url: str, payload: dict[str, Any] | None = None, method: str = "GET", timeout: int = 20) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, method=method.upper())
    if body is not None:
        request.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        response_body = exc.read().decode("utf-8", "ignore")
        raise RuntimeError(f"HTTP {exc.code}: {response_body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc'''

new_func = '''def request_json_call(url: str, payload: dict[str, Any] | None = None, method: str = "GET", timeout: int = 20, _retries: int = 3) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, method=method.upper())
    if body is not None:
        request.add_header("Content-Type", "application/json; charset=utf-8")
    last_exc: Exception | None = None
    for attempt in range(_retries):
        try:
            with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", "ignore")
            last_exc = RuntimeError(f"HTTP {exc.code}: {response_body}")
            if exc.code >= 500 and attempt < _retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise last_exc from exc
        except URLError as exc:
            last_exc = RuntimeError(f"Network error: {exc}")
            if attempt < _retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise last_exc from exc
    raise last_exc or RuntimeError("request_json_call failed after retries")'''

text = text.replace(old_func, new_func)

if text != original:
    SUBMIT_SCRIPT.write_text(text, encoding="utf-8")
    print(f"Patched {SUBMIT_SCRIPT}")
    print("Changes: Added retry logic (3 attempts with exponential backoff) to request_json_call")
else:
    print("No changes needed (pattern not found)")
