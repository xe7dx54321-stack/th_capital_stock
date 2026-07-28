from __future__ import annotations

import math
import re
from typing import Any


NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?%?")


def _number(token: str) -> float:
    value = token.replace(",", "")
    if value.endswith("%"):
        return float(value[:-1]) / 100
    return float(value)


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}%"


def _change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return current / previous - 1


def _main_metrics_chunk(chunks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        if (
            "主要会计数据和财务指标" in text
            and ("本年比上年增减" in text or "本期比上年同期增减" in text)
        ):
            return chunk
    return None


def _extract_sse_annual_metrics(text: str, chunk: dict[str, Any]) -> dict[str, Any] | None:
    """Parse the column-major annual summary used by Shanghai annual reports.

    PDFMiner emits this table by visual columns rather than by logical rows.
    The layout is stable but differs materially from the Shenzhen row order:
    the first three rows are emitted for every year before the remaining rows,
    while the balance-sheet and per-share blocks each repeat their year header.
    """
    if "本期比上年同期增减" not in text or "利润总额" not in text:
        return None
    start = text.find("近三年主要会计数据和财务指标")
    if start < 0:
        start = text.find("主要会计数据和财务指标")
    end = text.find("报告期末公司前三年", start)
    if start < 0 or end < 0:
        return None
    segment = text[start:end]
    tokens = NUMBER_RE.findall(segment)
    if len(tokens) < 57:
        return None
    years = [token.replace("年", "").strip() for token in tokens[:3]]
    if not all(re.fullmatch(r"20\d{2}", year) for year in years):
        return None
    current, previous, prior = years
    if tokens[21:23] != [current, previous] or tokens[25] != prior:
        return None
    if tokens[34:37] != [current, previous, prior]:
        return None

    values = [_number(token) for token in tokens]
    unit_multiplier = 1.0
    if re.search(r"单位\s*[：:]\s*千元", segment):
        unit_multiplier = 1_000.0
    elif re.search(r"单位\s*[：:]\s*万元", segment):
        unit_multiplier = 10_000.0

    def money(index: int) -> float:
        return values[index] * unit_multiplier

    def ratio(index: int) -> float:
        return values[index] / 100

    roe_change_pp = ratio(50)
    if re.search(rf"减少\s*{re.escape(tokens[50])}\s*个?百分点", segment):
        roe_change_pp = -abs(roe_change_pp)

    metrics = {
        "revenue": {
            current: money(3), previous: money(6), "yoy": ratio(9), prior: money(12),
        },
        "attributable_net_income": {
            current: money(5), previous: money(8), "yoy": ratio(11), prior: money(14),
        },
        "adjusted_net_income": {
            current: money(15), previous: money(16), "yoy": ratio(17), prior: money(18),
        },
        "operating_cash_flow": {
            current: money(19), previous: money(20), "yoy": ratio(23), prior: money(24),
        },
        "attributable_equity": {
            current: money(26), previous: money(28), "yoy": ratio(30), prior: money(32),
        },
        "total_assets": {
            current: money(27), previous: money(29), "yoy": ratio(31), prior: money(33),
        },
        "basic_eps": {
            current: values[37], previous: values[42], "yoy": ratio(47), prior: values[52],
        },
        "diluted_eps": {
            current: values[38], previous: values[43], "yoy": ratio(48), prior: values[53],
        },
        "weighted_roe": {
            current: ratio(40), previous: ratio(45), "change_pp": roe_change_pp, prior: ratio(55),
        },
    }
    return {
        "status": "available",
        "periods": [current, previous, prior],
        "metrics": metrics,
        "evidence_ids": [chunk.get("evidence_id")],
        "source_chunk_id": chunk.get("chunk_id"),
        "table_layout": "sse_column_major",
        "monetary_unit_multiplier": unit_multiplier,
    }


def extract_a_share_annual_metrics(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    chunk = _main_metrics_chunk(chunks)
    if not chunk:
        return {"status": "unavailable", "periods": [], "metrics": {}, "evidence_ids": []}
    text = str(chunk.get("text") or "")
    sse_result = _extract_sse_annual_metrics(text, chunk)
    if sse_result is not None:
        return sse_result
    header = re.search(
        r"(?P<current>20\d{2})\s*年\s*(?P<previous>20\d{2})\s*年\s*本年比上年增减\s*(?P<prior>20\d{2})\s*年",
        text,
        re.S,
    )
    if not header:
        return {"status": "unavailable", "periods": [], "metrics": {}, "evidence_ids": [chunk.get("evidence_id")]}
    tail = text[header.end():]
    boundary = tail.find("公司最近三个")
    if boundary >= 0:
        tail = tail[:boundary]
    tokens = NUMBER_RE.findall(tail)
    if len(tokens) < 32:
        return {"status": "unavailable", "periods": [], "metrics": {}, "evidence_ids": [chunk.get("evidence_id")]}
    values = [_number(token) for token in tokens]
    current, previous, prior = header.group("current"), header.group("previous"), header.group("prior")
    balance_start = 28
    repeated_balance_header = [current, previous, prior]
    for index in range(28, min(len(tokens) - 2, 36)):
        if [token.replace("年", "").strip() for token in tokens[index:index + 3]] == repeated_balance_header:
            balance_start = index + 3
            break
    metrics = {
        "revenue": {current: values[0], previous: values[1], "yoy": values[2], prior: values[3]},
        "attributable_net_income": {current: values[4], previous: values[5], "yoy": values[6], prior: values[7]},
        "adjusted_net_income": {current: values[8], previous: values[9], "yoy": values[10], prior: values[11]},
        "operating_cash_flow": {current: values[12], previous: values[13], "yoy": values[14], prior: values[15]},
        "basic_eps": {current: values[16], previous: values[18], "yoy": values[20], prior: values[22]},
        "diluted_eps": {current: values[17], previous: values[19], "yoy": values[21], prior: values[23]},
        "weighted_roe": {current: values[24], previous: values[25], "change_pp": values[26], prior: values[27]},
        "total_assets": (
            {current: values[balance_start], previous: values[balance_start + 1], "yoy": values[balance_start + 2], prior: values[balance_start + 3]}
            if len(values) >= balance_start + 4 and values[balance_start] > 1_000_000 and values[balance_start + 1] > 1_000_000 and abs(values[balance_start + 2]) < 10
            else {}
        ),
        "attributable_equity": (
            {current: values[balance_start + 4], previous: values[balance_start + 5], "yoy": values[balance_start + 6], prior: values[balance_start + 7]}
            if len(values) >= balance_start + 8 and values[balance_start + 4] > 1_000_000 and values[balance_start + 5] > 1_000_000 and abs(values[balance_start + 6]) < 10
            else {}
        ),
    }
    return {
        "status": "available",
        "periods": [current, previous, prior],
        "metrics": metrics,
        "evidence_ids": [chunk.get("evidence_id")],
        "source_chunk_id": chunk.get("chunk_id"),
    }


def _compact_pdf_text(value: Any) -> str:
    text = " ".join(str(value or "").split())
    return re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)


def _money_multiplier(text: str) -> float:
    if re.search(r"单位\s*[：:]\s*千元", text):
        return 1_000.0
    if re.search(r"单位\s*[：:]\s*万元", text):
        return 10_000.0
    return 1.0


def _segment_rows(text: str, multiplier: float) -> list[dict[str, Any]]:
    start = text.find("主营业务分产品情况")
    if start < 0:
        return []
    end = text.find("主营业务分地区情况", start)
    body = text[start:end if end >= 0 else start + 5_000]
    row_pattern = re.compile(
        r"(?P<label>.{1,100}?)\s+"
        r"(?P<revenue>-?\d[\d,]*\.\d{2})\s+"
        r"(?P<cost>-?\d[\d,]*\.\d{2})\s+"
        r"(?P<margin>-?\d+(?:\.\d+)?)\s+"
        r"(?P<revenue_yoy>-?\d+(?:\.\d+)?)\s+"
        r"(?P<cost_yoy>-?\d+(?:\.\d+)?)"
    )
    output: list[dict[str, Any]] = []
    for match in row_pattern.finditer(body):
        label = match.group("label")
        label = re.split(r"[（(]\s*%\s*[）)]", label)[-1]
        label = re.sub(
            r"^(?:分产品|营业收入|营业成本|毛利率|比上年增减|上年增减|\s)+",
            "",
            label,
        ).strip(" ：；，")
        if not label or len(label) > 28:
            continue
        revenue = _number(match.group("revenue")) * multiplier
        cost = _number(match.group("cost")) * multiplier
        margin = _number(match.group("margin")) / 100
        revenue_yoy = _number(match.group("revenue_yoy")) / 100
        cost_yoy = _number(match.group("cost_yoy")) / 100
        if revenue <= 0 or cost < 0 or not -1 <= margin <= 1:
            continue
        previous_revenue = revenue / (1 + revenue_yoy) if revenue_yoy > -1 else None
        previous_cost = cost / (1 + cost_yoy) if cost_yoy > -1 else None
        previous_margin = (
            1 - previous_cost / previous_revenue
            if previous_revenue and previous_cost is not None
            else None
        )
        output.append({
            "name": label,
            "revenue": revenue,
            "cost": cost,
            "gross_margin": margin,
            "revenue_yoy": revenue_yoy,
            "cost_yoy": cost_yoy,
            "previous_revenue": previous_revenue,
            "previous_gross_margin": previous_margin,
            "gross_margin_change_pp": (
                margin - previous_margin if previous_margin is not None else None
            ),
        })
    return output


def _balance_sheet_row(
    text: str,
    label: str,
    stop_labels: tuple[str, ...],
    multiplier: float,
) -> dict[str, Any] | None:
    start = text.find(label)
    if start < 0:
        return None
    end = min(
        (
            index
            for stop in stop_labels
            if (index := text.find(stop, start + len(label))) >= 0
        ),
        default=min(len(text), start + 900),
    )
    tokens = NUMBER_RE.findall(text[start + len(label):end])
    if len(tokens) < 5:
        return None
    values = [_number(token) for token in tokens[:5]]
    current, current_share, previous, previous_share, yoy = values
    if current <= 0 or previous <= 0 or not 0 <= current_share <= 100:
        return None
    return {
        "current": current * multiplier,
        "current_asset_share": current_share / 100,
        "previous": previous * multiplier,
        "previous_asset_share": previous_share / 100,
        "yoy": yoy / 100,
    }


def _risk_exposure_metrics(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    text = _compact_pdf_text(" ".join(
        str(chunk.get("text") or "")
        for chunk in chunks
        if chunk.get("chunk_section_type") == "risk_factors"
    ))
    def amount(pattern: str) -> float | None:
        match = re.search(pattern, text)
        return _number(match.group(1)) * 1_000.0 if match else None

    def ratio(pattern: str) -> float | None:
        match = re.search(pattern, text)
        return _number(match.group(1)) / 100 if match else None

    return {
        "receivables": amount(r"应收账款账面价值为\s*([\d,]+(?:\.\d+)?)\s*千元"),
        "notes_receivable": amount(r"应收票据账面价值为\s*([\d,]+(?:\.\d+)?)\s*千元"),
        "receivables_current_asset_share": ratio(
            r"应收账款和应收票据合计占流动资产的比例为\s*([\d.]+)%"
        ),
        "inventory": amount(r"存货账面价值为\s*([\d,]+(?:\.\d+)?)\s*千元"),
        "inventory_current_asset_share": ratio(
            r"存货账面价值为.*?占流动资产的比例为\s*([\d.]+)%"
        ),
    }


def extract_operating_metrics(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    for chunk in chunks:
        text = _compact_pdf_text(chunk.get("text"))
        if "主营业务分产品情况" not in text or "营业成本" not in text:
            continue
        multiplier = _money_multiplier(text)
        rows = _segment_rows(text, multiplier)
        total = next((row for row in rows if row["name"] == "合计"), None)
        if total is None and rows:
            total = {
                "revenue": sum(row["revenue"] for row in rows),
                "previous_revenue": sum(
                    row["previous_revenue"] or 0 for row in rows
                ),
                "gross_margin": (
                    1 - sum(row["cost"] for row in rows) / sum(row["revenue"] for row in rows)
                ),
            }
        top_five = re.search(
            r"前五名客户销售额\s*([\d,]+(?:\.\d+)?)\s*千元，"
            r"占年度销售总额\s*([\d.]+)%",
            text,
        )
        operating_observations = []
        for pattern in (
            r"传输类产品库存量大幅增长\s*[\d.]+%[^。]*。",
            r"接入和数据类产品生产量和销售量大幅减少[^。]*。",
            r"经营活动产生的现金流量净额变动原因说明[^。]*。",
        ):
            match = re.search(pattern, text)
            if match:
                operating_observations.append(match.group(0))
        balance_text = _compact_pdf_text(" ".join(
            str(item.get("text") or "")
            for item in chunks
            if item.get("chunk_section_type") == "balance_sheet_analysis"
        ))
        balance_multiplier = _money_multiplier(balance_text)
        balance_rows = {
            "inventory": _balance_sheet_row(
                balance_text, "存货", ("其他流动资产", "其他非流动金融资产"), balance_multiplier
            ),
            "construction_in_progress": _balance_sheet_row(
                balance_text, "在建工程", ("使用权资产",), balance_multiplier
            ),
            "accounts_payable": _balance_sheet_row(
                balance_text, "应付账款", ("应交税费",), balance_multiplier
            ),
        }
        return {
            "status": "available" if rows and total else "partial",
            "current_revenue": total.get("revenue") if total else None,
            "previous_revenue": total.get("previous_revenue") if total else None,
            "current_gross_margin": total.get("gross_margin") if total else None,
            "previous_gross_margin": total.get("previous_gross_margin") if total else None,
            "segments": [row for row in rows if row["name"] != "合计"],
            "customer_concentration": {
                "top_five_sales": (
                    _number(top_five.group(1)) * multiplier if top_five else None
                ),
                "top_five_share": (
                    _number(top_five.group(2)) / 100 if top_five else None
                ),
            },
            "operating_observations": operating_observations,
            "balance_sheet_rows": {
                key: value for key, value in balance_rows.items() if value is not None
            },
            "risk_exposures": _risk_exposure_metrics(chunks),
            "evidence_ids": [chunk.get("evidence_id")],
            "source_chunk_id": chunk.get("chunk_id"),
            "table_layout": "a_share_product_segment",
        }
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        if "产能 产量 销量" not in text or "本报告期" not in text:
            continue
        segment = text[text.find("本报告期"):]
        end = segment.find("通过招投标方式")
        if end >= 0:
            segment = segment[:end]
        tokens = NUMBER_RE.findall(segment)
        values = [_number(token) for token in tokens]
        large = [value for value in values if abs(value) >= 1_000_000]
        ratios = [value for token, value in zip(tokens, values) if token.endswith("%")]
        small = [value for token, value in zip(tokens, values) if "万只" not in token and not token.endswith("%") and value < 10_000]
        # Annual reports generally lay this table out as current capacity/production/sales/revenue/margin,
        # followed by the same prior-period fields. Preserve raw values when the extraction is incomplete.
        return {
            "status": "available" if len(large) >= 2 and len(ratios) >= 2 else "partial",
            "current_revenue": large[0] if large else None,
            "previous_revenue": large[1] if len(large) > 1 else None,
            "current_gross_margin": ratios[0] if ratios else None,
            "previous_gross_margin": ratios[1] if len(ratios) > 1 else None,
            "raw_number_tokens": tokens[:24],
            "evidence_ids": [chunk.get("evidence_id")],
            "source_chunk_id": chunk.get("chunk_id"),
        }
    return {"status": "unavailable", "evidence_ids": []}


def extract_broker_research_signals(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract a small auditable signal set from secondary research.

    Broker research is never promoted to official company fact.  The structured
    values below retain their report-level evidence IDs and are rendered with an
    explicit secondary-source label.
    """
    result: dict[str, Any] = {
        "status": "unavailable",
        "reports": [],
        "quarter_snapshot": None,
        "annual_snapshot": None,
        "capacity_snapshot": None,
        "evidence_ids": [],
    }
    for report in reports:
        text = " ".join(str(report.get("text") or "").split())
        evidence_id = report.get("evidence_id")
        result["reports"].append({
            "title": report.get("title"),
            "source_name": report.get("source_name"),
            "published_at": report.get("published_at"),
            "rating": report.get("rating"),
            "evidence_id": evidence_id,
        })
        if evidence_id and evidence_id not in result["evidence_ids"]:
            result["evidence_ids"].append(evidence_id)
        if result["quarter_snapshot"] is None:
            match = re.search(
                r"(?P<year>20\d{2})年一季度.*?营收(?P<revenue>\d+(?:\.\d+)?)亿元，"
                r"同环比分别(?P<revenue_yoy>[+-]?\d+(?:\.\d+)?)%、(?P<revenue_qoq>[+-]?\d+(?:\.\d+)?)%；"
                r"实现归母净利润(?P<profit>\d+(?:\.\d+)?)亿元，"
                r"同环比分别(?P<profit_yoy>[+-]?\d+(?:\.\d+)?)%、(?P<profit_qoq>[+-]?\d+(?:\.\d+)?)%",
                text,
            )
            if match:
                result["quarter_snapshot"] = {
                    "period": f"{match.group('year')}Q1",
                    "revenue": float(match.group("revenue")) * 1e8,
                    "revenue_yoy": float(match.group("revenue_yoy")) / 100,
                    "revenue_qoq": float(match.group("revenue_qoq")) / 100,
                    "attributable_net_income": float(match.group("profit")) * 1e8,
                    "profit_yoy": float(match.group("profit_yoy")) / 100,
                    "profit_qoq": float(match.group("profit_qoq")) / 100,
                    "evidence_ids": [evidence_id] if evidence_id else [],
                    "source_name": report.get("source_name"),
                }
        if result["annual_snapshot"] is None:
            annual = re.search(r"(?P<year>20\d{2})年公司营业收入(?P<revenue>\d+(?:\.\d+)?)亿元", text)
            mix = re.search(r"传输类、接入及数据类收入占比分别为(?P<transmission>\d+(?:\.\d+)?)%、(?P<data>\d+(?:\.\d+)?)%", text)
            if annual:
                result["annual_snapshot"] = {
                    "period": annual.group("year"),
                    "revenue": float(annual.group("revenue")) * 1e8,
                    "transmission_share": float(mix.group("transmission")) / 100 if mix else None,
                    "access_data_share": float(mix.group("data")) / 100 if mix else None,
                    "evidence_ids": [evidence_id] if evidence_id else [],
                    "source_name": report.get("source_name"),
                }
        if result["capacity_snapshot"] is None:
            capacity = re.search(
                r"现有产能约为(?P<current>\d+(?:\.\d+)?)亿元.*?"
                r"新增产能(?P<thailand>\d+(?:\.\d+)?)亿元.*?"
                r"再新增(?P<wuxi>\d+(?:\.\d+)?)亿元产能.*?"
                r"总产能将达到(?P<total>\d+(?:\.\d+)?)亿元",
                text,
            )
            if capacity:
                result["capacity_snapshot"] = {
                    "current": float(capacity.group("current")) * 1e8,
                    "thailand_increment": float(capacity.group("thailand")) * 1e8,
                    "wuxi_increment": float(capacity.group("wuxi")) * 1e8,
                    "planned_total": float(capacity.group("total")) * 1e8,
                    "evidence_ids": [evidence_id] if evidence_id else [],
                    "source_name": report.get("source_name"),
                }
    if result["reports"]:
        result["status"] = "secondary_only"
    return result


def _market_analysis(target: dict[str, Any]) -> dict[str, Any]:
    bars = target.get("daily_bars") or []
    latest = bars[0] if bars else {}
    quote = target.get("quote") or {}
    valuation = target.get("valuation") or {}
    result: dict[str, Any] = {
        "as_of": quote.get("quote_time") or latest.get("trade_date"),
        "latest_price": quote.get("price") if quote.get("price") is not None else latest.get("close"),
        "price_type": "intraday_quote" if quote.get("price") is not None else "completed_close",
        "latest_completed_session": latest.get("trade_date"),
        "latest_completed_close": latest.get("close"),
        "return_5d": None,
        "return_20d": None,
        "valuation": valuation,
        "evidence_ids": list(dict.fromkeys([
            *(quote.get("source_evidence_ids") or []),
            *(valuation.get("source_evidence_ids") or []),
        ])),
    }
    for days, key in ((5, "return_5d"), (20, "return_20d")):
        if len(bars) >= 2:
            index = min(days - 1, len(bars) - 1)
            old = bars[index].get("close")
            current = latest.get("close")
            result[key] = _change(float(current), float(old)) if current and old else None
    return result


def _peer_analysis(peers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for peer in peers:
        bars = peer.get("daily_bars") or []
        latest = bars[0] if bars else {}
        oldest = bars[-1] if len(bars) > 1 else {}
        valuation = peer.get("valuation") or {}
        output.append({
            "ticker": peer.get("ticker"),
            "company_name": peer.get("company_name") or peer.get("ticker"),
            "as_of": valuation.get("generated_at") or latest.get("trade_date"),
            "latest_price": valuation.get("current_price") if valuation.get("current_price") is not None else latest.get("close"),
            "period_return": _change(latest.get("close"), oldest.get("close")) if latest.get("close") and oldest.get("close") else None,
            "market_cap": valuation.get("market_cap"),
            "pe_ttm": valuation.get("pe_ttm"),
            "pb_mrq": valuation.get("pb"),
            "valuation_flags": valuation.get("valuation_flags") or [],
            "currency": valuation.get("currency") or "CNY",
            "selection_reason": peer.get("selection_reason"),
            "evidence_ids": valuation.get("source_evidence_ids") or [],
            "has_valuation": bool(valuation),
            "has_fundamentals": bool(peer.get("fundamentals")),
        })
    return output


def _coverage(
    context: dict[str, Any], plan: dict[str, Any], annual: dict[str, Any], broker: dict[str, Any]
) -> dict[str, Any]:
    corpus = context["corpus"]
    topics = {topic for chunk in corpus["chunks"] for topic in chunk.get("research_topics") or []}
    graph = context.get("graph") or {}
    target = (context.get("instruments") or {}).get("target") or {}
    peer_instruments = (context.get("instruments") or {}).get("peers") or []
    has_official = bool(corpus.get("filings") and corpus.get("chunks"))
    has_financials = annual.get("status") == "available"
    has_peer_matrix = bool(
        graph.get("peers")
        and peer_instruments
        and any((item.get("valuation") or {}).get("current_price") is not None for item in peer_instruments)
    )
    has_valuation = bool(
        (target.get("valuation") or {}).get("current_price") is not None
        and (target.get("valuation") or {}).get("pe_ttm") is not None
    )
    has_product_catalyst = any(
        item.get("chunk_section_type") == "product_progress"
        for item in corpus.get("chunks") or []
    )
    map_status = {
        "investment_summary": has_official and has_financials,
        "company_business": "business" in topics,
        "industry": "industry" in topics,
        "products_moat": "products" in topics,
        "operations": "operations" in topics,
        "financials": has_financials,
        "peers": has_peer_matrix,
        "growth": "growth" in topics,
        "valuation": has_valuation,
        "catalysts": bool(corpus["news"] or corpus["events"] or has_product_catalyst),
        "risks": "risks" in topics,
        "scenarios": has_financials and has_official,
        "tracking": has_official,
        "conclusion": has_financials and has_official,
        "evidence_index": has_official,
    }
    sections = []
    for section in plan["sections"]:
        covered = bool(map_status.get(section["section_id"]))
        sections.append({**section, "status": "covered" if covered else "degraded"})
    covered_count = sum(item["status"] == "covered" for item in sections)
    return {"sections": sections, "covered": covered_count, "total": len(sections), "score": covered_count / len(sections)}


def build_market_peer_analysis(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "market": _market_analysis(context["instruments"]["target"]),
        "peers": _peer_analysis(context["instruments"]["peers"]),
    }


def build_financial_analysis(context: dict[str, Any], market: dict[str, Any]) -> dict[str, Any]:
    chunks = context["corpus"]["chunks"]
    annual = extract_a_share_annual_metrics(chunks)
    operations = extract_operating_metrics(chunks)
    broker = extract_broker_research_signals(context["corpus"].get("broker_reports") or [])
    metrics = annual.get("metrics") or {}
    periods = annual.get("periods") or []
    current = periods[0] if periods else None
    derived: dict[str, Any] = {}
    if current:
        revenue = (metrics.get("revenue") or {}).get(current)
        profit = (metrics.get("attributable_net_income") or {}).get(current)
        cash_flow = (metrics.get("operating_cash_flow") or {}).get(current)
        eps = (metrics.get("basic_eps") or {}).get(current)
        derived = {
            "net_margin": profit / revenue if revenue and profit is not None else None,
            "cash_conversion": cash_flow / profit if profit and cash_flow is not None else None,
            "trailing_pe_from_latest_price": market["latest_price"] / eps if market.get("latest_price") and eps else None,
            "trailing_pe_basis": f"latest price / {current} basic EPS" if eps else None,
        }
    insights = []
    if current:
        revenue_yoy = (metrics.get("revenue") or {}).get("yoy")
        profit_yoy = (metrics.get("attributable_net_income") or {}).get("yoy")
        cash_yoy = (metrics.get("operating_cash_flow") or {}).get("yoy")
        if revenue_yoy is not None and profit_yoy is not None:
            if revenue_yoy >= 0 and profit_yoy >= revenue_yoy:
                growth_assessment = "利润增速快于收入，利润率方向改善"
            elif revenue_yoy >= 0 > profit_yoy:
                growth_assessment = "收入增长但利润下降，盈利质量和利润率承压"
            elif profit_yoy < revenue_yoy:
                growth_assessment = "利润表现弱于收入，经营杠杆向下"
            else:
                growth_assessment = "利润表现好于收入，但仍需结合绝对规模判断"
            insights.append({
                "type": "growth_quality",
                "statement": (
                    f"{current} 年收入同比 {_pct(revenue_yoy)}，归母净利润同比 {_pct(profit_yoy)}；"
                    f"{growth_assessment}。"
                ),
                "evidence_ids": annual["evidence_ids"],
            })
        if cash_yoy is not None and derived.get("cash_conversion") is not None:
            if profit_yoy is not None and cash_yoy < profit_yoy:
                cash_assessment = "现金流表现弱于利润，需要重点核对营运资本占用"
            elif derived["cash_conversion"] >= 1:
                cash_assessment = "现金流覆盖当期利润"
            else:
                cash_assessment = "现金流未完全覆盖当期利润"
            insights.append({
                "type": "cash_quality",
                "statement": (
                    f"经营现金流同比 {_pct(cash_yoy)}，经营现金流/归母净利润为 "
                    f"{derived['cash_conversion']:.2f} 倍；{cash_assessment}。"
                ),
                "evidence_ids": annual["evidence_ids"],
            })
        roe = (metrics.get("weighted_roe") or {}).get(current)
        if roe is not None:
            insights.append({
                "type": "capital_efficiency",
                "statement": f"加权平均 ROE 为 {_pct(roe)}，需要结合利润率、周转效率与资本投入判断其变化原因。",
                "evidence_ids": annual["evidence_ids"],
            })
    return {
        "annual_financials": annual,
        "operating_metrics": operations,
        "broker_research": broker,
        "derived": derived,
        "insights": insights,
    }


def build_business_industry_analysis(context: dict[str, Any]) -> dict[str, Any]:
    corpus = context["corpus"]
    topic_counts: dict[str, int] = {}
    evidence_ids: list[str] = []
    for item in [*(corpus.get("chunks") or []), *(corpus.get("broker_reports") or [])]:
        for topic in item.get("research_topics") or []:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        if item.get("evidence_id"):
            evidence_ids.append(str(item["evidence_id"]))
    return {
        "topic_counts": topic_counts,
        "sector": (context.get("graph") or {}).get("sector") or {},
        "official_chunk_count": len(corpus.get("chunks") or []),
        "secondary_report_count": len(corpus.get("broker_reports") or []),
        "evidence_ids": list(dict.fromkeys(evidence_ids)),
    }


def build_catalyst_risk_analysis(context: dict[str, Any]) -> dict[str, Any]:
    corpus = context["corpus"]
    return {
        "news_count": len(corpus.get("news") or []),
        "event_count": len(corpus.get("events") or []),
        "risk_source_count": sum(
            "risks" in (item.get("research_topics") or [])
            for item in [*(corpus.get("chunks") or []), *(corpus.get("broker_reports") or [])]
        ),
        "evidence_ids": list(dict.fromkeys(
            str(item["evidence_id"])
            for item in [*(corpus.get("news") or []), *(corpus.get("events") or [])]
            if item.get("evidence_id")
        )),
    }


def assemble_stock_analysis_v3(
    context: dict[str, Any],
    plan: dict[str, Any],
    *,
    market_peers: dict[str, Any],
    financials: dict[str, Any],
    business_industry: dict[str, Any],
    catalysts_risks: dict[str, Any],
) -> dict[str, Any]:
    return {
        **financials,
        **market_peers,
        "business_industry": business_industry,
        "catalysts_risks": catalysts_risks,
        "coverage": _coverage(
            context,
            plan,
            financials["annual_financials"],
            financials["broker_research"],
        ),
    }


def build_stock_analysis_v3(context: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    market_peers = build_market_peer_analysis(context)
    financials = build_financial_analysis(context, market_peers["market"])
    return assemble_stock_analysis_v3(
        context,
        plan,
        market_peers=market_peers,
        financials=financials,
        business_industry=build_business_industry_analysis(context),
        catalysts_risks=build_catalyst_risk_analysis(context),
    )
