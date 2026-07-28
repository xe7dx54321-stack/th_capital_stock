from __future__ import annotations

import json
import http.client
import os
import re
import time
import urllib.parse
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from zoneinfo import ZoneInfo

from smr_app.acquisition.contracts import (
    AcquisitionBatch,
    AcquisitionRequest,
    AuthorityTier,
    EvidenceCandidate,
    NormalizedFact,
    SourceDocument,
    utc_now,
)


SHANGHAI = ZoneInfo("Asia/Shanghai")
SZSE_QUOTE_URL = "https://www.szse.cn/api/market/ssjjhq/getTimeData"
SZSE_HISTORY_URL = "https://www.szse.cn/api/market/ssjjhq/getHistoryData"
TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q="
TENCENT_HISTORY_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
EASTMONEY_QUOTE_URL = "https://push2.eastmoney.com/api/qt/stock/get"
BAIDU_VALUATION_URL = "https://gushitong.baidu.com/opendata"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PEER_CONFIG = PROJECT_ROOT / "config" / "peer_sets.json"
PARSER_VERSION = "a-share-market-v1"

A_SHARE_HOLIDAYS_2026 = frozenset({
    "2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20",
    "2026-04-06", "2026-05-01", "2026-06-19", "2026-09-25",
    "2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06", "2026-10-07",
})


def _float(value: Any) -> float | None:
    if value in (None, "", "-") or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _require_float(value: Any, field: str) -> float:
    parsed = _float(value)
    if parsed is None:
        raise ValueError(f"market response missing numeric field {field}")
    return parsed


def _compact_quote_time(value: str) -> str:
    raw = str(value or "").strip()
    if re.fullmatch(r"\d{14}", raw):
        parsed = datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=SHANGHAI)
    else:
        parsed = datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=SHANGHAI)
    return parsed.isoformat()


def _is_a_share_trading_day(value: date) -> bool:
    return value.weekday() < 5 and value.isoformat() not in A_SHARE_HOLIDAYS_2026


def _previous_trading_day(value: date, *, include_same: bool = True) -> date:
    cursor = value if include_same else value - timedelta(days=1)
    for _ in range(370):
        if _is_a_share_trading_day(cursor):
            return cursor
        cursor -= timedelta(days=1)
    raise RuntimeError("could not resolve previous A-share trading day")


def expected_completed_a_share_session(now: datetime) -> str:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    local = now.astimezone(SHANGHAI)
    anchor = local.date() if local.hour >= 18 else local.date() - timedelta(days=1)
    return _previous_trading_day(anchor).isoformat()


def _market_session_status(now: datetime) -> str:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    local = now.astimezone(SHANGHAI)
    if not _is_a_share_trading_day(local.date()):
        return "closed"
    minutes = local.hour * 60 + local.minute
    if minutes < 9 * 60 + 15:
        return "preopen"
    if minutes < 11 * 60 + 30:
        return "open"
    if minutes < 13 * 60:
        return "midday_break"
    if minutes < 15 * 60:
        return "open"
    if local.hour < 18:
        return "settling"
    return "closed"


def _tencent_code(ticker: str) -> str:
    code, suffix = ticker.upper().split(".", 1)
    prefix = "sh" if suffix == "SH" else "bj" if suffix == "BJ" else "sz"
    return prefix + code


def _eastmoney_secid(ticker: str) -> str:
    code, suffix = ticker.upper().split(".", 1)
    prefix = "1" if suffix == "SH" else "0"
    return f"{prefix}.{code}"


class MarketTransport(Protocol):
    def szse_quote(self, code: str) -> Mapping[str, Any]: ...
    def szse_history(self, code: str) -> Mapping[str, Any]: ...
    def tencent_quote(self, ticker: str) -> str: ...
    def tencent_history(self, ticker: str) -> Mapping[str, Any]: ...
    def eastmoney_quote(self, ticker: str) -> Mapping[str, Any]: ...
    def eastmoney_quotes(self, tickers: list[str]) -> Mapping[str, Any]: ...
    def baidu_valuation(self, ticker: str, indicator: str) -> Mapping[str, Any]: ...


class UrllibMarketTransport:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://www.szse.cn/market/product/stock/list/index.html",
    }

    def __init__(self, *, timeout_seconds: int = 20, retry_delays: tuple[float, ...] = (0.0, 0.5, 1.5)) -> None:
        self.timeout_seconds = timeout_seconds
        self.retry_delays = retry_delays

    def _get_bytes(self, url: str, *, referer: str | None = None) -> bytes:
        headers = dict(self.headers)
        if referer:
            headers["Referer"] = referer
        last_error: Exception | None = None
        for attempt, delay in enumerate(self.retry_delays, start=1):
            if delay:
                time.sleep(delay)
            request = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    if response.status != 200:
                        raise RuntimeError(f"market endpoint returned HTTP {response.status}: {url}")
                    return response.read()
            except (urllib.error.URLError, http.client.RemoteDisconnected, TimeoutError, ConnectionResetError) as exc:
                last_error = exc
                if attempt >= len(self.retry_delays):
                    break
        raise RuntimeError(
            f"market endpoint failed after {len(self.retry_delays)} attempts: {url}; "
            f"{type(last_error).__name__}: {last_error}"
        ) from last_error

    def _get_json(self, url: str, *, referer: str | None = None) -> Mapping[str, Any]:
        return json.loads(self._get_bytes(url, referer=referer).decode("utf-8", errors="strict"))

    def szse_quote(self, code: str) -> Mapping[str, Any]:
        query = urllib.parse.urlencode({"marketId": "1", "code": code})
        return self._get_json(f"{SZSE_QUOTE_URL}?{query}")

    def szse_history(self, code: str) -> Mapping[str, Any]:
        query = urllib.parse.urlencode({"marketId": "1", "code": code, "cycleType": "32"})
        return self._get_json(f"{SZSE_HISTORY_URL}?{query}")

    def tencent_quote(self, ticker: str) -> str:
        raw = self._get_bytes(TENCENT_QUOTE_URL + _tencent_code(ticker), referer="https://gu.qq.com/")
        return raw.decode("gb18030", errors="replace")

    def tencent_history(self, ticker: str) -> Mapping[str, Any]:
        params = f"{_tencent_code(ticker)},day,,,260,qfq"
        query = urllib.parse.urlencode({"param": params})
        return self._get_json(f"{TENCENT_HISTORY_URL}?{query}", referer="https://gu.qq.com/")

    def eastmoney_quote(self, ticker: str) -> Mapping[str, Any]:
        fields = "f43,f44,f45,f46,f47,f48,f57,f58,f60,f116,f117,f162,f167,f168"
        query = urllib.parse.urlencode({"secid": _eastmoney_secid(ticker), "fields": fields})
        return self._get_json(f"{EASTMONEY_QUOTE_URL}?{query}", referer="https://quote.eastmoney.com/")

    def eastmoney_quotes(self, tickers: list[str]) -> Mapping[str, Any]:
        fields = "f2,f3,f5,f6,f8,f9,f12,f14,f15,f16,f17,f18,f20,f21,f23"
        query = urllib.parse.urlencode({
            "fltt": "2", "invt": "2",
            "secids": ",".join(_eastmoney_secid(ticker) for ticker in tickers),
            "fields": fields,
        })
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get?" + query
        return self._get_json(url, referer="https://quote.eastmoney.com/")

    def baidu_valuation(self, ticker: str, indicator: str) -> Mapping[str, Any]:
        query = urllib.parse.urlencode({
            "openapi": "1", "dspName": "iphone", "tn": "tangram", "client": "app",
            "query": indicator, "code": ticker.split(".", 1)[0], "word": "",
            "resource_id": "51171", "market": "ab", "tag": indicator,
            "chart_select": "近一年", "industry_select": "", "skip_industry": "1",
            "finClientType": "pc",
        })
        return self._get_json(
            f"{BAIDU_VALUATION_URL}?{query}",
            referer=f"https://gushitong.baidu.com/stock/ab-{ticker.split('.', 1)[0]}",
        )


def parse_szse_quote(payload: Mapping[str, Any], ticker: str) -> dict[str, Any]:
    data = dict(payload.get("data") or {})
    code = ticker.split(".", 1)[0]
    if str(payload.get("code")) != "0" or str(data.get("code")) != code:
        raise ValueError(f"SZSE quote response does not match {ticker}")
    quote_time = _compact_quote_time(str(data.get("marketTime") or ""))
    reported_volume = _require_float(data.get("volume"), "volume")
    minute_volume = sum(
        value for row in data.get("picupdata") or []
        if len(row) > 5 and (value := _float(row[5])) is not None and value >= 0
    )
    volume = reported_volume
    volume_source = "top_level"
    if minute_volume > 0 and _relative_difference(reported_volume, minute_volume) > 0.10:
        volume = minute_volume
        volume_source = "minute_rows_sum"
    return {
        "ticker": ticker,
        "company_name": str(data.get("name") or ticker),
        "price": _require_float(data.get("now"), "now"),
        "previous_close": _require_float(data.get("close"), "close"),
        "open": _require_float(data.get("open"), "open"),
        "high": _require_float(data.get("high"), "high"),
        "low": _require_float(data.get("low"), "low"),
        "volume_lots": volume,
        "volume_source": volume_source,
        "amount_cny": _require_float(data.get("amount"), "amount"),
        "change_percent": _float(data.get("deltaPercent")),
        "quote_time": quote_time,
        "currency": "CNY",
    }


def parse_tencent_quote(raw_text: str, ticker: str) -> dict[str, Any]:
    match = re.search(r'=\s*"(?P<body>.*?)"\s*;?\s*$', raw_text.strip(), re.S)
    if not match:
        raise ValueError("Tencent quote response has an unexpected envelope")
    parts = match.group("body").split("~")
    if len(parts) < 53 or parts[2] != ticker.split(".", 1)[0]:
        raise ValueError(f"Tencent quote response does not match {ticker}")
    quote_time = _compact_quote_time(parts[30])
    result = {
        "ticker": ticker,
        "company_name": parts[1] or ticker,
        "price": _require_float(parts[3], "price"),
        "previous_close": _require_float(parts[4], "previous_close"),
        "open": _require_float(parts[5], "open"),
        "high": _require_float(parts[33], "high"),
        "low": _require_float(parts[34], "low"),
        "volume_lots": _require_float(parts[36] or parts[6], "volume"),
        "amount_cny": _require_float(parts[37], "amount_10k_cny") * 10_000,
        "turnover_rate": _float(parts[38]),
        # 39 与百度“市盈率(TTM)”历史序列按股价同比例变动；52 是预测/动态口径，不能冒充 TTM。
        "pe_ttm": _float(parts[39]),
        "float_market_cap_cny": _require_float(parts[44], "float_market_cap_100m_cny") * 100_000_000,
        "market_cap_cny": _require_float(parts[45], "market_cap_100m_cny") * 100_000_000,
        "pb_mrq": _float(parts[46]),
        "pe_forward": _float(parts[52]),
        "pe_lyr": _float(parts[53]) if len(parts) > 53 else None,
        "change_percent": _float(parts[32]),
        "quote_time": quote_time,
        "currency": "CNY",
    }
    return {key: value for key, value in result.items() if value is not None}


def parse_eastmoney_quote(payload: Mapping[str, Any], ticker: str, quote_time: str) -> dict[str, Any]:
    data = dict(payload.get("data") or {})
    if str(data.get("f57")) != ticker.split(".", 1)[0]:
        raise ValueError(f"Eastmoney quote response does not match {ticker}")
    result = {
        "ticker": ticker,
        "company_name": str(data.get("f58") or ticker),
        "price": _require_float(data.get("f43"), "f43") / 100,
        "high": _require_float(data.get("f44"), "f44") / 100,
        "low": _require_float(data.get("f45"), "f45") / 100,
        "open": _require_float(data.get("f46"), "f46") / 100,
        "volume_lots": _require_float(data.get("f47"), "f47"),
        "amount_cny": _require_float(data.get("f48"), "f48"),
        "previous_close": _require_float(data.get("f60"), "f60") / 100,
        "market_cap_cny": _require_float(data.get("f116"), "f116"),
        "float_market_cap_cny": _require_float(data.get("f117"), "f117"),
        "pe_ttm": _float(data.get("f162")) / 100 if _float(data.get("f162")) is not None else None,
        "pb_mrq": _float(data.get("f167")) / 100 if _float(data.get("f167")) is not None else None,
        "turnover_rate": _float(data.get("f168")) / 100 if _float(data.get("f168")) is not None else None,
        "quote_time": quote_time,
        "currency": "CNY",
    }
    return {key: value for key, value in result.items() if value is not None}


def parse_eastmoney_batch_quote(payload: Mapping[str, Any], ticker: str, quote_time: str) -> dict[str, Any]:
    code = ticker.split(".", 1)[0]
    row = next((dict(item) for item in (payload.get("data") or {}).get("diff") or [] if str(item.get("f12")) == code), None)
    if row is None:
        raise ValueError(f"Eastmoney batch quote response does not contain {ticker}")
    result = {
        "ticker": ticker,
        "company_name": str(row.get("f14") or ticker),
        "price": _require_float(row.get("f2"), "f2"),
        "change_percent": _float(row.get("f3")),
        "volume_lots": _require_float(row.get("f5"), "f5"),
        "amount_cny": _require_float(row.get("f6"), "f6"),
        "turnover_rate": _float(row.get("f8")),
        "pe_ttm": _float(row.get("f9")),
        "high": _require_float(row.get("f15"), "f15"),
        "low": _require_float(row.get("f16"), "f16"),
        "open": _require_float(row.get("f17"), "f17"),
        "previous_close": _require_float(row.get("f18"), "f18"),
        "market_cap_cny": _require_float(row.get("f20"), "f20"),
        "float_market_cap_cny": _require_float(row.get("f21"), "f21"),
        "pb_mrq": _float(row.get("f23")),
        "quote_time": quote_time,
        "currency": "CNY",
    }
    return {key: value for key, value in result.items() if value is not None}


def parse_baidu_valuation(payload: Mapping[str, Any], ticker: str, indicator: str) -> dict[str, Any]:
    try:
        chart = payload["Result"][0]["DisplayData"]["resultData"]["tplData"]["result"]["chartInfo"][0]
        rows = list(chart["body"])
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Baidu valuation response has an unexpected envelope for {ticker} {indicator}") from exc
    parsed = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        try:
            row_date = date.fromisoformat(str(row[0])[:10])
        except ValueError:
            continue
        value = _float(row[1])
        if value is not None:
            parsed.append((row_date, value))
    if not parsed:
        raise ValueError(f"Baidu valuation response contains no usable values for {ticker} {indicator}")
    latest_date, latest_value = max(parsed, key=lambda item: item[0])
    return {
        "ticker": ticker,
        "indicator": indicator,
        "date": latest_date.isoformat(),
        "value": latest_value,
        "unit": str(chart.get("unit") or ""),
    }


def _load_baidu_valuation_set(transport: MarketTransport, ticker: str) -> tuple[dict[str, float | str], dict[str, Any]]:
    raw = {}
    parsed = {}
    for indicator, field in (("总市值", "market_cap_100m_cny"), ("市盈率(TTM)", "pe_ttm"), ("市净率", "pb_mrq")):
        payload = transport.baidu_valuation(ticker, indicator)
        item = parse_baidu_valuation(payload, ticker, indicator)
        raw[indicator] = payload
        parsed[field] = item["value"]
        parsed.setdefault("source_date", item["date"])
        if parsed["source_date"] != item["date"]:
            raise ValueError(f"Baidu valuation dates are inconsistent for {ticker}")
    return parsed, raw


def _validate_valuation_sources(
    *, ticker: str, official: Mapping[str, Any], tencent: Mapping[str, Any], baidu: Mapping[str, Any],
    soft_fields: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    if _relative_difference(float(official["price"]), float(tencent["price"])) > 0.005:
        raise ValueError(f"cross-source price disagreement for {ticker}: official={official['price']}, tencent={tencent['price']}")
    quote_date = datetime.fromisoformat(str(tencent["quote_time"])).date()
    source_date = date.fromisoformat(str(baidu["source_date"]))
    if source_date == quote_date:
        price_scale = 1.0
    elif source_date == _previous_trading_day(quote_date, include_same=False):
        price_scale = float(tencent["price"]) / float(tencent["previous_close"])
    else:
        raise ValueError(
            f"Baidu valuation is too stale for {ticker}: source_date={source_date}, quote_date={quote_date}"
        )
    adjusted = {
        "market_cap_cny": float(baidu["market_cap_100m_cny"]) * 100_000_000 * price_scale,
        "pe_ttm": float(baidu["pe_ttm"]) * price_scale,
        "pb_mrq": float(baidu["pb_mrq"]) * price_scale,
    }
    differences = {}
    for field, tolerance in (("market_cap_cny", 0.02), ("pe_ttm", 0.03), ("pb_mrq", 0.06)):
        left, right = tencent.get(field), adjusted[field]
        difference = None if left is None else _relative_difference(float(left), right)
        if difference is None or difference > tolerance:
            if field in soft_fields:
                differences[field] = {"tencent": left, "baidu_adjusted": right, "relative_difference": difference}
                continue
            raise ValueError(f"cross-source {field} disagreement for {ticker}: tencent={left}, baidu_adjusted={right}")
    return {
        "baidu_source_date": source_date.isoformat(),
        "price_scale": price_scale,
        "adjusted_baidu": adjusted,
        "soft_disagreements": differences,
    }


def _relative_difference(left: float, right: float) -> float:
    return abs(left - right) / max(abs(left), abs(right), 1e-12)


def _fact(
    *, ticker: str, data_type: str, field_name: str, value: Any, unit: str | None,
    as_of: str, document: SourceDocument, authority: AuthorityTier, metadata: Mapping[str, Any] | None = None,
) -> NormalizedFact:
    return NormalizedFact.build(
        entity_key=ticker,
        data_type=data_type,
        field_name=field_name,
        value=value,
        unit=unit,
        as_of=as_of,
        source_document_id=document.document_id,
        authority_tier=authority,
        confidence=0.99 if authority is AuthorityTier.OFFICIAL else 0.95,
        metadata=dict(metadata or {}),
    )


def _daily_bar_facts(
    ticker: str, rows: list[dict[str, Any]], document: SourceDocument, authority: AuthorityTier,
) -> tuple[NormalizedFact, ...]:
    units = {
        "trade_date": "ISO-8601-date", "open": "CNY/share", "high": "CNY/share",
        "low": "CNY/share", "close": "CNY/share", "volume": "lot_100_shares", "amount": "CNY",
    }
    return tuple(
        _fact(
            ticker=ticker, data_type="daily_bars", field_name=field_name, value=row[field_name],
            unit=units[field_name], as_of=row["trade_date"], document=document, authority=authority,
            metadata={"bar_status": "completed"},
        )
        for row in rows
        for field_name in units
        if row.get(field_name) is not None
    )


def _szse_history_rows(payload: Mapping[str, Any], ticker: str, completed_through: str) -> list[dict[str, Any]]:
    data = dict(payload.get("data") or {})
    if str(payload.get("code")) != "0" or str(data.get("code") or ticker.split(".", 1)[0]) != ticker.split(".", 1)[0]:
        raise ValueError(f"SZSE history response does not match {ticker}")
    rows = []
    for raw in data.get("picupdata") or []:
        if len(raw) < 9 or str(raw[0]) > completed_through:
            continue
        rows.append({
            "trade_date": str(raw[0]), "open": _require_float(raw[1], "open"),
            "close": _require_float(raw[2], "close"), "low": _require_float(raw[3], "low"),
            "high": _require_float(raw[4], "high"), "volume": _require_float(raw[7], "volume"),
            "amount": _require_float(raw[8], "amount"),
        })
    rows.sort(key=lambda item: item["trade_date"])
    if not rows:
        raise ValueError("SZSE history response contains no completed daily bars")
    return rows


def _tencent_history_rows(payload: Mapping[str, Any], ticker: str, completed_through: str) -> list[dict[str, Any]]:
    key = _tencent_code(ticker)
    data = dict((payload.get("data") or {}).get(key) or {})
    raw_rows = data.get("qfqday") or data.get("day") or []
    rows = []
    for raw in raw_rows:
        if len(raw) < 6 or str(raw[0]) > completed_through:
            continue
        rows.append({
            "trade_date": str(raw[0]), "open": _require_float(raw[1], "open"),
            "close": _require_float(raw[2], "close"), "high": _require_float(raw[3], "high"),
            "low": _require_float(raw[4], "low"), "volume": _require_float(raw[5], "volume"),
            "amount": None,
        })
    rows.sort(key=lambda item: item["trade_date"])
    if not rows:
        raise ValueError("Tencent history response contains no completed daily bars")
    return rows


class SzseMarketProvider:
    provider_id = "szse_market_official"
    priority = 10
    authority_tier = AuthorityTier.OFFICIAL
    data_types = frozenset({"daily_bars", "realtime_quote"})
    markets = frozenset({"A", "CN"})

    def __init__(self, *, transport: MarketTransport | None = None, clock: Callable[[], datetime] = utc_now) -> None:
        self.transport = transport or UrllibMarketTransport()
        self.clock = clock

    def acquire(self, request: AcquisitionRequest) -> AcquisitionBatch:
        ticker = request.requirement.entity_key
        data_type = request.requirement.data_type
        if not ticker.endswith(".SZ"):
            raise ValueError("SZSE market provider only supports Shenzhen-listed securities")
        now = self.clock()
        code = ticker.split(".", 1)[0]
        if data_type == "daily_bars":
            raw = self.transport.szse_history(code)
            through = expected_completed_a_share_session(now)
            rows = _szse_history_rows(raw, ticker, through)
            document = SourceDocument.build(
                source_id=f"szse_market_history:{ticker}", entity_key=ticker, data_type=data_type,
                source_type="official_exchange_daily_bars", authority_tier=AuthorityTier.OFFICIAL,
                title=f"深圳证券交易所 {ticker} 历史日线", fetched_at=now,
                published_at=rows[-1]["trade_date"], source_url=f"{SZSE_HISTORY_URL}?marketId=1&code={code}&cycleType=32",
                raw_payload=raw, parser_version=PARSER_VERSION,
                metadata={"currency": "CNY", "volume_unit": "lot_100_shares", "bar_count": len(rows), "completed_through": through},
            )
            facts = _daily_bar_facts(ticker, rows, document, AuthorityTier.OFFICIAL)
            candidate = EvidenceCandidate.build(
                entity_key=ticker, data_type=data_type, claim_type="official_market_history",
                text=f"深交所日线显示，{ticker} 最近已完成交易日 {rows[-1]['trade_date']} 收盘价为 {rows[-1]['close']:.2f} 元。",
                source_document_ids=(document.document_id,), authority_tier=AuthorityTier.OFFICIAL,
                occurred_at=rows[-1]["trade_date"], usable_for=("research", "analysis"), status="validated",
            )
            present = ("trade_date", "open", "high", "low", "close", "volume")
            return AcquisitionBatch(
                documents=(document,), facts=facts, evidence_candidates=(candidate,), available_through=rows[-1]["trade_date"],
                required_fields_present=present, quality_status="verified", is_complete=set(request.requirement.required_fields).issubset(present),
                metadata={"bar_count": len(rows), "bar_status": "completed"},
            )
        if data_type == "realtime_quote":
            raw = self.transport.szse_quote(code)
            quote = parse_szse_quote(raw, ticker)
            document = SourceDocument.build(
                source_id=f"szse_market_quote:{ticker}", entity_key=ticker, data_type=data_type,
                source_type="official_exchange_realtime_quote", authority_tier=AuthorityTier.OFFICIAL,
                title=f"深圳证券交易所 {ticker} 实时行情", fetched_at=now, published_at=quote["quote_time"],
                source_url=f"{SZSE_QUOTE_URL}?marketId=1&code={code}", raw_payload=raw, parser_version=PARSER_VERSION,
                metadata={"market_session_status": _market_session_status(now), "currency": "CNY"},
            )
            units = {
                "price": "CNY/share", "quote_time": "ISO-8601-datetime", "currency": "ISO-4217",
                "previous_close": "CNY/share", "open": "CNY/share", "high": "CNY/share", "low": "CNY/share",
                "volume_lots": "lot_100_shares", "amount_cny": "CNY", "change_percent": "percent",
            }
            facts = tuple(
                _fact(ticker=ticker, data_type=data_type, field_name=field, value=quote[field], unit=unit,
                      as_of=quote["quote_time"], document=document, authority=AuthorityTier.OFFICIAL)
                for field, unit in units.items() if quote.get(field) is not None
            )
            candidate = EvidenceCandidate.build(
                entity_key=ticker, data_type=data_type, claim_type="official_realtime_quote",
                text=f"深交所行情显示，{ticker} 于 {quote['quote_time']} 报 {quote['price']:.2f} 元。",
                source_document_ids=(document.document_id,), authority_tier=AuthorityTier.OFFICIAL,
                occurred_at=quote["quote_time"], usable_for=("research", "analysis"), status="validated",
            )
            present = ("price", "quote_time", "currency")
            return AcquisitionBatch(
                documents=(document,), facts=facts, evidence_candidates=(candidate,), available_through=quote["quote_time"],
                required_fields_present=present, quality_status="verified", is_complete=True,
                metadata={"market_session_status": _market_session_status(now)},
            )
        raise ValueError("SZSE market provider does not support this requirement")


class TencentMarketProvider:
    provider_id = "tencent_market_fallback"
    priority = 20
    authority_tier = AuthorityTier.REPUTABLE_SECONDARY
    data_types = frozenset({"daily_bars", "realtime_quote"})
    markets = frozenset({"A", "CN"})

    def __init__(self, *, transport: MarketTransport | None = None, clock: Callable[[], datetime] = utc_now) -> None:
        self.transport = transport or UrllibMarketTransport()
        self.clock = clock

    def acquire(self, request: AcquisitionRequest) -> AcquisitionBatch:
        ticker = request.requirement.entity_key
        data_type = request.requirement.data_type
        now = self.clock()
        if data_type == "daily_bars":
            raw = self.transport.tencent_history(ticker)
            through = expected_completed_a_share_session(now)
            rows = _tencent_history_rows(raw, ticker, through)
            document = SourceDocument.build(
                source_id=f"tencent_market_history:{ticker}", entity_key=ticker, data_type=data_type,
                source_type="secondary_market_daily_bars", authority_tier=self.authority_tier,
                title=f"腾讯行情 {ticker} 前复权日线", fetched_at=now, published_at=rows[-1]["trade_date"],
                source_url=f"{TENCENT_HISTORY_URL}?param={_tencent_code(ticker)},day,,,260,qfq",
                raw_payload=raw, parser_version=PARSER_VERSION,
                metadata={"adjustment": "qfq", "currency": "CNY", "bar_count": len(rows), "completed_through": through},
            )
            facts = _daily_bar_facts(ticker, rows, document, self.authority_tier)
            candidate = EvidenceCandidate.build(
                entity_key=ticker, data_type=data_type, claim_type="secondary_market_history",
                text=f"腾讯前复权日线显示，{ticker} 最近已完成交易日 {rows[-1]['trade_date']} 收盘价为 {rows[-1]['close']:.2f} 元。",
                source_document_ids=(document.document_id,), authority_tier=self.authority_tier,
                occurred_at=rows[-1]["trade_date"], usable_for=("research", "analysis"), status="validated",
            )
            present = ("trade_date", "open", "high", "low", "close", "volume")
            return AcquisitionBatch(
                documents=(document,), facts=facts, evidence_candidates=(candidate,), available_through=rows[-1]["trade_date"],
                required_fields_present=present, quality_status="verified", is_complete=set(request.requirement.required_fields).issubset(present),
                metadata={"bar_count": len(rows), "adjustment": "qfq", "fallback": True},
            )
        if data_type == "realtime_quote":
            raw = self.transport.tencent_quote(ticker)
            quote = parse_tencent_quote(raw, ticker)
            document = SourceDocument.build(
                source_id=f"tencent_market_quote:{ticker}", entity_key=ticker, data_type=data_type,
                source_type="secondary_realtime_quote", authority_tier=self.authority_tier,
                title=f"腾讯行情 {ticker} 实时快照", fetched_at=now, published_at=quote["quote_time"],
                source_url=TENCENT_QUOTE_URL + _tencent_code(ticker), raw_text=raw, parser_version=PARSER_VERSION,
                metadata={"market_session_status": _market_session_status(now), "currency": "CNY", "fallback": True},
            )
            units = {"price": "CNY/share", "quote_time": "ISO-8601-datetime", "currency": "ISO-4217"}
            facts = tuple(
                _fact(ticker=ticker, data_type=data_type, field_name=field, value=quote[field], unit=unit,
                      as_of=quote["quote_time"], document=document, authority=self.authority_tier)
                for field, unit in units.items()
            )
            candidate = EvidenceCandidate.build(
                entity_key=ticker, data_type=data_type, claim_type="secondary_realtime_quote",
                text=f"腾讯行情显示，{ticker} 于 {quote['quote_time']} 报 {quote['price']:.2f} 元。",
                source_document_ids=(document.document_id,), authority_tier=self.authority_tier,
                occurred_at=quote["quote_time"], usable_for=("research", "analysis"), status="validated",
            )
            return AcquisitionBatch(
                documents=(document,), facts=facts, evidence_candidates=(candidate,), available_through=quote["quote_time"],
                required_fields_present=tuple(units), quality_status="verified", is_complete=True,
                metadata={"market_session_status": _market_session_status(now), "fallback": True},
            )
        raise ValueError("Tencent market provider does not support this requirement")


class CrossValidatedValuationProvider:
    provider_id = "cross_validated_a_share_valuation"
    priority = 10
    authority_tier = AuthorityTier.REPUTABLE_SECONDARY
    data_types = frozenset({"valuation_snapshot"})
    markets = frozenset({"A", "CN"})

    def __init__(self, *, transport: MarketTransport | None = None, clock: Callable[[], datetime] = utc_now) -> None:
        self.transport = transport or UrllibMarketTransport()
        self.clock = clock

    def acquire(self, request: AcquisitionRequest) -> AcquisitionBatch:
        ticker = request.requirement.entity_key
        now = self.clock()
        tencent_raw = self.transport.tencent_quote(ticker)
        tencent = parse_tencent_quote(tencent_raw, ticker)
        if ticker.endswith(".SZ"):
            price_raw = self.transport.szse_quote(ticker.split(".", 1)[0])
            price_source = parse_szse_quote(price_raw, ticker)
            price_source_error = None
            price_document = SourceDocument.build(
                source_id=f"szse_valuation_price:{ticker}", entity_key=ticker, data_type="valuation_snapshot",
                source_type="official_exchange_realtime_quote", authority_tier=AuthorityTier.OFFICIAL,
                title=f"深圳证券交易所 {ticker} 行情价格", fetched_at=now,
                published_at=price_source["quote_time"],
                source_url=f"{SZSE_QUOTE_URL}?marketId=1&code={ticker.split('.', 1)[0]}",
                raw_payload=price_raw, parser_version=PARSER_VERSION,
                metadata={"field_contract": {"price": "now, CNY/share"}},
            )
            verification_method = "szse_tencent_baidu_cross_validation"
        else:
            try:
                price_raw = self.transport.eastmoney_quote(ticker)
                price_source = parse_eastmoney_quote(price_raw, ticker, tencent["quote_time"])
                price_source_error = None
                price_document = SourceDocument.build(
                    source_id=f"eastmoney_valuation_price:{ticker}", entity_key=ticker,
                    data_type="valuation_snapshot", source_type="secondary_market_quote",
                    authority_tier=self.authority_tier,
                    title=f"东方财富 {ticker} 行情价格交叉校验", fetched_at=now,
                    published_at=price_source["quote_time"],
                    source_url=(
                        f"{EASTMONEY_QUOTE_URL}?"
                        + urllib.parse.urlencode({
                            "secid": _eastmoney_secid(ticker),
                            "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f116,f117,f162,f167,f168",
                        })
                    ),
                    raw_payload=price_raw, parser_version=PARSER_VERSION,
                    metadata={"field_contract": {"price": "f43/100, CNY/share"}},
                )
                verification_method = "eastmoney_tencent_baidu_cross_validation"
            except (OSError, RuntimeError, ValueError, http.client.HTTPException, urllib.error.URLError) as exc:
                # 东方财富对上海标的偶发断连时，不应阻断仍然独立的
                # “腾讯估值快照 × 百度历史估值”交叉校验。
                price_raw = tencent_raw
                price_source = tencent
                price_source_error = f"{type(exc).__name__}: {exc}"
                price_document = SourceDocument.build(
                    source_id=f"tencent_valuation_price_fallback:{ticker}", entity_key=ticker,
                    data_type="valuation_snapshot", source_type="secondary_market_quote",
                    authority_tier=self.authority_tier,
                    title=f"腾讯行情 {ticker} 价格降级来源", fetched_at=now,
                    published_at=tencent["quote_time"],
                    source_url=TENCENT_QUOTE_URL + _tencent_code(ticker),
                    raw_text=tencent_raw, parser_version=PARSER_VERSION,
                    metadata={
                        "field_contract": {"price": "index 3, CNY/share"},
                        "fallback_reason": price_source_error,
                    },
                )
                verification_method = "tencent_price_baidu_valuation_cross_validation"
        baidu, baidu_raw = _load_baidu_valuation_set(self.transport, ticker)
        validation = _validate_valuation_sources(
            ticker=ticker, official=price_source, tencent=tencent, baidu=baidu
        )
        tencent_doc = SourceDocument.build(
            source_id=f"tencent_valuation:{ticker}", entity_key=ticker, data_type="valuation_snapshot",
            source_type="secondary_valuation_quote", authority_tier=self.authority_tier,
            title=f"腾讯行情 {ticker} 估值快照", fetched_at=now, published_at=tencent["quote_time"],
            source_url=TENCENT_QUOTE_URL + _tencent_code(ticker), raw_text=tencent_raw, parser_version=PARSER_VERSION,
            metadata={"field_contract": {"market_cap": "index 45, CNY 100m", "pe_ttm": "index 39", "pb_mrq": "index 46"}},
        )
        baidu_doc = SourceDocument.build(
            source_id=f"baidu_valuation:{ticker}", entity_key=ticker, data_type="valuation_snapshot",
            source_type="secondary_valuation_history", authority_tier=self.authority_tier,
            title=f"百度股市通 {ticker} 历史估值校验", fetched_at=now, published_at=str(baidu["source_date"]),
            source_url=f"https://gushitong.baidu.com/stock/ab-{ticker.split('.', 1)[0]}", raw_payload=baidu_raw,
            parser_version=PARSER_VERSION,
            metadata={
                "field_contract": {"market_cap": "总市值, CNY 100m", "pe_ttm": "市盈率(TTM)", "pb_mrq": "市净率"},
                "price_scale": validation["price_scale"], "adjusted_values": validation["adjusted_baidu"],
            },
        )
        as_of = tencent["quote_time"]
        values = {
            "price": (price_source["price"], "CNY/share"),
            "market_cap": (tencent["market_cap_cny"], "CNY"),
            "pe_ttm": (tencent["pe_ttm"], "multiple"),
            "pb_mrq": (tencent["pb_mrq"], "multiple"),
            "as_of": (as_of, "ISO-8601-datetime"),
        }
        facts = tuple(
            _fact(
                ticker=ticker, data_type="valuation_snapshot", field_name=field, value=value, unit=unit,
                as_of=as_of, document=tencent_doc, authority=self.authority_tier,
                metadata={
                    "verification_method": verification_method,
                    "comparison_tolerance": "field_specific", "baidu_source_date": validation["baidu_source_date"],
                },
            )
            for field, (value, unit) in values.items()
        )
        candidate = EvidenceCandidate.build(
            entity_key=ticker, data_type="valuation_snapshot", claim_type="cross_validated_valuation",
            text=(f"{ticker} 于 {as_of} 的跨源核验估值快照：价格 {price_source['price']:.2f} 元，"
                  f"总市值 {tencent['market_cap_cny'] / 1e8:.2f} 亿元，PE(TTM) {tencent['pe_ttm']:.2f} 倍，"
                  f"PB(MRQ) {tencent['pb_mrq']:.2f} 倍。"),
            source_document_ids=(price_document.document_id, tencent_doc.document_id, baidu_doc.document_id),
            authority_tier=self.authority_tier,
            occurred_at=as_of, usable_for=("research", "analysis"), status="validated",
            metadata={"verification_method": verification_method},
        )
        return AcquisitionBatch(
            documents=(price_document, tencent_doc, baidu_doc), facts=facts,
            evidence_candidates=(candidate,), available_through=as_of,
            required_fields_present=tuple(values), quality_status="cross_validated", is_complete=True,
            metadata={
                "verification_method": verification_method, "currency": "CNY",
                "baidu_source_date": validation["baidu_source_date"],
                "price_source_fallback": price_source_error is not None,
                "price_source_error": price_source_error,
            },
        )


class PeerComparisonProvider:
    provider_id = "configured_peer_comparison"
    priority = 10
    authority_tier = AuthorityTier.REPUTABLE_SECONDARY
    data_types = frozenset({"peer_comparison"})
    markets = frozenset({"A", "CN"})

    def __init__(
        self, *, config_path: str | Path = DEFAULT_PEER_CONFIG, transport: MarketTransport | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.config_path = Path(config_path)
        self.transport = transport or UrllibMarketTransport()
        self.clock = clock

    def acquire(self, request: AcquisitionRequest) -> AcquisitionBatch:
        ticker = request.requirement.entity_key
        registry = json.loads(self.config_path.read_text(encoding="utf-8"))
        configured = dict(registry.get(ticker) or {})
        peers = list(configured.get("peers") or [])
        methodology = str(configured.get("methodology") or "").strip()
        if not peers or not methodology:
            raise ValueError(f"no explainable peer set configured for {ticker}")
        now = self.clock()
        raw_rows = []
        comparable = []
        as_of_values = []
        for peer in peers:
            peer_ticker = str(peer["ticker"]).upper()
            if not peer_ticker.endswith(".SZ"):
                raise ValueError(f"peer {peer_ticker} is outside the currently verified SZSE peer chain")
            official_raw = self.transport.szse_quote(peer_ticker.split(".", 1)[0])
            official = parse_szse_quote(official_raw, peer_ticker)
            tencent_raw = self.transport.tencent_quote(peer_ticker)
            tencent = parse_tencent_quote(tencent_raw, peer_ticker)
            baidu, baidu_raw = _load_baidu_valuation_set(self.transport, peer_ticker)
            validation = _validate_valuation_sources(
                ticker=peer_ticker, official=official, tencent=tencent, baidu=baidu,
                soft_fields=frozenset({"pb_mrq"}),
            )
            as_of_values.append(official["quote_time"])
            flags = []
            if tencent["pe_ttm"] > 300:
                flags.append("pe_outlier_low_earnings_base_not_rankable")
            if tencent["pb_mrq"] > 100:
                flags.append("pb_outlier_not_rankable")
            peer_pb = tencent["pb_mrq"]
            if "pb_mrq" in validation["soft_disagreements"]:
                peer_pb = None
                flags.append("pb_source_disagreement_not_rankable")
            comparable.append({
                "ticker": peer_ticker,
                "company_name": str(peer.get("name") or official["company_name"]),
                "selection_reason": str(peer.get("reason") or methodology),
                "source_quote_time": official["quote_time"],
                "currency": "CNY",
                "price": official["price"],
                "market_cap_cny": tencent["market_cap_cny"],
                "pe_ttm": tencent["pe_ttm"],
                "pb_mrq": peer_pb,
                "baidu_valuation_date": validation["baidu_source_date"],
                "valuation_flags": flags,
            })
            raw_rows.append({
                "ticker": peer_ticker, "official_szse": official_raw,
                "tencent": tencent_raw, "baidu_valuation": baidu_raw,
                "baidu_adjustment": validation,
            })
        parsed_times = [datetime.fromisoformat(value) for value in as_of_values]
        if len({value.date() for value in parsed_times}) != 1:
            raise ValueError(f"peer quote trading dates are inconsistent: {sorted(set(as_of_values))}")
        spread_seconds = (max(parsed_times) - min(parsed_times)).total_seconds()
        if spread_seconds > 120:
            raise ValueError(f"peer quote sampling window exceeded 120 seconds: {spread_seconds:.0f}")
        as_of = max(parsed_times).isoformat()
        for item in comparable:
            item["as_of"] = as_of
        document = SourceDocument.build(
            source_id=f"peer_matrix:{ticker}", entity_key=ticker, data_type="peer_comparison",
            source_type="cross_validated_peer_market_matrix", authority_tier=self.authority_tier,
            title=f"{ticker} 可解释同行比较矩阵", fetched_at=now, published_at=as_of,
            source_url="local-config://config/peer_sets.json", raw_payload={
                "methodology": methodology, "configured_peers": peers, "source_responses": raw_rows,
            }, parser_version=PARSER_VERSION,
            metadata={
                "currency": "CNY", "peer_count": len(comparable),
                "timestamp_policy": "same_trading_date_within_120_seconds", "sampling_spread_seconds": spread_seconds,
            },
        )
        values = {
            "peer_set": ([row["ticker"] for row in comparable], "ticker-list"),
            "selection_reason": (methodology, "text"),
            "comparable_metrics": (comparable, "structured-json"),
            "as_of": (as_of, "ISO-8601-datetime"),
        }
        facts = tuple(
            _fact(ticker=ticker, data_type="peer_comparison", field_name=field, value=value, unit=unit,
                  as_of=as_of, document=document, authority=self.authority_tier,
                  metadata={"verification_method": "official_price_plus_tencent_and_baidu_valuation"})
            for field, (value, unit) in values.items()
        )
        candidate = EvidenceCandidate.build(
            entity_key=ticker, data_type="peer_comparison", claim_type="peer_comparison_matrix",
            text=f"依据“{methodology}”选取 {len(comparable)} 个同行，并在 {as_of} 使用同币种、同时间口径比较价格、总市值、PE(TTM) 与 PB(MRQ)；价格经深交所与腾讯核验，估值经腾讯与百度历史序列核验。",
            source_document_ids=(document.document_id,), authority_tier=self.authority_tier,
            occurred_at=as_of, usable_for=("research", "analysis"), status="validated",
        )
        return AcquisitionBatch(
            documents=(document,), facts=facts, evidence_candidates=(candidate,), available_through=as_of,
            required_fields_present=tuple(values), quality_status="cross_validated", is_complete=True,
            metadata={
                "methodology": methodology, "peer_count": len(comparable), "currency": "CNY",
                "sampling_spread_seconds": spread_seconds,
            },
        )


def default_szse_market_provider() -> SzseMarketProvider:
    return SzseMarketProvider()


def default_tencent_market_provider() -> TencentMarketProvider:
    return TencentMarketProvider()


def default_valuation_provider() -> CrossValidatedValuationProvider:
    return CrossValidatedValuationProvider()


def default_peer_comparison_provider() -> PeerComparisonProvider:
    configured = os.environ.get("SMR_PEER_SET_CONFIG")
    return PeerComparisonProvider(config_path=Path(configured) if configured else DEFAULT_PEER_CONFIG)
