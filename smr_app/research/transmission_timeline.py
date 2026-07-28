"""
研究信号的「传导时间轴」建模（Transmission Timeline）

功能说明：
    阶段 7「公司信号计划」中最关键的一个模块。
    解决 master plan 阶段 10 的核心痛点：
        新手容易把"样品送测"当成"批量订单落地"，
        把"工厂开业"当成"产能利用+利润兑现"，
        把"上游资本开支"和"公司收入确认"当成同一时间点。

    本模块把三类常见信号链的"先后顺序 + 典型耗时（月）"固化成模板，
    避免研究者跳步。任何一条信号（Signal）都能挂到 Timeline 上，
    并算出：当前进度、落后/超前了多少、下一步是什么、何时会影响利润。

    三类标准传导轴：
        产品认证轴（sample → engineering → certification → vendor code → mass order → revenue）
        工厂产能轴（site_breakground → equipment_install → pilot → ramp_up → utilization70 → profit_contribution）
        上下游订单轴（upstream_capex → vendor_po → company_po → shipment → revenue）

参数说明：
    TimelineNode            - 单个节点（id/中文名/属于哪条轴/典型耗时月/达到条件说明）
    TransmissionTemplate    - 整条传导轴模板（例："800G 光模块产品认证"是一条产品轴）
    TransmissionTimeline    - 单个公司实际运行的时间轴：模板 + 每个节点当前进度 + 证据
    TransmissionEngine      - 核心引擎：
        * build_from_signals()      把 CompanySignalPlan 里的 Signal 映射到节点
        * progress_pct()            算出整轴百分比（0~100%）
        * next_step()               下一步要确认什么
        * months_needed_to_revenue()粗略估算到"利润兑现"还需要几个月
        * diagnose_jumps()          检查有没有跳步（没确认"送测"就当"认证通过"）
        * profit_linkage_summary()  "什么会在什么时间影响利润多少"的小白式解释

返回值说明：
    - progress_pct() -> float（0~100）
    - next_step() -> (next_node_id, need_evidence, reason)
    - diagnose_jumps() -> list[(signal_id, from_node, to_node, reason)]
    - never 抛异常；输入不合法 → 返回 (空列表/0%/警告)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from smr_app.research.signal_registry import (
    CATEGORY_LABELS,
    CompanySignalPlan,
    Signal,
    STATE_DOUBLE_CONFIRM,
    STATE_FIRST_CONFIRM,
    STATE_INVALIDATED,
    STATE_OBSERVING,
    SIGNAL_CATEGORY_FACTORY,
    SIGNAL_CATEGORY_ORDER,
    SIGNAL_CATEGORY_PRODUCT,
    SIGNAL_CATEGORY_UPSTREAM,
)

# 保留引用避免 lint 报无用（CATEGORY_LABELS / SIGNAL_CATEGORY_PRODUCT 供模板节点使用）
_ = (CATEGORY_LABELS, SIGNAL_CATEGORY_PRODUCT)


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class TimelineNode:
    """
    单个传导节点

    字段说明（小白版）：
        node_id      - 节点 ID（例：sample_delivery, certification_pass, mass_order ...）
        name         - 中文名，"样品送测客户"
        axis         - 所属传导轴 id（PRODUCT / FACTORY / UPSTREAM_ORDER）
        axis_label   - 轴的中文名
        order_in_axis- 在轴内的序号（0=最早，数越大越晚）
        typical_months - 达到这个节点一般要花几个月（从轴起点开始算）
        condition    - 达到这个节点需要什么（人话，不是代码判断）
        affects_profit - 到了这个节点，利润会不会开始受影响（0 不影响，1 影响，0.3 部分影响）
        key_category - 对应 signal 的 category（挂信号用）
        keywords     - 关键词列表，signal.name/note 里命中任何一个，就推测挂这个节点
    """
    node_id: str
    name: str
    axis: str
    axis_label: str
    order_in_axis: int
    typical_months: float
    condition: str = ""
    affects_profit: float = 0.0
    key_category: str = ""
    keywords: list[str] = field(default_factory=list)


@dataclass
class TransmissionTemplate:
    """一条完整的传导轴模板（带节点列表 + 模板说明）"""
    template_id: str
    name: str
    axis: str
    description: str = ""
    nodes: list[TimelineNode] = field(default_factory=list)

    def nodes_sorted(self) -> list[TimelineNode]:
        return sorted(self.nodes, key=lambda n: n.order_in_axis)


@dataclass
class NodeProgress:
    """公司实际达到该节点的进度信息（0=没开始，0.5=首次确认，1.0=双变量确认，-1=被证伪）"""
    node_id: str
    state: str = STATE_OBSERVING          # 4 态之一
    state_score: float = 0.0              # 0=没开始, 0.55=首次确认, 1.0=双确认, -1=证伪
    reached: bool = False                 # 是否被视为"已达到"（>=first_confirm 就算）
    reached_at_iso: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    mapped_signal_ids: list[str] = field(default_factory=list)


@dataclass
class TransmissionTimeline:
    """
    单个公司实际运行的传导时间轴

    字段说明：
        ticker / name         - 标的
        template              - 用哪套模板（可以 1 个公司挂多个，这里先简单：1 个 timeline = 1 条模板）
        node_progress         - 每个节点实际进度（dict node_id -> NodeProgress）
        overall_progress_pct  - 整轴进度 0~100
        warnings              - 跳步 / 数据缺口等警告
        notes                 - 给小白看的一句解释（如"还在客户送测阶段，离收入确认还有 12~18 月"）
    """
    ticker: str
    name: str
    template: TransmissionTemplate
    node_progress: dict[str, NodeProgress] = field(default_factory=dict)
    overall_progress_pct: float = 0.0
    warnings: list[str] = field(default_factory=list)
    notes: str = ""


# ============================================================================
# 三套标准传导轴（产品 / 工厂 / 上下游订单）
# ============================================================================

def product_cert_template(name: str = "产品认证→批量订单→收入", template_id: str = "product_cert_std") -> TransmissionTemplate:
    """
    标准「产品认证」传导轴
        样品 → 送测/工程样 → 客户认证/行业认证 → 供应商代码 → 小批量试单 → 批量订单 → 收入确认 → 利润贡献
    """
    nodes = [
        TimelineNode("sample_dev",      "原型/样品开发",           "PRODUCT", "产品", 0, 0,  "公司出 POC 样品，送实验室内部测试",  0.0, keywords=["样品", "原型", "poc", "sample"], key_category=SIGNAL_CATEGORY_PRODUCT),
        TimelineNode("sample_delivery", "客户送测/工程样交付",      "PRODUCT", "产品", 1, 2,  "工程样给客户 A/B test",               0.0, keywords=["送测", "工程样", "demo", "客户测试"], key_category=SIGNAL_CATEGORY_PRODUCT),
        TimelineNode("certification",   "权威认证/客户认证通过",    "PRODUCT", "产品", 2, 5,  "拿到 3GPP/IEEE/客户供应商资质",       0.05,keywords=["认证通过", "资质", "certification", "合规"], key_category=SIGNAL_CATEGORY_PRODUCT),
        TimelineNode("vendor_code",     "进入客户供应商代码清单",   "PRODUCT", "产品", 3, 7,  "客户 ERP 里给分配 vendor code",       0.1, keywords=["供应商代码", "vendor code", "名录", "入围"], key_category=SIGNAL_CATEGORY_ORDER),
        TimelineNode("pilot_order",     "小批量试单（POC 订单）",   "PRODUCT", "产品", 4, 10, "几十万到百万级别试订单",             0.15,keywords=["小批量", "pilot", "试单", "首单"], key_category=SIGNAL_CATEGORY_ORDER),
        TimelineNode("mass_order",      "批量订单（量产）",         "PRODUCT", "产品", 5, 13, "月出货达到设计产能 30%+",            0.5, keywords=["批量", "量产", "mass order", "大单"], key_category=SIGNAL_CATEGORY_ORDER),
        TimelineNode("revenue_confirm", "财报/调研确认收入",        "PRODUCT", "产品", 6, 16, "公司披露收入占比/券商拆分确认",      0.85,keywords=["收入确认", "营收占比", "财报", "拆分"], key_category=SIGNAL_CATEGORY_ORDER),
        TimelineNode("profit_contrib",  "对利润产生显著贡献",       "PRODUCT", "产品", 7, 20, "毛利贡献 >5% 或 净利 >3%",            1.0, keywords=["利润贡献", "毛利贡献", "净利率", "贡献利润"], key_category=SIGNAL_CATEGORY_ORDER),
    ]
    return TransmissionTemplate(
        template_id=template_id,
        name=name,
        axis="PRODUCT",
        description="样品 → 客户送测 → 认证 → 供应商代码 → 小批量 → 批量 → 收入 → 利润",
        nodes=nodes,
    )


def factory_capacity_template(name: str = "工厂→产能爬坡→盈利", template_id: str = "factory_cap_std") -> TransmissionTemplate:
    """
    标准「工厂产能」传导轴
        拿地/奠基 → 设备安装 → 试产 → 爬坡 → 利用率 70% → 盈利贡献
    """
    nodes = [
        TimelineNode("ground_break",  "拿地/奠基/签约",         "FACTORY", "工厂", 0, 0,  "官宣建厂，或与地方签约",         0.0, keywords=["签约", "奠基", "拿地", "规划"], key_category=SIGNAL_CATEGORY_FACTORY),
        TimelineNode("equip_install", "设备进场/安装",           "FACTORY", "工厂", 1, 6,  "产线设备到位、调试",            0.0, keywords=["设备", "安装", "调试", "进场"], key_category=SIGNAL_CATEGORY_FACTORY),
        TimelineNode("pilot_run",     "试产（良率验证）",         "FACTORY", "工厂", 2, 10, "首批产品下线，良率 50% 以下",     0.05,keywords=["试产", "下线", "良率", "首件"], key_category=SIGNAL_CATEGORY_FACTORY),
        TimelineNode("ramp_up",       "产能爬坡",                "FACTORY", "工厂", 3, 14, "产能从 10% 爬升到 50%",          0.2, keywords=["爬坡", "产能", "月出货"], key_category=SIGNAL_CATEGORY_FACTORY),
        TimelineNode("util_70",       "利用率 >70%",             "FACTORY", "工厂", 4, 18, "持续 2 个季度产能利用率 ≥70%",  0.55,keywords=["利用率 70", "满载", "稼动"], key_category=SIGNAL_CATEGORY_FACTORY),
        TimelineNode("profit_contrib","工厂对利润显著贡献",       "FACTORY", "工厂", 5, 24, "事业部/公司披露工厂盈利",       1.0, keywords=["工厂盈利", "盈亏平衡", "贡献利润"], key_category=SIGNAL_CATEGORY_FACTORY),
    ]
    return TransmissionTemplate(
        template_id=template_id,
        name=name,
        axis="FACTORY",
        description="拿地/签约 → 设备安装 → 试产 → 爬坡 → 利用率70% → 工厂盈利",
        nodes=nodes,
    )


def upstream_order_template(name: str = "上游→系统商→公司订单→出货→收入", template_id: str = "upstream_order_std") -> TransmissionTemplate:
    """
    标准「上下游订单传导」轴
        上游 Capex → 系统商/大客户 PO → 公司采购 PO → 出货 → 收入确认
    """
    nodes = [
        TimelineNode("upstream_capex", "上游/终端客户官宣资本开支",  "UPSTREAM", "订单", 0, 0,  "英伟达/三大运营商/云厂宣布扩产", 0.0, keywords=["资本开支", "capex", "扩产", "招标"], key_category=SIGNAL_CATEGORY_UPSTREAM),
        TimelineNode("system_vendor_po","系统商/客户下大订单",        "UPSTREAM", "订单", 1, 4, "华为/浪潮/运营商集采公示中标",    0.05,keywords=["集采", "中标", "系统商订单", "框架采购"], key_category=SIGNAL_CATEGORY_UPSTREAM),
        TimelineNode("company_po",      "公司收到正式 PO",           "UPSTREAM", "订单", 2, 6, "公司公告重大合同/投资者调研口径",  0.2, keywords=["PO", "采购订单", "合同", "在手订单"], key_category=SIGNAL_CATEGORY_ORDER),
        TimelineNode("shipment",        "公司开始批量出货",          "UPSTREAM", "订单", 3, 9, "调研口径：出货量 X 万/月",        0.55,keywords=["出货", "月出货", "交付"], key_category=SIGNAL_CATEGORY_ORDER),
        TimelineNode("revenue_confirm", "收入确认（财报口径）",       "UPSTREAM", "订单", 4, 12,"季度披露/券商拆分",               0.85,keywords=["收入", "营收", "季度", "拆分"], key_category=SIGNAL_CATEGORY_ORDER),
        TimelineNode("profit_contrib",  "对利润有显著贡献",          "UPSTREAM", "订单", 5, 15,"毛利贡献 >5% / 净利贡献 >3%",     1.0, keywords=["利润贡献", "净利贡献"], key_category=SIGNAL_CATEGORY_ORDER),
    ]
    return TransmissionTemplate(
        template_id=template_id,
        name=name,
        axis="UPSTREAM",
        description="上游Capex → 系统商订单 → 公司PO → 出货 → 收入 → 利润",
        nodes=nodes,
    )


# ============================================================================
# 核心引擎
# ============================================================================

class TransmissionEngine:
    """
    传导时间轴引擎

    小白讲解：
        1) 你给我一个 CompanySignalPlan（一整个公司的信号清单）+ 1 个 template
        2) 我把每条信号自动"挂"到合适的节点上（按关键词 + category 匹配）
        3) 算出进度百分比、下一步是什么、有没有"跳步"（没送测就吹批量）
        4) 最后给你一句人话解释："现在还在客户送测，离利润大概还有 14~18 个月"
    """

    TEMPLATES = {
        "product":  product_cert_template,
        "factory":  factory_capacity_template,
        "upstream": upstream_order_template,
    }

    @staticmethod
    def _score_state(state: str) -> float:
        """把 4 态（来自 signal_registry）转成 0~1 分；证伪返回 -1"""
        return {
            STATE_OBSERVING: 0.0,
            STATE_FIRST_CONFIRM: 0.55,
            STATE_DOUBLE_CONFIRM: 1.0,
            STATE_INVALIDATED: -1.0,
        }.get(state, 0.0)

    @classmethod
    def build(
        cls,
        plan: CompanySignalPlan,
        template: TransmissionTemplate,
    ) -> TransmissionTimeline:
        """
        把公司信号计划 挂到 模板 → 形成实际运行的 timeline

        参数：
            plan     - CompanySignalPlan，某公司的整套信号
            template - 选上面三套 standard template 之一（或自定义）
        返回 TransmissionTimeline，永远非 None
        """
        tl = TransmissionTimeline(
            ticker=plan.ticker,
            name=plan.name,
            template=template,
        )
        # 1) 为每个节点建立 NodeProgress（初始 observing / 0）
        for node in template.nodes_sorted():
            tl.node_progress[node.node_id] = NodeProgress(
                node_id=node.node_id,
                state=STATE_OBSERVING,
                state_score=0.0,
                reached=False,
            )
        # 2) 把每条 Signal 挂到最合适的节点
        for sig in plan.signals:
            target = cls._pick_node(sig, template)
            if target is None:
                tl.warnings.append(f"信号 {sig.signal_id!r} 未匹配到传导节点（忽略但保留）")
                continue
            prog = tl.node_progress[target.node_id]
            prog.mapped_signal_ids.append(sig.signal_id)
            # 合并 evidence ids
            for ev in sig.evidence:
                if ev.evidence_id and ev.evidence_id not in prog.evidence_ids:
                    prog.evidence_ids.append(ev.evidence_id)
            # 状态合并（两条里取更高；invalidated 覆盖一切）
            new_score = cls._score_state(sig.current_state)
            if new_score < 0:
                prog.state = STATE_INVALIDATED
                prog.state_score = -1.0
                prog.reached = False
            elif new_score > prog.state_score:
                prog.state_score = new_score
                prog.state = sig.current_state
                prog.reached = prog.state_score >= 0.5  # 首次确认以上视为"已达到"
                prog.reached_at_iso = sig.last_updated_at or prog.reached_at_iso
        # 3) 算整体进度
        tl.overall_progress_pct = cls._calc_progress(tl, template)
        # 4) 算诊断（跳步）
        tl.warnings.extend(cls._diagnose_jumps(tl, template))
        # 5) 人话注释
        tl.notes = cls._summary(tl, template)
        return tl

    # ------------------------------------------------------------------
    # 信号→节点 匹配
    # ------------------------------------------------------------------
    @staticmethod
    def _pick_node(sig: Signal, template: TransmissionTemplate) -> Optional[TimelineNode]:
        """根据 signal 的 category + name/note 关键词，找最佳匹配节点"""
        text_pool = (sig.name + " " + sig.note + " " + sig.signal_id).lower()
        cat = sig.category
        candidates: list[tuple[int, TimelineNode]] = []  # (score, node)
        for node in template.nodes:
            score = 0
            if node.key_category and cat == node.key_category:
                score += 2
            for kw in node.keywords:
                if kw.lower() in text_pool:
                    score += 1
            if score > 0:
                candidates.append((score, node))
        if not candidates:
            return None
        candidates.sort(key=lambda t: t[0], reverse=True)
        return candidates[0][1]

    # ------------------------------------------------------------------
    # 进度 0~100%
    # ------------------------------------------------------------------
    @staticmethod
    def _calc_progress(tl: TransmissionTimeline, tmpl: TransmissionTemplate) -> float:
        """按节点权重(affects_profit + 固定均分)算整体进度；-1 的 invalidated 计 0"""
        nodes = tmpl.nodes_sorted()
        if not nodes:
            return 0.0
        eq_w = 1.0 / len(nodes)
        total_profit_w = sum(n.affects_profit for n in nodes) or 1.0
        score = 0.0
        for n in nodes:
            prog = tl.node_progress[n.node_id]
            s = max(0.0, prog.state_score)  # invalidated 不会让进度为负
            profit_w = n.affects_profit / total_profit_w
            w = 0.5 * eq_w + 0.5 * profit_w
            score += w * s
        return round(score * 100.0, 1)

    # ------------------------------------------------------------------
    # 跳步诊断（防"没送测就吹批量"）
    # ------------------------------------------------------------------
    @staticmethod
    def _diagnose_jumps(tl: TransmissionTimeline, tmpl: TransmissionTemplate) -> list[str]:
        """
        跳步 = 后面节点达到了，但它前面某个必要节点还没到 首次确认

        例：mass_order 已首次确认，但 sample_delivery 还是 0 → 跳步警告
        """
        warns: list[str] = []
        nodes = tmpl.nodes_sorted()
        reached_indices = [i for i, n in enumerate(nodes) if tl.node_progress[n.node_id].reached]
        if not reached_indices:
            return warns
        last_reached = max(reached_indices)
        for i in range(0, last_reached):
            prev = nodes[i]
            prog = tl.node_progress[prev.node_id]
            if not prog.reached and prog.state != STATE_INVALIDATED:
                later = nodes[last_reached]
                sigs = ", ".join(tl.node_progress[later.node_id].mapped_signal_ids) or "(无)"
                warns.append(
                    f"⚠️ 疑似跳步：{later.name}({later.node_id})已达到，但前面 "
                    f"[{prev.name}({prev.node_id})]还没确认；映射信号={sigs}。"
                    "请补充前置节点证据。"
                )
        return warns

    # ------------------------------------------------------------------
    # 下一步 + 利润兑现估算
    # ------------------------------------------------------------------
    @staticmethod
    def next_step(tl: TransmissionTimeline) -> tuple[str, str, str]:
        """
        返回 (下一个节点ID, 需要什么证据, 人话解释)
        没信号时就从第一个节点开始；已经全部 100% → (最后节点ID, "维持", "传导已完成，观察持续性")
        """
        nodes = tl.template.nodes_sorted()
        for n in nodes:
            prog = tl.node_progress[n.node_id]
            if not prog.reached and prog.state != STATE_INVALIDATED:
                return (
                    n.node_id,
                    n.condition or f"至少 1 条权威证据支持「{n.name}」",
                    f"下一步要确认「{n.name}」；若不先确认，后续节点可信度不足。",
                )
        last = nodes[-1]
        return (last.node_id, "维持跟踪+验证可持续性", "整条传导已完成，需持续跟踪持续性与利润率。")

    @staticmethod
    def months_needed_to_profit(tl: TransmissionTimeline) -> Optional[float]:
        """粗略估算到「利润贡献节点」还剩几个月（模板典型月差，不够精准但足够排优先级）"""
        profit_node = None
        for n in tl.template.nodes_sorted():
            if n.affects_profit >= 1.0:
                profit_node = n
                break
        if profit_node is None:
            return None
        nodes = tl.template.nodes_sorted()
        reached_idx = -1
        for i, n in enumerate(nodes):
            if tl.node_progress[n.node_id].reached:
                reached_idx = i
        if reached_idx < 0:
            return round(profit_node.typical_months, 1)
        cur_node = nodes[reached_idx]
        remain = max(0.0, profit_node.typical_months - cur_node.typical_months)
        return round(remain, 1)

    @staticmethod
    def profit_linkage_summary(tl: TransmissionTimeline) -> str:
        """一句话小白式解释："哪些节点会影响利润、影响多少" """
        parts = []
        for n in tl.template.nodes_sorted():
            if n.affects_profit <= 0:
                continue
            prog = tl.node_progress[n.node_id]
            pct_label = f"{n.affects_profit * 100:.0f}%"
            if prog.reached:
                status = "✅已达"
            elif prog.state == STATE_INVALIDATED:
                status = "❌证伪"
            else:
                status = "⏳未达"
            parts.append(f"{status} 「{n.name}」→ 利润影响{pct_label}")
        if not parts:
            return "本传导模板暂未定义利润影响节点。"
        return "；".join(parts)

    @staticmethod
    def _summary(tl: TransmissionTimeline, tmpl: TransmissionTemplate) -> str:
        """总体注释（给小白看）"""
        progress = tl.overall_progress_pct
        remain = TransmissionEngine.months_needed_to_profit(tl)
        nid, need, _ = TransmissionEngine.next_step(tl)
        node_name = next((n.name for n in tmpl.nodes if n.node_id == nid), "(未知)")
        msg = f"进度 {progress:.1f}%；下一步：「{node_name}」（需要{need[:20]}…）"
        if remain is not None:
            if remain <= 0:
                msg += "；传导已到利润贡献期，重点跟踪持续性"
            else:
                msg += f"；距「显著利润贡献」预估还需 ≈{remain:.0f} 个月"
        if tl.warnings:
            msg += f"；⚠️ {len(tl.warnings)} 条警告（疑似跳步/缺口）"
        return msg
