"""
研究信号注册表（Signal Registry）+ 4 态状态机

功能说明：
    阶段 7「公司信号计划 V1」的核心数据结构模块。
    解决：工厂开业 ≠ 产能利用 ≠ 利润兑现；样品 ≠ 送测 ≠ 认证 ≠ 供应商代码 ≠ 批量订单 ≠ 收入确认。
    每个信号（signal）有 4 个状态（4 态机，源自 master plan 阶段 10 验收）：
        observing  - 观察期：只看到了一些传闻/预告，没有过硬证据
        first_confirm - 首次确认：至少有 1 条权威源硬证据
        double_confirm - 双变量确认：2 个独立信号源 + 1 条交叉验证（例：工厂开业 + 首批出货）
        invalidated  - 证伪：证据出现反转（例：官方说认证被驳回）
    另外支持领先 / 滞后 / 同步指标分类，避免"把滞后指标当成领先指标"的经典错误。

参数说明：
    SignalThreshold         - 触发/失效阈值（支持数值区间、事件、日期等）
    Signal                  - 单条信号结构（id / 名称 / 类别 / 当前态 / 阈值 / 监测频率 ...）
    CompanySignalPlan       - 单个公司的整套信号计划
    SignalStateMachine      - 4 态机：提供 try_transition()，按规则 + 证据 切状态
    SignalRegistry          - 对整套计划做：增、查、状态快照、批量打分

返回值说明：
    - CompanySignalPlan：一整个公司的信号集合 + 当前态分布 + 总体信心度
    - SignalStateMachine.try_transition：返回 (success_bool, 新状态, 理由)
    - never 抛异常；非法 transition 返回 False + 旧状态 + "为什么不能切"

异常处理：
    - 缺失 evidence / 重复 transition → 不抛异常，返回 (False, 旧状态, 详细理由)
    - 任意参数类型错 → 内部 try/except + 降级（不会让整个工作流崩）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


# ============================================================================
# 4 态枚举（字符串形式，避免 Python Enum 在 JSON 里的麻烦）
# ============================================================================

STATE_OBSERVING = "observing"            # 观察期
STATE_FIRST_CONFIRM = "first_confirm"    # 首次确认
STATE_DOUBLE_CONFIRM = "double_confirm"  # 双变量确认
STATE_INVALIDATED = "invalidated"        # 证伪

STATE_ORDER = {
    STATE_OBSERVING: 0,
    STATE_FIRST_CONFIRM: 1,
    STATE_DOUBLE_CONFIRM: 2,
    STATE_INVALIDATED: 3,
}

STATE_LABELS = {
    STATE_OBSERVING: "观察期",
    STATE_FIRST_CONFIRM: "首次确认",
    STATE_DOUBLE_CONFIRM: "双变量确认",
    STATE_INVALIDATED: "已证伪",
}

# 指标分类：leading(领先) / coincident(同步) / lagging(滞后)
IND_LEADING = "leading"
IND_COINCIDENT = "coincident"
IND_LAGGING = "lagging"

IND_LABELS = {
    IND_LEADING: "领先指标",
    IND_COINCIDENT: "同步指标",
    IND_LAGGING: "滞后指标",
}

# 信号大类（小白一眼看懂：这是什么类型的信号）
SIGNAL_CATEGORY_PRODUCT = "产品/认证"      # 样品 / 送测 / 认证 / 供应商代码
SIGNAL_CATEGORY_ORDER = "订单/出货"        # 批量订单 / 出货 / 收入确认
SIGNAL_CATEGORY_FACTORY = "工厂/产能"       # 工厂开业 / 试产 / 爬坡 / 利用率 / 盈利
SIGNAL_CATEGORY_UPSTREAM = "上游传导"       # 上游资本开支 / 系统商订单
SIGNAL_CATEGORY_PRICE = "价格/估值"         # PE / PB / 换手 / 相对强度
SIGNAL_CATEGORY_MANAGEMENT = "经营/治理"    # 管理层 / 定增 / 回购 / 机构调研
SIGNAL_CATEGORY_MACRO = "宏观/政策"         # 补贴 / 关税 / 行业准入

CATEGORY_LABELS = {
    SIGNAL_CATEGORY_PRODUCT: "产品/认证",
    SIGNAL_CATEGORY_ORDER: "订单/出货",
    SIGNAL_CATEGORY_FACTORY: "工厂/产能",
    SIGNAL_CATEGORY_UPSTREAM: "上游传导",
    SIGNAL_CATEGORY_PRICE: "价格/估值",
    SIGNAL_CATEGORY_MANAGEMENT: "经营/治理",
    SIGNAL_CATEGORY_MACRO: "宏观/政策",
}


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class EvidenceSnippet:
    """
    支持信号状态的"证据片段"（每一条信号状态切换，必须有 evidence_id 可追溯）

    字段说明（小白版）：
        evidence_id   - 证据 ID，对应 ArtifactStore 里的硬证据文件，例如 ev_20260723_dcu_cert
        source        - 来源类型（巨潮公告 / 公司官网 / 权威媒体 / 调研纪要 ...）
        published_at  - 发布时间 ISO
        summary       - 一句话摘要（小白能看，比如"深算四号完成生态适配"）
        authority_tier - 权威等级（1 最权威 → 4 最低）
    """
    evidence_id: str
    source: str = ""
    published_at: str = ""
    summary: str = ""
    authority_tier: int = 4


@dataclass
class SignalThreshold:
    """
    触发 / 失效阈值

    字段说明（小白版）：
        trigger             - 触发条件（从 observing → first_confirm 需要什么发生）
                              支持三种：数值(value_gte/value_lte/value_in_range)、
                              事件(event_happened)、日期(after_date)
        invalidate          - 证伪条件（一旦发生，直接切到 invalidated，无论当前态）
        double_confirm_cond - 进入 double_confirm 需要的额外条件（第二路独立验证）
        frequency           - 监测频率（实时 / 每日 / 每周 / 每月 / 每季财报后）
        expire_after        - 信号过期时间 ISO（到期了还没确认就降级）
    """
    trigger: dict = field(default_factory=dict)
    invalidate: dict = field(default_factory=dict)
    double_confirm_cond: dict = field(default_factory=dict)
    frequency: str = "每周"
    expire_after: str = ""


@dataclass
class Signal:
    """
    一条信号

    字段说明（小白版，对照 master plan 阶段 10 验收）：
        signal_id             - ID，如 "dco_800g_certification"
        name                  - 中文名，如"800G 相干认证通过"
        category              - 信号大类（产品/订单/工厂...）
        indicator_kind        - 领先 / 同步 / 滞后
        current_state         - 当前态（4 态机）
        thresholds            - 触发 / 失效阈值
        evidence              - 已收集证据片段（每条可追溯到 artifact）
        transmission_order    - 在传导时间轴上的先后序号（0=最早，数越大越靠后）
        expected_months_delay - 该信号相对"主题启动"的预期延迟（月数，用于判断是不是太慢）
        importance            - 重要度 0~1（1 = 最关键，建仓信号）
        note                  - 备注
        invalidated_reason    - 如果 state=invalidated，写清楚为什么被证伪
        last_updated_at       - 最后一次更新 ISO
    """
    signal_id: str
    name: str
    category: str = SIGNAL_CATEGORY_PRODUCT
    indicator_kind: str = IND_LEADING
    current_state: str = STATE_OBSERVING
    thresholds: SignalThreshold = field(default_factory=SignalThreshold)
    evidence: list[EvidenceSnippet] = field(default_factory=list)
    transmission_order: int = 0
    expected_months_delay: int = 0
    importance: float = 0.5
    note: str = ""
    invalidated_reason: str = ""
    last_updated_at: str = ""


@dataclass
class CompanySignalPlan:
    """
    单个公司的整套信号计划

    字段说明：
        ticker / name       - 标的
        plan_id             - 本次计划 ID（可用于 memory persistence 归档）
        signals             - 信号列表
        state_summary       - 每态多少条 {observing: 3, first_confirm: 2 ...}
        overall_confidence  - 总体信心度（先按 importance 加权，再根据"是否过早建仓"打折扣）
        building_position_ready - 是否已经到了"可考虑建仓"的点（至少 2 条 double_confirm 重要领先指标 & 无关键 invalidated）
        created_at          - ISO
    """
    ticker: str
    name: str = ""
    plan_id: str = ""
    signals: list[Signal] = field(default_factory=list)
    state_summary: dict = field(default_factory=dict)
    overall_confidence: float = 0.0
    building_position_ready: bool = False
    created_at: str = ""


# ============================================================================
# 4 态状态机
# ============================================================================

class SignalStateMachine:
    """
    研究信号 4 态机

    允许的转移（顺序 / 条件）：
        observing     → first_confirm   : 至少 1 条权威 evidence + trigger 条件满足
        first_confirm → double_confirm  : 额外 1 条"独立来源"evidence + double_confirm_cond 满足
        first_confirm → invalidated     : invalidate 条件命中
        double_confirm → invalidated    : invalidate 条件命中
        observing     → invalidated     : invalidate 条件命中（项目刚开始就被证伪，也得允许）
    其他任何转移（例如 observing → double_confirm 跳步）都 **不允许**，防止"一步到位=一步翻车"。

    每条非法转移都会返回 (False, 原状态, "原因说明")，而不是抛异常。
    """

    ALLOWED_TRANSITIONS: set[tuple[str, str]] = {
        (STATE_OBSERVING, STATE_FIRST_CONFIRM),
        (STATE_FIRST_CONFIRM, STATE_DOUBLE_CONFIRM),
        (STATE_OBSERVING, STATE_INVALIDATED),
        (STATE_FIRST_CONFIRM, STATE_INVALIDATED),
        (STATE_DOUBLE_CONFIRM, STATE_INVALIDATED),
    }

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def try_transition(
        cls,
        signal: Signal,
        target_state: str,
        evidence: Optional[EvidenceSnippet] = None,
        reason: str = "",
        independent_from_existing: bool = False,
    ) -> tuple[bool, str, str]:
        """
        尝试把 signal 的当前态 → target_state

        参数：
            signal               - 要转移的信号对象（会原地修改 current_state / evidence）
            target_state         - 目标态（4 态之一）
            evidence             - 本次转移附带的证据片段（建议所有转移都要有；首次 / 双确认必须有）
            reason               - 一句话文字理由
            independent_from_existing - True=这条 evidence 来源和 signal.evidence 中已有来源不同
                                        （用于 double_confirm 的"独立来源"要求）

        返回 (是否成功, 新状态字符串, 原因说明)
        """
        try:
            cur = signal.current_state
            if target_state not in STATE_ORDER:
                return False, cur, f"非法目标态 target_state={target_state!r}"

            pair = (cur, target_state)
            if pair not in cls.ALLOWED_TRANSITIONS:
                return False, cur, (
                    f"状态机不允许从 {STATE_LABELS.get(cur, cur)}"
                    f" 直接跳到 {STATE_LABELS.get(target_state, target_state)}"
                    f"（防止跳步=翻车，先补齐前序证据）"
                )

            # → first_confirm 必须有 1 条证据
            if target_state == STATE_FIRST_CONFIRM and evidence is None:
                return False, cur, "从 observing → first_confirm 必须附带至少 1 条 EvidenceSnippet"

            # → double_confirm 必须：独立证据 + independent_from_existing
            if target_state == STATE_DOUBLE_CONFIRM:
                if evidence is None:
                    return False, cur, "进入 double_confirm 必须附带来自独立来源的证据"
                if not independent_from_existing and len(signal.evidence) > 0:
                    return False, cur, (
                        "进入 double_confirm 必须标记 evidence 为 independent_from_existing=True"
                        "（需要第二路独立验证，避免同源重复计入）"
                    )

            # → invalidated 强制写 invalidated_reason
            if target_state == STATE_INVALIDATED and not (reason or signal.invalidated_reason):
                return False, cur, "进入 invalidated 必须填 reason（写清楚为什么证伪）"

            # 校验通过 → 应用转移
            if evidence is not None:
                signal.evidence.append(evidence)
            if target_state == STATE_INVALIDATED:
                signal.invalidated_reason = reason or signal.invalidated_reason or "证据反转"
            signal.last_updated_at = cls._now_iso()
            signal.current_state = target_state
            return True, target_state, (reason or "状态转移成功")
        except Exception as e:  # 任何异常都兜住
            return False, signal.current_state, f"状态机异常（已兜底，不抛）：{type(e).__name__}: {e}"


# ============================================================================
# 信号计划构建 / 汇总（CompanySignalPlan 总体统计）
# ============================================================================

class SignalRegistry:
    """
    信号计划总装器：给单个公司构建/维护整个 SignalPlan

    小白讲解：
        这是"整份作战计划书"的装订处。你把一条条信号加进来，
        它自动算出：每态几条、总体信心度、"是不是已经可以考虑建仓了"。
    """

    @staticmethod
    def build_plan(
        ticker: str,
        name: str = "",
        signals: Optional[list[Signal]] = None,
        plan_id: str = "",
    ) -> CompanySignalPlan:
        """构建整个 CompanySignalPlan，并计算 state_summary / confidence / ready"""
        plan = CompanySignalPlan(
            ticker=ticker,
            name=name,
            plan_id=plan_id or f"signal_plan_{ticker}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            signals=list(signals or []),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        SignalRegistry.recompute_summary(plan)
        return plan

    @staticmethod
    def recompute_summary(plan: CompanySignalPlan) -> None:
        """重新计算：state_summary / confidence / building_position_ready（状态变了就跑一次）"""
        summary = {k: 0 for k in STATE_ORDER.keys()}
        total_importance = 0.0
        weighted_score = 0.0
        key_invalid = 0
        key_double = 0

        for s in plan.signals:
            summary[s.current_state] = summary.get(s.current_state, 0) + 1
            w = max(0.0, min(1.0, float(s.importance)))
            total_importance += w
            # 每态的分数（observing=0.2, first=0.55, double=1.0, invalidated=0）
            score = {
                STATE_OBSERVING: 0.2,
                STATE_FIRST_CONFIRM: 0.55,
                STATE_DOUBLE_CONFIRM: 1.0,
                STATE_INVALIDATED: 0.0,
            }.get(s.current_state, 0.0)
            weighted_score += w * score
            if w >= 0.7:  # 关键信号（importance ≥ 0.7）
                if s.current_state == STATE_DOUBLE_CONFIRM:
                    key_double += 1
                if s.current_state == STATE_INVALIDATED:
                    key_invalid += 1

        plan.state_summary = summary
        plan.overall_confidence = 0.0 if total_importance <= 0 else round(
            weighted_score / total_importance, 3,
        )
        # 建仓准备度：≥ 2 条关键信号进入 double_confirm 且没有关键信号被证伪
        plan.building_position_ready = (key_double >= 2) and (key_invalid == 0)
