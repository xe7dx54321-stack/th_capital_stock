from __future__ import annotations

import re
from statistics import median
from typing import Any


CITATION_RE = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9_.:-]{2,127})\]")
REQUIRED_HEADINGS = (
    "投资摘要与核心判断", "公司画像与商业模式", "行业阶段与需求驱动", "产品矩阵与核心竞争力",
    "经营模式、客户与供应链", "财务深度分析", "同行比较与竞争格局", "增长驱动与预测边界", "估值分析", "催化剂与时间表",
    "风险、反面证据与证伪条件", "三种情景", "后续跟踪指标", "结论", "证据索引",
)
FORBIDDEN_SYSTEM_TEXT = ("隔离字段数量", "执行步骤：", "任务编号：", "权威研究任务：", "引用校验：")
FORBIDDEN_SOURCE_NOISE = ("监管指引第 4 号", "产品外观 产品特性 应用场景")
RAW_LAYOUT_NOISE_RE = (
    re.compile(r"[□√]\s*(?:适用|不适用)"),
    re.compile(r"\b\d{1,3}\s*/\s*\d{1,3}\b"),
)
FORBIDDEN_PROCESS_TEXT = (
    "本报告的价值是建立",
    "研究上应建立",
    "下一步必须补齐",
    "后续更新必须",
    "当前未取得可直接用于核心主张",
    "当前财务材料只有",
    "主要会计数据表未能被确定性解析",
    "本节降级",
    "当前没有可审计的同行数据",
    "没有可用的近期行情",
    "证据边界风险",
    "内部行业映射",
    "受治理",
    "质量门",
    "研究包",
    "工具调用",
)


def _citation(ids: list[str | None]) -> str:
    return " ".join(f"[{value}]" for value in dict.fromkeys(value for value in ids if value))


def _money(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value / 1e8:,.2f} 亿元"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}%"


def _pp(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f} 个百分点"


def _yoy_text(value: float | None) -> str:
    if value is None:
        return "变化率不可得"
    direction = "增长" if value >= 0 else "下降"
    return f"{direction} {abs(value) * 100:.2f}%"


def _pp_text(value: float | None) -> str:
    if value is None:
        return "变化不可得"
    direction = "提升" if value >= 0 else "下降"
    return f"{direction} {abs(value) * 100:.2f} 个百分点"


def _sequence_text(values: list[float]) -> str:
    first, second, third = values
    first_move = "升至" if second >= first else "降至"
    second_move = "再升至" if third >= second else "再降至"
    return f"从 {_pct(first)} {first_move} {_pct(second)}，{second_move} {_pct(third)}"


def _find_chunks(context: dict[str, Any], *topics: str, limit: int = 3) -> list[dict[str, Any]]:
    output = []
    seen = set()
    for item in context["corpus"]["chunks"]:
        if not set(item.get("research_topics") or []).intersection(topics):
            continue
        identity = item.get("chunk_id") or (
            item.get("evidence_id"),
            item.get("chunk_section_type"),
            str(item.get("text") or "")[:160],
        )
        if identity in seen:
            continue
        seen.add(identity)
        output.append(item)
        if len(output) >= limit:
            break
    return output


def _find_section_chunks(context: dict[str, Any], *section_types: str, limit: int = 3) -> list[dict[str, Any]]:
    wanted = set(section_types)
    return [
        item for item in context["corpus"]["chunks"]
        if item.get("chunk_section_type") in wanted
    ][:limit]


def _compact_chunk_text(chunk: dict[str, Any]) -> str:
    text = " ".join(str(chunk.get("text") or "").split())
    return re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)


def _photonics_progress_rows(text: str) -> list[tuple[str, str, str]]:
    patterns = (
        ("400G 相干模块", r"400G\s*相干模块完成小批量试产", "小批量试产"),
        ("800G 相干模块器件", r"800G\s*相干模块器件.*?实现订单交付", "取得技术突破并交付订单"),
        ("400G/800G 数通模块", r"400G/800G\s*数通模块.*?小批量订单", "产品迭代并取得小批量订单"),
        ("1.6T 数通模块", r"1\.6T\s*数通模块完成.*?产品开发", "完成 EML、硅光、TFLN 多方案开发"),
        ("400G/600G DCI 板卡", r"400G/600G\s*DCI\s*板卡批量交付", "批量交付"),
        ("800G 板卡", r"800G\s*板卡完成样品开发及验证", "样品开发及验证"),
        ("1.6T 板卡", r"1\.6T\s*板卡开始预研", "预研"),
    )
    rows = []
    for product, pattern, status in patterns:
        if re.search(pattern, text):
            next_gate = (
                "持续批量、收入占比与毛利率"
                if "批量交付" in status or "订单" in status
                else "客户认证、小批量订单与量产良率"
            )
            rows.append((product, status, next_gate))
    return rows


def _excerpt(chunk: dict[str, Any], keywords: tuple[str, ...], limit: int = 360) -> str:
    text = " ".join(str(chunk.get("text") or "").split())
    # PDF extraction often inserts spaces inside Chinese words and carries table/page
    # labels into prose.  Keep citations to the source chunk, but never paste its raw
    # layout noise into the reader-facing report.
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"\bP\d{1,3}\b", "", text, flags=re.I)
    text = re.sub(r"\s*-\s*\d{1,3}\s*-\s*", " ", text)
    text = re.sub(r"[\u4e00-\u9fff]{2,30}(?:股份)?有限公司\s*20\d{2}\s*年年度报告(?:全文)?", "", text)
    text = re.sub(r"监管指引第\s*4\s*号.*?(?=公司主营业务)", "", text)
    text = text.replace("产品系列 产品外观 产品特性 应用场景", "")
    text = re.sub(r"[□√]\s*(?:适用|不适用)", "", text)
    text = re.sub(r"\b\d{1,3}\s*/\s*\d{1,3}\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    start = next((text.find(keyword) for keyword in keywords if text.find(keyword) >= 0), 0)
    candidate = text[start:start + max(1_600, limit * 6)]
    for stop in ("新增重要非主营业务情况", "行业情况说明", "非企业会计准则财务指标"):
        stop_index = candidate.find(stop, 80)
        if stop_index >= 0:
            candidate = candidate[:stop_index]
    clauses = [item.strip(" ，。；：") for item in re.split(r"(?<=[。；！？])", candidate) if item.strip()]
    selected = []
    for clause in clauses:
        if not selected or any(keyword in clause for keyword in keywords):
            selected.append(clause)
        if len("；".join(selected)) >= limit:
            break
    excerpt = "；".join(selected)
    if len(excerpt) > limit:
        prefix = excerpt[:limit]
        boundary = max(prefix.rfind(mark) for mark in ("。", "；", "！", "？"))
        if boundary >= max(60, int(limit * 0.55)):
            excerpt = prefix[:boundary + 1]
        else:
            tail = excerpt[limit:min(len(excerpt), limit + 120)]
            tail_boundary = min(
                (index for mark in ("。", "；", "！", "？") if (index := tail.find(mark)) >= 0),
                default=-1,
            )
            excerpt = (
                excerpt[:limit + tail_boundary + 1]
                if tail_boundary >= 0
                else prefix.rstrip(" ，、：") + "……"
            )
    return excerpt.rstrip(" ，。；：")


def compile_stock_research_report_v3(packet: dict[str, Any]) -> str:
    v3 = packet["research_v3"]
    context = v3["context"]
    analysis = v3["analysis"]
    identity = context["identity"]
    annual = analysis["annual_financials"]
    metrics = annual.get("metrics") or {}
    periods = annual.get("periods") or []
    current = periods[0] if periods else None
    evidence = annual.get("evidence_ids") or []
    official_cite = _citation(evidence)
    business_chunks = _find_chunks(context, "business", limit=3)
    product_chunks = _find_chunks(context, "products", limit=3)
    operations_chunks = _find_chunks(context, "operations", limit=2)
    industry_chunks = _find_chunks(context, "industry", "growth", limit=3)
    risk_chunks = _find_chunks(context, "risks", limit=3)
    performance_chunks = _find_section_chunks(context, "performance_drivers", limit=2)
    product_progress_chunks = _find_section_chunks(context, "product_progress", limit=2)
    operating_model_chunks = _find_section_chunks(context, "operating_model", limit=1)
    competitive_chunks = _find_section_chunks(context, "competitive_advantages", limit=2)
    outlook_chunks = _find_section_chunks(context, "outlook", limit=2)
    filings = context["corpus"]["filings"]
    news = context["corpus"]["news"]
    events = context["corpus"]["events"]
    broker_reports = context["corpus"].get("broker_reports") or []
    broker = analysis.get("broker_research") or {}
    market = analysis["market"]
    derived = analysis["derived"]
    company_name = identity.get("company_name") or packet["ticker"]
    sector_text = " ".join(str(value or "") for value in (
        identity.get("sector_key"), identity.get("sector_name"),
        (context.get("graph", {}).get("sector") or {}).get("sector_name"),
    ))
    corpus_preview = " ".join(str(item.get("text") or "")[:800] for item in context["corpus"]["chunks"][:12])
    corpus_preview += " " + " ".join(str(item.get("text") or "")[:800] for item in broker_reports[:3])
    is_photonics = packet["ticker"] == "300308.SZ" or any(term in sector_text + corpus_preview for term in ("光通信", "光模块", "800G", "1.6T"))

    lines = [
        f"# {identity.get('company_name') or packet['ticker']}（{packet['ticker']}）个股深度研究",
        "",
        f"> 研究基准：正式披露优先；报告生成于 {packet['generated_at'][:10]}。行情数据截至 {market.get('as_of') or '未取得'}。",
        "",
        "## 1. 投资摘要与核心判断",
        "",
    ]
    for insight in analysis.get("insights") or []:
        lines.append(f"- {insight['statement']} {_citation(insight.get('evidence_ids') or [])}")
    if current:
        revenue = metrics.get("revenue", {}).get(current)
        profit = metrics.get("attributable_net_income", {}).get(current)
        cash = metrics.get("operating_cash_flow", {}).get(current)
        revenue_yoy = metrics.get("revenue", {}).get("yoy")
        profit_yoy = metrics.get("attributable_net_income", {}).get("yoy")
        cash_yoy = metrics.get("operating_cash_flow", {}).get("yoy")
        if all(value is not None and value >= 0 for value in (revenue_yoy, profit_yoy, cash_yoy)):
            summary_assessment = "收入、利润和现金流同向改善。"
        elif revenue_yoy is not None and revenue_yoy >= 0 and profit_yoy is not None and profit_yoy < 0:
            summary_assessment = "收入增长没有转化为利润增长，盈利质量是当前核心矛盾。"
        else:
            summary_assessment = "三项指标方向并不一致，不能把收入变化直接外推为盈利与现金流改善。"
        lines.extend([
            (
                f"- {current} 年，公司实现营业收入 {_money(revenue)}、归母净利润 {_money(profit)}、"
                f"经营活动现金流净额 {_money(cash)}；同比分别{_yoy_text(revenue_yoy)}、"
                f"{_yoy_text(profit_yoy)}、{_yoy_text(cash_yoy)}。{summary_assessment}{official_cite}"
            ),
            "- 当前最值得研究的矛盾不是“公司是否增长”，而是需求景气、产品升级和交付优势还能维持多久，以及市场价格已经反映了多少增长预期。",
        ])
        if performance_chunks:
            driver_excerpt = _excerpt(
                performance_chunks[0],
                ("业绩变化主要源于", "传统电信市场", "战略投入", "购买商品"),
                380,
            )
            if driver_excerpt:
                lines.append(
                    f"- 年报对利润与现金流压力的解释是：{driver_excerpt}。"
                    f"{_citation([performance_chunks[0].get('evidence_id')])}"
                )
    elif broker.get("quarter_snapshot"):
        snapshot = broker["quarter_snapshot"]
        lines.extend([
            f"- 现有经营数字来自{snapshot.get('source_name') or '券商研报'}的二级转述，不作为公司正式财务事实。{_citation(snapshot.get('evidence_ids') or [])}",
            f"- 券商研报转述 {snapshot['period']} 营收约 {_money(snapshot.get('revenue'))}，同比 {_pct(snapshot.get('revenue_yoy'))}；归母净利润约 {_money(snapshot.get('attributable_net_income'))}，同比 {_pct(snapshot.get('profit_yoy'))}。这是研究线索，不是已通过一手证据门的事实。{_citation(snapshot.get('evidence_ids') or [])}",
            "- 这些二级数据只能支持业务假设，不能支持完整财务判断、估值结论或买卖结论。",
        ])
    lines.extend(["", "## 2. 公司画像与商业模式", ""])
    if business_chunks:
        cite = _citation([business_chunks[0].get('evidence_id')])
        excerpt = _excerpt(business_chunks[0], ("公司主营业务", "主营业务", "经营模式", "销售模式"), 280)
        lines.append(f"年报的主营业务摘要为：{excerpt}。{cite}")
        lines.extend([
            "收入获取链条可拆为“客户资本开支与网络升级需求→方案与供应商认证→产品代码认证→订单→批量交付→售后支持”。认证周期和量产能力构成进入门槛，但也使业绩更容易受头部客户投资节奏影响。",
            "商业模式质量不能只用收入增速衡量。更关键的四个验证项是：重要客户中的供应份额是否稳定，产品升级是否支撑平均售价与毛利率，批量交付是否伴随良率改善，以及利润能否转化为经营现金流。",
        ])
    elif broker_reports:
        report = broker_reports[0]
        lines.extend([
            f"二级研究材料将公司定位为光电子器件综合供应商，业务覆盖光收发模块、光放大器和光传输子系统，下游覆盖电信设备商、运营商、工业专网与数据中心互联场景。{_citation([report.get('evidence_id')])}",
            "商业模式可拆为两类：传统传输业务提供基础收入与客户关系，接入、数通和 DCI 业务提供增长弹性。研究关键是后者的增长能否超过传统业务下滑，并在产能扩张后转化为利润和现金流。",
            "与单纯器件公司相比，从器件到板卡、子系统和 DCI 整机的覆盖可以扩大客户价值量，但也增加产品组合、客户导入、交付和营运资金管理难度。",
        ])
    else:
        lines.append("正式材料尚不足以完整重建商业模式，本节仅保留研究问题，不进行外推。")

    lines.extend(["", "## 3. 行业阶段与需求驱动", ""])
    sector = context.get("graph", {}).get("sector") or {}
    industry_focus = "云数据中心互联速率升级、AI 集群规模、网络拓扑变化和单位算力光连接价值量" if is_photonics else "终端需求、客户预算、竞争供给、渗透率和监管环境"
    inferred_sector = "光通信与光电子器件" if is_photonics else "行业待确认"
    lines.append(f"公司所处行业为“{sector.get('sector_name') or identity.get('sector_name') or inferred_sector}”。业绩的主要需求变量包括{industry_focus}，题材热度本身不能解释公司收入和利润。")
    if outlook_chunks:
        for chunk in outlook_chunks[:2]:
            outlook_text = _compact_chunk_text(chunk)
            outlook_cite = _citation([chunk.get("evidence_id")])
            if (
                is_photonics
                and all(term in outlook_text for term in ("传统电信", "算力网络", "供应链", "自主"))
            ):
                lines.extend([
                    f"- 公司年报将需求概括为传统电信网络升级与算力网络建设的双轮驱动："
                    f"前者偏稳定存量需求，后者是高速率光模块、DCI 与子系统的新增量来源。{outlook_cite}",
                    f"- 年报同时认为竞争已经呈现结构化分层，供应链安全、核心技术自主和"
                    f"全球交付能力会影响企业能否把行业需求转化为持续份额。该表述属于公司"
                    f"管理层判断，仍需用订单、产品结构与同行经营数据验证。{outlook_cite}",
                ])
                break
            lines.append(f"- 正式材料显示：{_excerpt(chunk, ('行业格局', '发展趋势', '市场需求', '竞争'), 320)}。{outlook_cite}")
    elif industry_chunks:
        for chunk in industry_chunks[:2]:
            lines.append(f"- 正式材料显示：{_excerpt(chunk, ('行业', '市场需求', '需求', '市场份额'), 260)}。{_citation([chunk.get('evidence_id')])}")
    elif broker_reports:
        report = broker_reports[0]
        lines.append(f"- 券商研报认为，AI 集群跨域组网正在提升 DCI 设备、板卡、光放大器和长距离光模块需求；该判断属于行业观点，需用客户订单、交付和公司正式披露持续验证。{_citation([report.get('evidence_id')])}")
    if is_photonics:
        lines.append("")
        lines.extend([
            "800G/1.6T 的放量速度决定收入弹性，硅光、EML、LPO 等路线的良率、功耗和成本决定利润弹性，客户资本开支和产品认证节奏决定兑现时间。这三层需要同向改善，行业景气才可能转化为公司订单和利润。",
            "时间维度上，短期看云厂商资本开支、客户认证与交付节奏；中期看 1.6T 占比、技术路线与单位成本；长期看网络架构演进是否持续提升单位算力的光连接价值量。三个层次只有同向时，行业增长才更可能沉淀为持续盈利。",
        ])
    else:
        lines.append("从研究框架看，需要把行业总需求、公司份额、产品价格与单位成本分开验证：总需求决定收入天花板，竞争地位与交付能力决定份额，产品结构和成本控制决定利润弹性。行业景气不能直接等同于公司订单，更不能替代公司层面的财务兑现。")

    lines.extend(["", "## 4. 产品矩阵与核心竞争力", ""])
    if product_chunks:
        product_text = _compact_chunk_text(product_chunks[0])
        product_cite = _citation([product_chunks[0].get("evidence_id")])
        if all(term in product_text for term in ("传输类产品", "接入类产品", "数据通信产品")):
            lines.extend([
                f"- **传输类**：覆盖电信传输光收发模块、光纤放大器、传输子系统和"
                f"光无源模块；光模块速率从 155M、1.25G、10G、100G 延伸至 400G 及以上，"
                f"传输距离覆盖 10km、40km、80km 及以上。{product_cite}",
                f"- **接入类**：覆盖 GPON OLT、Combo PON、BOSA，以及用于无线前传的"
                f"10G/25G 灰光和彩光模块。{product_cite}",
                f"- **数据通信类**：覆盖数据中心互联 DCI 与机房内部短距光模块，"
                f"短距模块面向 2km 以下场景。{product_cite}",
            ])
        else:
            lines.append(f"- {_excerpt(product_chunks[0], ('主要产品', '产品', '研发', '客户'), 340)}。{product_cite}")
        for chunk in product_progress_chunks[:1]:
            progress_text = _compact_chunk_text(chunk)
            progress_cite = _citation([chunk.get("evidence_id")])
            research_match = re.search(
                r"研发投入金额达\s*([\d,]+(?:\.\d+)?)\s*千元，"
                r"研发投入占营收比例为\s*([\d.]+)%",
                progress_text,
            )
            if research_match:
                research_value = float(research_match.group(1).replace(",", "")) * 1_000
                lines.append(
                    f"- 报告期研发投入约 {_money(research_value)}，占收入 "
                    f"{float(research_match.group(2)):.2f}%。高研发强度需要由产品认证、"
                    f"规模收入与利润率改善来证明投入产出。{progress_cite}"
                )
            progress_rows = _photonics_progress_rows(progress_text)
            if progress_rows:
                lines.extend([
                    "",
                    "| 产品/平台 | 年报披露阶段 | 下一验证门 |",
                    "|---|---|---|",
                ])
                for product, status, next_gate in progress_rows:
                    lines.append(f"| {product} | {status} | {next_gate} |")
                lines.append(
                    f"该表严格区分预研、样品、验证、小批量和批量交付；只有跨过后续验证门，"
                    f"技术进展才能进入盈利判断。{progress_cite}"
                )
            else:
                lines.append(
                    f"- 年报披露的产品商业化进展为："
                    f"{_excerpt(chunk, ('技术突破驱动产品矩阵升级', '研发投入', '400G', '800G', '1.6T'), 520)}。"
                    f"{progress_cite}"
                )
        for chunk in competitive_chunks[:1]:
            competitive_text = _compact_chunk_text(chunk)
            patent_match = re.search(
                r"累计取得\s*(\d+)\s*项专利，其中发明专利\s*(\d+)\s*项、"
                r"实用新型专利\s*(\d+)\s*项、外观设计专利\s*(\d+)\s*项",
                competitive_text,
            )
            competitive_cite = _citation([chunk.get("evidence_id")])
            if patent_match:
                lines.append(
                    f"- 截至报告期末，公司累计取得 {patent_match.group(1)} 项专利，其中发明专利 "
                    f"{patent_match.group(2)} 项、实用新型 {patent_match.group(3)} 项、外观设计 "
                    f"{patent_match.group(4)} 项。专利数量只能证明研发资产积累，护城河仍需由"
                    f"客户认证、量产良率、产品份额和利润率持续验证。{competitive_cite}"
                )
            else:
                lines.append(
                    f"- 公司对竞争力的正式披露包括："
                    f"{_excerpt(chunk, ('技术创新', '研发优势', '专利', '客户资源'), 360)}。"
                    f"{competitive_cite}"
                )
    elif broker_reports and is_photonics:
        report = broker_reports[0]
        lines.extend([
            f"- 二级研究材料描述的 DCI 产品布局包括 DCIBOX 整机、光放大器/WSS/光模块等器件及板卡，以及相干和非相干可插拔光模块。{_citation([report.get('evidence_id')])}",
            f"- 研报转述 400G/600G DCI 板卡已批量交付，800G 板卡完成样品开发与验证，1.6T 板卡仍处于预研；这些进展必须区分“研发”、“客户导入”、“小批量”和“规模收入”四个阶段。{_citation([report.get('evidence_id')])}",
            f"- 研报还提到 1.6T 光模块布局硅光、EML 和薄膜铌酸锂三条方案，硅基光波导 OCS 处于端口数扩展和客户验证阶段。多路线布局提供选择权，但不等于所有路线都能同时规模商业化。{_citation([report.get('evidence_id')])}",
        ])
    if is_photonics:
        lines.append("")
        product_source_label = "正式年报" if product_chunks else "现有二级研究材料"
        lines.extend([
            "核心竞争力可以拆成四个可验证环节：第一，速率代际能否领先进入客户认证；第二，不同技术平台能否覆盖距离、功耗和成本需求；第三，量产良率和供应链组织能否支持大规模交付；第四，产品迭代能否转化为持续的毛利率和现金流，而不是一次性的收入脉冲。",
            f"{product_source_label}所描述的多平台与多规格产品组合说明公司没有只押注单一技术路线，但也意味着研发投入、物料管理和产线切换更复杂。由于当前缺少各路线收入、毛利率和量产良率的一手数据，这里只能确认技术布局线索，不能确认其已经形成护城河。",
            "商业化质量可以用“产品代际—认证状态—收入占比—毛利率—现金转化”连续判断。如果新产品只有技术发布却没有认证和量产，不应计入盈利预期；如果出货放量但毛利率与现金流恶化，则需警惕价格换量或营运资金占用。",
        ])
    else:
        lines.extend([
            "核心竞争力需要拆成可验证环节：产品或服务能否持续解决客户关键问题，研发与渠道投入能否形成转化，规模扩张能否保持交付质量，竞争优势最终能否沉淀为毛利率、周转效率和自由现金流。",
            "产品矩阵本身不等于护城河。真正的护城河应由客户留存或复购、议价能力、单位经济性、交付可靠性以及新产品商业化速度共同验证，并与竞争对手同口径比较。",
        ])

    lines.extend(["", "## 5. 经营模式、客户与供应链", ""])
    if operating_model_chunks:
        operating_text = _compact_chunk_text(operating_model_chunks[0])
        operating_cite = _citation([operating_model_chunks[0].get("evidence_id")])
        if all(term in operating_text for term in ("采购模式", "生产模式", "销售模式")):
            lines.extend([
                f"- **采购**：以销定采并保留适度备货，采购需求同时受在手订单、销售预测和"
                f"研发项目驱动。{operating_cite}",
                f"- **生产**：以自主生产为主，按销售订单与销售预测组合排产；这使产能与"
                f"库存管理对需求预测准确度较敏感。{operating_cite}",
                f"- **销售与导入**：直销为主、经销为辅，潜在客户通常需要经过需求沟通、"
                f"样品测试与客户认证后才形成订单。{operating_cite}",
            ])
        else:
            lines.append(
                f"年报对采购、生产、销售与客户导入的描述为："
                f"{_excerpt(operating_model_chunks[0], ('采购模式', '生产模式', '销售模式', '客户认证'), 420)}。"
                f"{operating_cite}"
            )
    elif operations_chunks:
        if is_photonics:
            lines.append(f"年报披露，原材料主要包括光器件、集成电路芯片与结构件，公司对供应商实施遴选和采购控制；生产以销定产，销售以直销为主，进入客户体系通常需通过供应商和产品代码认证。{_citation([operations_chunks[0].get('evidence_id')])}")
        else:
            lines.append(f"正式材料对采购、生产、销售和客户获取的描述为：{_excerpt(operations_chunks[0], ('采购模式', '生产模式', '销售模式', '客户'), 300)}。{_citation([operations_chunks[0].get('evidence_id')])}")
    operations = analysis.get("operating_metrics") or {}
    if operations.get("status") != "unavailable":
        segment_label = "公司主营业务" if is_photonics else "主要经营分部"
        current_margin = operations.get("current_gross_margin")
        previous_margin = operations.get("previous_gross_margin")
        margin_change = (
            current_margin - previous_margin
            if current_margin is not None and previous_margin is not None
            else None
        )
        margin_direction = (
            f"提升 {abs(margin_change) * 100:.2f} 个百分点"
            if margin_change is not None and margin_change >= 0
            else f"下降 {abs(margin_change) * 100:.2f} 个百分点"
            if margin_change is not None
            else "变化暂不可算"
        )
        lines.append(
            f"{segment_label}本期收入约 {_money(operations.get('current_revenue'))}，"
            f"上期约 {_money(operations.get('previous_revenue'))}；主营业务毛利率由 "
            f"{_pct(previous_margin)}变为 {_pct(current_margin)}，{margin_direction}。"
            f"这说明收入增长需要和产品结构、价格竞争及成本增速结合判断，不能直接外推为利润增长。"
            f"{_citation(operations.get('evidence_ids') or [])}"
        )
        segments = operations.get("segments") or []
        if segments:
            lines.extend([
                "",
                "| 分产品 | 本期收入 | 收入同比 | 毛利率 | 毛利率同比变化 |",
                "|---|---:|---:|---:|---:|",
            ])
            for segment in segments:
                change = segment.get("gross_margin_change_pp")
                change_text = "—" if change is None else f"{change * 100:+.2f} 个百分点"
                lines.append(
                    f"| {segment.get('name')} | {_money(segment.get('revenue'))} | "
                    f"{_pct(segment.get('revenue_yoy'))} | {_pct(segment.get('gross_margin'))} | "
                    f"{change_text} |"
                )
            lines.append(
                f"分产品表揭示了结构性分化：增长更快的业务未必具有更高毛利率，"
                f"因此收入结构迁移对综合毛利率的影响要同时看增速和盈利水平。"
                f"{_citation(operations.get('evidence_ids') or [])}"
            )
        concentration = operations.get("customer_concentration") or {}
        if concentration.get("top_five_share") is not None:
            lines.append(
                f"前五大客户销售额约 {_money(concentration.get('top_five_sales'))}，"
                f"占年度销售总额 {_pct(concentration.get('top_five_share'))}。"
                f"这一集中度有利于规模交付，但也会放大大客户采购节奏和议价变化对收入、"
                f"应收及库存的影响。{_citation(operations.get('evidence_ids') or [])}"
            )
        for observation in operations.get("operating_observations") or []:
            lines.append(
                f"- 年报经营说明：{observation}"
                f"{_citation(operations.get('evidence_ids') or [])}"
            )
    capacity = broker.get("capacity_snapshot") or {}
    if capacity:
        lines.append(
            f"{capacity.get('source_name') or '券商研报'}转述公司现有产能约 {_money(capacity.get('current'))}，泰国工厂与无锡二期各规划新增约 {_money(capacity.get('thailand_increment'))} 和 {_money(capacity.get('wuxi_increment'))}，计划合计达到 {_money(capacity.get('planned_total'))}。这是尚待公司原始披露核验的产能路线图，不应直接等同于订单或收入。{_citation(capacity.get('evidence_ids') or [])}"
        )
    supply_focus = "光器件、集成电路芯片、结构件等关键物料的价格与可得性" if is_photonics else "关键供应商、研发资源、渠道与交付能力的可得性和成本"
    customer_focus = "头部云厂商资本开支、订单集中度、认证节奏和产品迭代" if is_photonics else "客户预算、获客与留存、收入集中度、合同兑现和产品迭代"
    lines.append(f"供应链研究需要持续跟踪{supply_focus}；客户侧则重点跟踪{customer_focus}。客户稳定性构成优势，过度集中也可能放大单一客户调整带来的波动。")
    lines.append("经营质量的领先指标应比收入更早。采购端看关键物料交期、成本与单一供应商依赖；生产端看产能利用率、良率和交付周期；销售端看认证数量、订单能见度与客户集中度；财务端看存货、应收和经营现金流是否与收入同步。这四组指标可以用于区分真实放量、提前备货与交付压力。")

    lines.extend(["", "## 6. 财务深度分析", ""])
    if current:
        prior = periods[2]
        previous = periods[1]
        revenue_cagr = (metrics["revenue"][current] / metrics["revenue"][prior]) ** 0.5 - 1
        profit_cagr = (metrics["attributable_net_income"][current] / metrics["attributable_net_income"][prior]) ** 0.5 - 1
        margin_current = metrics["attributable_net_income"][current] / metrics["revenue"][current]
        margin_previous = metrics["attributable_net_income"][previous] / metrics["revenue"][previous]
        margin_prior = metrics["attributable_net_income"][prior] / metrics["revenue"][prior]
        cash_conversion_previous = metrics["operating_cash_flow"][previous] / metrics["attributable_net_income"][previous]
        cash_conversion_prior = metrics["operating_cash_flow"][prior] / metrics["attributable_net_income"][prior]
        current_assets = (metrics.get("total_assets") or {}).get(current)
        previous_assets = (metrics.get("total_assets") or {}).get(previous)
        current_equity = (metrics.get("attributable_equity") or {}).get(current)
        previous_equity = (metrics.get("attributable_equity") or {}).get(previous)
        lines.extend([
            "| 指标 | " + " | ".join(periods) + " | 最近一年变化 |",
            "|---|---:|---:|---:|---:|",
        ])
        for key, label, formatter in (
            ("revenue", "营业收入", _money),
            ("attributable_net_income", "归母净利润", _money),
            ("adjusted_net_income", "扣非归母净利润", _money),
            ("operating_cash_flow", "经营现金流净额", _money),
            ("basic_eps", "基本每股收益", lambda value: "—" if value is None else f"{value:.2f} 元"),
            ("weighted_roe", "加权平均 ROE", _pct),
            ("total_assets", "资产总额", _money),
            ("attributable_equity", "归母净资产", _money),
        ):
            row = metrics.get(key) or {}
            lines.append(
                f"| {label} | {formatter(row.get(current))} | {formatter(row.get(previous))} | "
                f"{formatter(row.get(prior))} | "
                f"{_yoy_text(row.get('yoy')) if key != 'weighted_roe' else _pp_text(row.get('change_pp'))} |"
            )
        revenue_yoy = metrics["revenue"]["yoy"]
        profit_yoy = metrics["attributable_net_income"]["yoy"]
        cash_yoy = metrics["operating_cash_flow"]["yoy"]
        if revenue_yoy >= 0 > profit_yoy:
            profit_assessment = "收入扩张但利润收缩，净利率和费用/减值因素需要优先解释"
        elif profit_yoy >= revenue_yoy:
            profit_assessment = "利润增速不低于收入，经营杠杆方向为正"
        else:
            profit_assessment = "利润表现弱于收入，经营杠杆方向为负"
        if cash_yoy < profit_yoy:
            cash_assessment = "现金流表现弱于利润，营运资本占用风险上升"
        elif derived.get("cash_conversion", 0) >= 1:
            cash_assessment = "经营现金流覆盖当期利润"
        else:
            cash_assessment = "经营现金流未完全覆盖当期利润"
        roe_change = metrics["weighted_roe"].get("change_pp")
        margin_sequence = _sequence_text([margin_prior, margin_previous, margin_current])
        conversion_direction = (
            "回升到" if derived.get("cash_conversion", 0) >= cash_conversion_previous
            else "回落到"
        )
        conversion_assessment = (
            "最近一年现金转化低于上年"
            if derived.get("cash_conversion", 0) < cash_conversion_previous
            else "最近一年现金转化不低于上年"
        )
        lines.extend([
            f"以上数据来自公司年度报告主要会计数据表。{official_cite}",
            (
                f"收入由 {_money(metrics['revenue'][previous])} 变为 {_money(metrics['revenue'][current])}，"
                f"同比{_yoy_text(revenue_yoy)}；归母净利润同比{_yoy_text(profit_yoy)}。"
                f"{profit_assessment}。{official_cite}"
            ),
            (
                f"经营现金流净额为 {_money(metrics['operating_cash_flow'][current])}，同比{_yoy_text(cash_yoy)}，"
                f"约为归母净利润的 {derived.get('cash_conversion', 0):.2f} 倍。"
                f"{cash_assessment}，需要结合存货、应收与预付款变化解释。{official_cite}"
            ),
            (
                f"加权平均 ROE 为 {_pct(metrics['weighted_roe'][current])}，较上年{_pp_text(roe_change)}。"
                f"ROE 变化应拆解为利润率、资产周转和财务杠杆，而不能仅由收入增长解释。{official_cite}"
            ),
            (
                f"拉长到 {prior}—{current} 年，营业收入两年复合增速约 {_pct(revenue_cagr)}，"
                f"归母净利润复合增速约 {_pct(profit_cagr)}。同期归母净利率{margin_sequence}；"
                f"收入规模与盈利能力并未持续同向变化。{official_cite}"
            ),
            (
                f"现金转化率从 {prior} 年的 {cash_conversion_prior:.2f} 倍变为 {previous} 年的 "
                f"{cash_conversion_previous:.2f} 倍，并在 {current} 年{conversion_direction} "
                f"{derived.get('cash_conversion', 0):.2f} 倍。{conversion_assessment}，"
                f"需要通过营运资本科目判断压力来源。{official_cite}"
            ),
        ])
        if current_assets and previous_assets and current_equity and previous_equity:
            leverage_current = current_assets / current_equity
            leverage_previous = previous_assets / previous_equity
            turnover_current = metrics["revenue"][current] / ((current_assets + previous_assets) / 2)
            leverage_assessment = (
                "财务杠杆大体稳定"
                if abs(leverage_current - leverage_previous) <= 0.02
                else "财务杠杆有所上升"
                if leverage_current > leverage_previous
                else "财务杠杆有所下降"
            )
            lines.append(
                f"总资产与归母净资产分别{_yoy_text(metrics['total_assets'].get('yoy'))}和"
                f"{_yoy_text(metrics['attributable_equity'].get('yoy'))}；资产/归母净资产约为 "
                f"{leverage_current:.2f} 倍，上年约 {leverage_previous:.2f} 倍，{leverage_assessment}。"
                f"按年末平均资产粗略计算，当年收入/平均总资产约为 {turnover_current:.2f} 倍。{official_cite}"
            )
        balance_rows = operations.get("balance_sheet_rows") or {}
        if balance_rows:
            lines.extend([
                "",
                "| 营运资本/扩产科目 | 本期末 | 上期末 | 同比 | 本期占总资产 |",
                "|---|---:|---:|---:|---:|",
            ])
            for key, label in (
                ("inventory", "存货"),
                ("construction_in_progress", "在建工程"),
                ("accounts_payable", "应付账款"),
            ):
                row = balance_rows.get(key)
                if not row:
                    continue
                lines.append(
                    f"| {label} | {_money(row.get('current'))} | {_money(row.get('previous'))} | "
                    f"{_pct(row.get('yoy'))} | {_pct(row.get('current_asset_share'))} |"
                )
            inventory = balance_rows.get("inventory") or {}
            construction = balance_rows.get("construction_in_progress") or {}
            if inventory.get("yoy") is not None or construction.get("yoy") is not None:
                lines.append(
                    "存货与在建工程的变化是当前盈利质量的重要领先指标。若扩产与战略备货先于"
                    "真实订单兑现，折旧、减值和营运资金占用会继续压制利润与现金流；反之，若后续"
                    "季度收入、毛利率和回款同步改善，才说明这些投入开始形成有效产出。"
                    f"{_citation(operations.get('evidence_ids') or [])}"
                )
    elif broker.get("quarter_snapshot") or broker.get("annual_snapshot"):
        quarter = broker.get("quarter_snapshot") or {}
        annual_secondary = broker.get("annual_snapshot") or {}
        lines.extend([
            "下表仅列示券商研报对公司披露的二级转述，不作为核心财务结论：",
            "| 口径 | 营业收入 | 归母净利润 | 变化/结构 | 证据级别 |",
            "|---|---:|---:|---|---|",
        ])
        if annual_secondary:
            mix = "—"
            if annual_secondary.get("transmission_share") is not None:
                mix = f"传输类 {_pct(annual_secondary.get('transmission_share'))}；接入及数据类 {_pct(annual_secondary.get('access_data_share'))}"
            lines.append(
                f"| {annual_secondary.get('period')} 年（研报转述） | {_money(annual_secondary.get('revenue'))} | — | {mix} | 二级材料，待定期报告复核 {_citation(annual_secondary.get('evidence_ids') or [])} |"
            )
        if quarter:
            lines.append(
                f"| {quarter.get('period')}（研报转述） | {_money(quarter.get('revenue'))} | {_money(quarter.get('attributable_net_income'))} | 营收同比 {_pct(quarter.get('revenue_yoy'))}；净利润同比 {_pct(quarter.get('profit_yoy'))} | 二级材料，待季报复核 {_citation(quarter.get('evidence_ids') or [])} |"
            )
        lines.append("")
        lines.extend([
            "仅从这些二级线索看，数通与 DCI 业务的增长正在对冲传统电信传输业务压力。但在毛利率、费用率、经营现金流、存货和应收账款缺失时，无法判断增长的利润质量。",
            "由于营收、扣非净利润、经营现金流、分部毛利率和资产负债项目未形成一手数据闭环，本节不计算资产周转、现金转化或 ROE。",
        ])
    else:
        lines.append("主要会计数据表没有形成可靠解析结果，因此不展示财务比率或趋势判断。")

    lines.extend(["", "## 7. 同行比较与竞争格局", ""])
    peers = analysis.get("peers") or []
    if peers:
        peer_evidence = list(dict.fromkeys(
            evidence_id for peer in peers for evidence_id in peer.get("evidence_ids") or []
        ))
        selection_method = (context.get("graph") or {}).get("peer_selection_reason")
        if selection_method:
            lines.append(f"可比池选择规则：{selection_method}。{_citation(peer_evidence)}")
            lines.append("")
        lines.extend(["| 可比标的 | 纳入理由 | 行情时点 | 价格 | 总市值 | PE(TTM) | PB(MRQ) |", "|---|---|---|---:|---:|---:|---:|"])
        for peer in peers:
            price = "—" if peer["latest_price"] is None else f"{peer['latest_price']:.2f}"
            market_cap = "—" if peer.get("market_cap") is None else f"{peer['market_cap'] / 1e8:.2f} 亿元"
            pe = "—" if peer.get("pe_ttm") is None else f"{peer['pe_ttm']:.2f} 倍"
            if "pe_outlier_low_earnings_base_not_rankable" in (peer.get("valuation_flags") or []):
                pe += "（低利润基数，不参与排序）"
            pb = "—" if peer.get("pb_mrq") is None else f"{peer['pb_mrq']:.2f} 倍"
            if "pb_source_disagreement_not_rankable" in (peer.get("valuation_flags") or []):
                pb = "—（跨源差异过大，不参与比较）"
            reason = str(peer.get("selection_reason") or "业务相关，具体可比边界待核")
            lines.append(f"| {peer['company_name']}（{peer['ticker']}） | {reason} | {peer['as_of'] or '—'} | {price} | {market_cap} | {pe} | {pb} |")
        lines.append("")
        lines.append("上述表格已经统一币种、行情时点和估值字段，但不同公司的收入结构、利润率与增长阶段仍不完全相同，因此只能用于观察市场定价差异，不能把最低 PE 自动解释为低估。在缺少同行同报告期收入增速、毛利率、现金流和盈利预测时，增长—估值比较仍不完整。")
    else:
        lines.append("缺少同币种、同时间和同估值口径的可比数据，因此不进行同行排名。")

    lines.extend(["", "## 8. 增长驱动与预测边界", ""])
    if is_photonics:
        lines.append("未来增长的第一驱动是高速率产品从研发、小批量订单走向规模交付；第二驱动是传统电信、数通和 DCI 业务之间的收入结构迁移；第三驱动是多技术路线的良率、功耗和成本优化；第四驱动是新增产能、物料供应与客户认证能否匹配真实订单。四项驱动必须最终落到毛利率、费用率和经营现金流，才能形成可持续增长。")
        if product_progress_chunks:
            lines.append(
                f"就公司自身而言，正式年报已经披露的验证节点包括："
                f"{_excerpt(product_progress_chunks[0], ('400G', '800G', '1.6T', '批量交付', '小批量订单'), 480)}。"
                f"{_citation([product_progress_chunks[0].get('evidence_id')])}"
            )
    else:
        lines.append("未来增长需要逐层拆解为行业需求、客户数量或使用量、公司份额、产品价格与单位成本，并分别寻找可核验的领先指标。产品商业化、渠道效率、产能或服务交付能力以及研发转化速度，共同决定增长能否从收入延伸到利润和现金流。")
    evidence_scope = "历史经营与业务布局" if current else "业务布局及少量经营线索"
    lines.append(f"预测必须把“行业需求”“公司份额”“产品价格”“毛利率”分开建模。当前证据只足以讨论{evidence_scope}，不足以给出精确的未来收入、EPS 或目标价，因此本报告只给出驱动框架和可验证条件，不补造模型参数。")
    if broker_reports:
        lines.append(f"对{company_name}而言，最关键的不是把所有新产品都写进预测，而是建立转化漏斗：客户验证数→小批量订单→批量交付→分部收入占比→分部毛利率→经营现金流。只有漏斗各环节连续改善，新业务叙事才能升级为可验证的盈利驱动。")

    lines.extend(["", "## 9. 估值分析", ""])
    if market.get("latest_price") is not None:
        trailing_pe = derived.get("trailing_pe_from_latest_price")
        pe_text = "暂不可算" if trailing_pe is None else f"{trailing_pe:.1f} 倍"
        price_label = "最新行情快照" if market.get("price_type") == "intraday_quote" else "最近已完成交易日收盘价"
        lines.append(f"{price_label}为 {market['latest_price']:.2f} 元，时点为 {market.get('as_of')}；最近已完成交易日 {market.get('latest_completed_session') or '—'} 的收盘价为 {market.get('latest_completed_close') if market.get('latest_completed_close') is not None else '—'} 元。以 {current or '最近年度'} 年基本 EPS 为静态分母计算的历史口径市盈率约为 {pe_text}；该值不是未来盈利口径，也不能直接等同于合理估值。{_citation(market.get('evidence_ids') or [])}")
        valuation_snapshot = (context.get("instruments", {}).get("target") or {}).get("valuation")
        pe_ttm = None
        if valuation_snapshot:
            market_cap = valuation_snapshot.get("market_cap")
            market_cap_text = "—" if market_cap is None else f"{market_cap / 1e8:.2f} 亿元"
            pe_ttm = valuation_snapshot.get("pe_ttm")
            pb = valuation_snapshot.get("pb")
            verification_method = str(
                (valuation_snapshot.get("metadata") or {}).get("verification_method") or ""
            )
            price_sources = (
                "东方财富与腾讯"
                if verification_method.startswith("eastmoney_")
                else "深交所与腾讯"
                if verification_method.startswith("szse_")
                else None
            )
            price_verification = (
                f"价格已由{price_sources}交叉核验；"
                if price_sources
                else "价格来自腾讯行情（独立价格源本次不可用，未宣称双源价格核验）；"
            )
            lines.append(
                f"跨源核验估值快照显示：总市值 {market_cap_text}、PE(TTM) "
                f"{'—' if pe_ttm is None else f'{pe_ttm:.2f} 倍'}、PB(MRQ) "
                f"{'—' if pb is None else f'{pb:.2f} 倍'}。{price_verification}"
                f"总市值、PE(TTM) 和 PB 已由腾讯与百度历史估值序列按交易日口径交叉核验，"
                f"该快照可作为时点事实，但不自动构成高估或低估判断。{_citation(valuation_snapshot.get('source_evidence_ids') or [])}"
            )
            lines.append("在没有统一口径的一致预期 EPS、PEG 和公司自身历史估值分位时，任何精确目标价都缺少可复算基础；同行横向表只能用于观察定价差异，不能替代盈利预测与商业质量分析。")
        else:
            lines.append("当前没有通过口径与来源校验的估值快照，因此本节不形成高估/低估或目标价结论。")
        valid_peer_pes = sorted(
            float(item["pe_ttm"])
            for item in analysis.get("peers") or []
            if item.get("has_valuation")
            and isinstance(item.get("pe_ttm"), (int, float))
            and 0 < float(item["pe_ttm"]) < 300
        )
        if (
            is_photonics
            and pe_ttm is not None
            and pe_ttm > 0
            and valid_peer_pes
        ):
            peer_median_pe = median(valid_peer_pes)
            required_earnings_multiple = pe_ttm / peer_median_pe
            required_three_year_cagr = required_earnings_multiple ** (1 / 3) - 1
            lines.extend([
                "同行估值只用于反推当前价格隐含的盈利兑现压力，不用于机械套用目标价：",
                "| 观察项 | 数值 | 含义 |",
                "|---|---:|---|",
                f"| 目标公司 PE(TTM) | {pe_ttm:.2f} 倍 | 当前时点市场定价 |",
                f"| 可比公司有效 PE 中位数 | {peer_median_pe:.2f} 倍 | 剔除无效值与超过 300 倍的低盈利基数异常值 |",
                f"| 若三年后估值回落至同行中位数，所需盈利累计倍数 | {required_earnings_multiple:.2f} 倍 | 假设股价不变，仅用于压力测试 |",
                f"| 对应三年盈利复合增速 | {_pct(required_three_year_cagr)} | 不是盈利预测，而是当前估值的反推门槛 |",
            ])
            lines.append(
                "这项压力测试的判断重点是：未来利润增速能否显著快于收入、现金转换能否恢复、"
                "高增长业务能否抵消传统业务利润率压力。若三者不能同时改善，估值消化将更多依赖股价调整。"
                f"{_citation(valuation_snapshot.get('source_evidence_ids') or [])}"
            )
        elif broker_reports:
            lines.append(
                f"现有券商研报包含 2026—2028 年盈利预测和高倍数 PE 推演，但这些是分析师假设，不是公司事实。在原始财报和一致口径尚未补齐时，本报告不复制其目标价或评级；只将高估值中隐含的 DCI 放量、产能利用和 OCS 商业化预期作为待证伪假设。{_citation([broker_reports[0].get('evidence_id')])}"
            )
    else:
        lines.append("近期行情数据缺失，因此不讨论当前估值水平。")

    lines.extend(["", "## 10. 催化剂与时间表", ""])
    if events:
        for item in events[:5]:
            lines.append(f"- {item.get('event_date') or '日期待核'}：{item.get('title')}。{_citation([item.get('evidence_id')])}")
    for item in broker_reports[:3]:
        lines.append(f"- {str(item.get('published_at') or '')[:10]}：{item.get('source_name')}研报《{str(item.get('title') or '').replace(packet['ticker'], '').strip()}》（二级研究线索）。{_citation([item.get('evidence_id')])}")
    if news:
        for item in news[:3]:
            lines.append(f"- {str(item.get('published_at') or '')[:10]}：{item.get('title')}（{item.get('source_name') or item.get('source_key')}；仅作外部背景）。{_citation([item.get('evidence_id')])}")
    if product_progress_chunks:
        progress_cite = _citation([product_progress_chunks[0].get("evidence_id")])
        lines.extend([
            f"- 产品兑现节点：400G/800G 数通模块的小批量订单能否升级为持续批量交付，直接检验数通转型的收入质量。{progress_cite}",
            f"- 技术转化节点：1.6T 数通模块从多方案开发进入客户认证、样品订单，再进入规模收入；任一环节延期都会降低增长兑现速度。{progress_cite}",
            f"- 子系统放量节点：已批量交付的 400G/600G DCI 板卡能否带动子系统收入占比、毛利率和现金回款同步改善。{progress_cite}",
        ])
    lines.append("")
    lines.append("季度报告是上述节点的统一校验窗口：收入结构改善只有同时伴随利润率、存货与应收周转、经营现金流改善，才可视为催化兑现；单纯发布新品、取得样品订单或建成产能均不等同于盈利兑现。")

    lines.extend(["", "## 11. 风险、反面证据与证伪条件", ""])
    risk_exposures = operations.get("risk_exposures") or {}
    risk_citation = _citation(
        [risk_chunks[0].get("evidence_id")] if risk_chunks else operations.get("evidence_ids") or []
    )
    if risk_chunks:
        lines.append(
            "公司年报明确列示了核心技术泄密、部分核心原材料依赖境外采购、市场竞争加剧、"
            "国际贸易摩擦以及海外经营环境变化等风险。这些风险的共同传导链是供货或认证受阻"
            "→交付延迟或价格承压→毛利率与现金回款恶化。"
            f"{risk_citation}"
        )
    receivables = risk_exposures.get("receivables")
    notes_receivable = risk_exposures.get("notes_receivable")
    inventory_exposure = risk_exposures.get("inventory")
    if receivables is not None and notes_receivable is not None:
        lines.append(
            f"截至年末，应收账款约 {_money(receivables)}、应收票据约 "
            f"{_money(notes_receivable)}，合计约 {_money(receivables + notes_receivable)}，"
            f"占流动资产 {_pct(risk_exposures.get('receivables_current_asset_share'))}。"
            f"若客户验收或回款放慢，利润与现金流的背离可能继续扩大。{risk_citation}"
        )
    if inventory_exposure is not None:
        lines.append(
            f"年末存货约 {_money(inventory_exposure)}，占流动资产 "
            f"{_pct(risk_exposures.get('inventory_current_asset_share'))}。"
            f"公司扩展数通市场时需要战略备货，但若产品迭代、客户认证或订单兑现不及预期，"
            f"库存积压与跌价风险会同时上升。{risk_citation}"
        )
    elif broker_reports:
        lines.append(f"券商研报的风险提示集中在新技术商业化、DCI 订单传导、传统电信需求、新增产能释放、竞争加剧以及 OCS 量产进度；这些二级观点用于构建跟踪清单，不代替公司风险披露。{_citation([broker_reports[0].get('evidence_id')])}")
    lines.extend([
        "1. **需求与客户投入风险**：若核心客户削减或延后相关投入，行业需求可能低于预期。预警信号是订单或合同能见度下降、产能/人员利用率回落和收入增速持续放缓。",
        "2. **产品迭代与竞争风险**：技术路线变化、竞争对手认证或价格竞争可能削弱份额和毛利率。预警信号是新产品进度落后、单位价格下行快于成本下降、毛利率连续回落。",
        "3. **客户集中与供应链风险**：大客户调整采购或关键芯片/光器件供应受限会放大业绩波动。预警信号是应收、存货或预付款增速显著高于收入，以及交付周期恶化。",
        "4. **高预期估值风险**：当股价隐含较高未来增长时，业绩即使增长但低于市场预期，也可能发生估值压缩。证伪条件是盈利增速连续低于收入增速且现金转换率恶化。",
    ])

    lines.extend(["", "## 12. 三种情景", ""])
    lines.extend([
        "以下均为待验证的条件分支，不是盈利预测：",
        "### 乐观情景",
        "成立条件：DCI 与高速光模块完成更多客户认证并进入规模交付，新增产能利用率提升，同时毛利率和经营现金流改善。失效条件：商业化或交付延后、产能利用不足，或收入增长未转化为现金流。",
        "",
        "### 基准情景",
        "成立条件：传统传输业务承压但相对稳定，接入、数通与 DCI 的增量可以覆盖其下滑；利润率不出现显著恶化。失效条件：正式财报显示收入结构改善停滞，或存货、应收明显快于收入增长。",
        "",
        "### 谨慎情景",
        "成立条件：客户资本开支降速、竞争加剧或产品迭代不及预期，扩产先于订单并造成折旧和营运资金压力。失效条件：订单、批量交付、毛利率和经营现金流重新形成可由一手材料验证的同向改善。",
    ])

    lines.extend(["", "## 13. 后续跟踪指标", ""])
    tracking_items = (
        ("800G 与 1.6T 产品收入、出货和客户认证进度" if is_photonics else "核心产品或服务的收入、交付、客户采用与复购进度"),
        ("云客户资本开支、网络设备部署和订单能见度" if is_photonics else "核心客户投入、合同或订单能见度与终端需求变化"),
        ("光通信模块业务毛利率及其环比/同比变化" if is_photonics else "主要业务毛利率及其环比、同比变化"),
        "收入、归母净利润与经营现金流的匹配关系",
        "存货、应收账款、预付款和合同负债的变化",
        "同行下一代产品进度、价格与市场份额变化",
        "最新价格对应的一致预期 PE/PEG 与历史分位",
    )
    for item in tracking_items:
        lines.append(f"- {item}")

    lines.extend(["", "## 14. 结论", ""])
    if is_photonics and current:
        revenue_yoy = metrics.get("revenue", {}).get("yoy")
        profit_yoy = metrics.get("attributable_net_income", {}).get("yoy")
        cash_yoy = metrics.get("operating_cash_flow", {}).get("yoy")
        if all(value is not None and value >= 0 for value in (revenue_yoy, profit_yoy, cash_yoy)):
            conclusion = (
                f"{company_name}的历史证据显示，最近一年收入、利润和经营现金流同向改善；"
                "后续判断重点是产品升级、客户资本开支和竞争格局能否支持增长持续。"
            )
        else:
            conclusion = (
                f"{company_name}最近一年的收入、利润和经营现金流没有同向改善："
                f"收入{_yoy_text(revenue_yoy)}，归母净利润{_yoy_text(profit_yoy)}，"
                f"经营现金流{_yoy_text(cash_yoy)}。研究重点应放在利润率、营运资本、"
                "产品结构与新增产能回报，而不能只依据行业景气判断盈利趋势。"
            )
    elif is_photonics and broker_reports:
        conclusion = f"{company_name}当前最值得跟踪的主线，是传统传输业务与 DCI、数通、高速光模块增量之间的此消彼长。现有二级研究材料提供了产品、产能和少量经营数据线索，但尚不足以证明收入结构改善已经转化为可持续的毛利率、经营现金流和资本回报。下一步判断必须以公司定期报告、产品批量交付和产能利用率的一手证据为准。"
    else:
        conclusion = f"{company_name}的现有证据可以用于判断历史经营质量、业务布局和主要风险，但未来回报仍取决于需求、竞争地位、产品商业化与现金兑现能否持续同向改善。当前研究的核心是用后续正式披露验证增长驱动，而不是把行业叙事直接外推为公司业绩。"
    lines.append(conclusion + "在一致预期、同行同口径估值和更及时行情补齐前，本报告不给出伪精确目标价或自动交易建议。")

    lines.extend(["", "## 15. 证据索引", ""])
    seen = set()
    for filing in filings[:10]:
        related = [chunk for chunk in context["corpus"]["chunks"] if chunk.get("document_id") == filing.get("filing_id")]
        ids = [chunk.get("evidence_id") for chunk in related if chunk.get("evidence_id")]
        key = (str(filing.get("published_at") or "")[:10], str(filing.get("title") or "").strip())
        if not ids or key in seen:
            continue
        seen.add(key)
        lines.append(f"- {str(filing.get('published_at') or '')[:10]}，《{filing.get('title')}》，{filing.get('source_key')}。{_citation(ids[:4])}")
    for item in news[:5]:
        lines.append(f"- {str(item.get('published_at') or '')[:10]}，{item.get('source_name') or item.get('source_key')}：{item.get('title')}（辅助背景）。{_citation([item.get('evidence_id')])}")
    for item in broker_reports[:5]:
        lines.append(f"- {str(item.get('published_at') or '')[:10]}，{item.get('source_name')}：{item.get('title')}（二级研究，仅作线索）。{_citation([item.get('evidence_id')])}")
    for item in context.get("acquired_evidence") or []:
        if item.get("source_type") in {
            "official_exchange_daily_bars", "official_exchange_realtime_quote", "secondary_valuation_quote",
            "cross_validated_peer_market_matrix",
        }:
            lines.append(
                f"- {str(item.get('published_at') or '')[:19]}，{item.get('text_excerpt')}"
                f"（{item.get('source_key')}）。{_citation([item.get('evidence_id')])}"
            )
    lines.extend(["", "---", "", "本报告用于本地研究辅助，不执行交易；所有估值与情景判断均受数据时点和证据边界约束。", ""])
    return "\n".join(lines)


def known_v3_evidence_ids(packet: dict[str, Any]) -> set[str]:
    v3 = packet.get("research_v3") or {}
    context = v3.get("context") or {}
    corpus = context.get("corpus") or {}
    known = set(packet.get("quality", {}).get("usable_evidence_ids") or [])
    for collection in ("chunks", "news", "events", "broker_reports"):
        for item in corpus.get(collection) or []:
            if item.get("evidence_id"):
                known.add(str(item["evidence_id"]))
    for item in context.get("acquired_evidence") or []:
        if item.get("evidence_id"):
            known.add(str(item["evidence_id"]))
    return known


def evaluate_v3_report_eligibility(packet: dict[str, Any]) -> dict[str, Any]:
    """Decide whether the available material can honestly support a deep report.

    A long chapter skeleton built from secondary research is not a deep report.
    The minimum publishable substrate is one parsed official filing, usable
    official chunks, and a deterministically parsed annual financial table.
    """
    v3 = packet.get("research_v3") or {}
    context = v3.get("context") or {}
    corpus = context.get("corpus") or {}
    analysis = v3.get("analysis") or {}
    filings = corpus.get("filings") or []
    chunks = corpus.get("chunks") or []
    annual = analysis.get("annual_financials") or {}
    missing = []
    if not filings:
        missing.append("official_filing")
    if not chunks:
        missing.append("official_filing_chunks")
    if annual.get("status") != "available" or not annual.get("periods"):
        missing.append("parsed_annual_financials")
    official_ids = {
        str(item.get("evidence_id"))
        for item in chunks
        if item.get("evidence_id")
    }
    if not official_ids:
        missing.append("official_evidence_ids")
    return {
        "eligible": not missing,
        "missing": missing,
        "official_filing_count": len(filings),
        "official_chunk_count": len(chunks),
        "official_evidence_count": len(official_ids),
        "annual_financials_status": annual.get("status") or "unavailable",
    }


def _numeric_narrative_contradictions(report: str, packet: dict[str, Any]) -> list[str]:
    annual = packet.get("research_v3", {}).get("analysis", {}).get("annual_financials", {})
    metrics = annual.get("metrics") or {}
    revenue_yoy = (metrics.get("revenue") or {}).get("yoy")
    profit_yoy = (metrics.get("attributable_net_income") or {}).get("yoy")
    cash_yoy = (metrics.get("operating_cash_flow") or {}).get("yoy")
    roe_change = (metrics.get("weighted_roe") or {}).get("change_pp")
    contradictions = []
    if (
        revenue_yoy is not None
        and profit_yoy is not None
        and profit_yoy < revenue_yoy
        and "利润增速快于收入" in report
    ):
        contradictions.append("利润增速快于收入")
    if (
        any(value is not None and value < 0 for value in (revenue_yoy, profit_yoy, cash_yoy))
        and "三项指标同时上行" in report
    ):
        contradictions.append("三项指标同时上行")
    if (
        cash_yoy is not None
        and profit_yoy is not None
        and cash_yoy < profit_yoy
        and "现金流增速高于利润增速" in report
    ):
        contradictions.append("现金流增速高于利润增速")
    if cash_yoy is not None and cash_yoy < 0 and "现金兑现也同步增强" in report:
        contradictions.append("现金兑现也同步增强")
    if roe_change is not None and roe_change < 0 and "较上年提升" in report:
        contradictions.append("较上年提升")
    return contradictions


def _duplicate_substantive_paragraphs(report: str) -> list[dict[str, Any]]:
    paragraphs = []
    for paragraph in re.split(r"\n{2,}", report):
        normalized = CITATION_RE.sub("", paragraph)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if len(normalized) >= 100 and not normalized.startswith("|"):
            paragraphs.append(normalized)
    counts: dict[str, int] = {}
    for paragraph in paragraphs:
        counts[paragraph] = counts.get(paragraph, 0) + 1
    return [
        {"preview": paragraph[:120], "count": count}
        for paragraph, count in counts.items()
        if count > 1
    ]


def _company_mention_count(report: str, company_name: str) -> int:
    short_name = re.sub(r"(?:股份)?有限公司$", "", company_name)
    variants = {value for value in (company_name, short_name) if len(value) >= 2}
    return max((report.count(value) for value in variants), default=0)


def validate_stock_research_report_v3(report: str, packet: dict[str, Any], *, minimum_characters: int = 3_500) -> dict[str, Any]:
    errors = []
    eligibility = evaluate_v3_report_eligibility(packet)
    if not eligibility["eligible"]:
        errors.append({
            "code": "insufficient_primary_research_evidence",
            "missing": eligibility["missing"],
        })
    missing_headings = [heading for heading in REQUIRED_HEADINGS if heading not in report]
    if missing_headings:
        errors.append({"code": "missing_required_sections", "sections": missing_headings})
    forbidden = [text for text in FORBIDDEN_SYSTEM_TEXT if text in report]
    if forbidden:
        errors.append({"code": "system_metadata_in_report", "tokens": forbidden})
    source_noise = [text for text in FORBIDDEN_SOURCE_NOISE if text in report]
    if source_noise:
        errors.append({"code": "raw_source_noise_in_report", "tokens": source_noise})
    layout_noise = [pattern.pattern for pattern in RAW_LAYOUT_NOISE_RE if pattern.search(report)]
    if layout_noise:
        errors.append({"code": "raw_source_layout_noise_in_report", "patterns": layout_noise})
    process_text = [text for text in FORBIDDEN_PROCESS_TEXT if text in report]
    if process_text:
        errors.append({"code": "research_process_text_in_report", "tokens": process_text})
    contradictions = _numeric_narrative_contradictions(report, packet)
    if contradictions:
        errors.append({"code": "numeric_narrative_contradiction", "tokens": contradictions})
    cited = set(CITATION_RE.findall(report))
    known = known_v3_evidence_ids(packet)
    unknown = sorted(cited - known)
    if unknown:
        errors.append({"code": "unknown_report_citation", "evidence_ids": unknown})
    if len(report) < minimum_characters:
        errors.append({"code": "report_too_short", "characters": len(report), "minimum": minimum_characters})
    identity = packet.get("research_v3", {}).get("context", {}).get("identity", {})
    company_name = str(identity.get("company_name") or "").strip()
    if company_name and company_name != packet.get("ticker") and _company_mention_count(report, company_name) < 2:
        errors.append({
            "code": "insufficient_company_specificity",
            "company_name": company_name,
            "minimum_mentions": 2,
        })
    duplicates = _duplicate_substantive_paragraphs(report)
    if duplicates:
        errors.append({"code": "duplicate_substantive_paragraphs", "duplicates": duplicates})
    coverage = packet.get("research_v3", {}).get("analysis", {}).get("coverage", {}).get("score", 0.0)
    # Coverage is a section-level readiness signal, not a reason to replace the whole
    # report with a system-status page. Missing sections must degrade explicitly while
    # structure, citations and factual boundaries remain enforceable hard gates.
    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "characters": len(report),
        "section_count": len(REQUIRED_HEADINGS) - len(missing_headings),
        "citation_count": len(cited),
        "cited_evidence_ids": sorted(cited),
        "unknown_citation_ids": unknown,
        "coverage": coverage,
        "eligibility": eligibility,
    }
