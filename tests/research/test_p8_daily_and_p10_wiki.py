"""
阶段 8 + 阶段 10 单文件测试

直接运行：python tests/research/test_p8_daily_and_p10_wiki.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smr_app.research.daily_signal_integration import (  # noqa: E402
    DailyDraftEngine, SignalEntry, WikiDraft,
    DRAFT_TYPE_FACT, DRAFT_TYPE_THESIS, DRAFT_TYPE_RISK_CASE,
    DRAFT_TYPE_CATALYST, DRAFT_TYPE_STRATEGY, DRAFT_TYPE_DECISION,
)
from smr_app.research.weekly_compression import (  # noqa: E402
    WeeklyCompressor, StableKnowledgeObject,
)
from smr_app.research.wiki_knowledge_base import (  # noqa: E402
    SourceManifest, SourceManifestEntry, IngestDraft, ReviewQueue,
    WikiEntry, WikiGovernanceService, WikiLinter,
    GOVERNANCE_STATUS_READY, GOVERNANCE_STATUS_REVIEW_REQUIRED,
    GOVERNANCE_STATUS_BLOCKED,
    APPROVAL_AUTO_READY, APPROVAL_PENDING, APPROVAL_APPROVED,
    APPROVAL_REJECTED, APPROVAL_REOPENED,
    WIKI_STATUS_ACTIVE, WIKI_STATUS_STALE,
)

_FAIL = 0
_PASS = 0


def _check(name, ok, d=""):
    global _FAIL, _PASS
    if ok:
        _PASS += 1
        print(f"  [PASS] {name}" + (f" — {d}" if d else ""))
    else:
        _FAIL += 1
        print(f"  [FAIL] {name}" + (f" — {d}" if d else ""))


# ============================================================================
# 阶段 8-1：日报 → 信号抽提 + 自动 draft（验收：1 个完整交易日 → 新增可审核知识草稿）
# ============================================================================
def case_p8_daily_engine():
    print("\n=== 阶段 8-1：日报高价值结论抽提（DCI + 星网锐捷样例） ===")

    daily_report = {
        "report_id": "daily_20260723",
        "theme": "DCI",
        "sections": {
            "市场流水账": [
                "今日沪指涨 0.3%，北向资金流出 20 亿，成交额 9800 亿",  # 纯流水 → 低分
                "尾盘创业板指拉升",  # 流水
            ],
            "研究结论": [
                {
                    "entity_key": "DCI",
                    "text": "DCI 需求真实，但 A 股映射不纯（龙头 DCI 业务 30%~45%）+ AI 算力吸金 → 行情滞后",
                    "evidence_ids": ["ev_dci_alliance_q1", "ev_cninf_tender"],
                },
                {
                    "entity_key": "688041.SH",
                    "text": "海光 DCU 2026 Q1 出货同比 +210%，全年出货目标上调 15%",
                    "evidence_ids": ["ev_hygon_q1_ccass"],
                },
                {
                    "entity_key": "002396.SZ",
                    "text": "星网锐捷 WACC 假设修正：11% → 8.5%，目标市值 199 亿 → 260 亿，上行空间 +40.5%",
                    "evidence_ids": ["ev_correction_wacc_2026"],
                },
            ],
            "催化观察": [
                {"entity_key": "300394.SZ", "text": "观察 DCI H2 追加招标 + 1.6T 首单"},
            ],
            "风险提醒": [
                {"entity_key": "300394.SZ",
                 "text": "光模块 2026 Q2 ASP -12%，存在价格战风险（暂未影响毛利率）"},
            ],
            "调仓建议": [
                {"entity_key": "002396.SZ", "text": "星网锐捷：目标市值上调，建议从观察池调入推荐池（参考 only）"},
            ],
        },
    }

    engine = DailyDraftEngine()
    r = engine.ingest_daily_report(daily_report)

    _check("抽到 ≥ 8 条 SignalEntry（市场流水 + 研究结论 3 + 催化 1 + 风险 1 + 调仓 1 = 至少 8）",
           len(r["signals"]) >= 8,
           f"实际={len(r['signals'])}")
    _check(f"产出 ≥ 5 条 WikiDraft（高价值条目都会变 draft，实际 {len(r['drafts'])}）",
           len(r["drafts"]) >= 5, f"类型分布={r['by_draft_type']}")
    _check(f"auto_ready ≥ 2（估值/目标价、出货同比 这类高分条目都 auto_ready，实际 {r['auto_ready_count']}）",
           r["auto_ready_count"] >= 2)

    # 分类检查
    by_t = r["by_draft_type"]
    _check("thesis 类草稿≥1（DCI 主题叙事）", by_t.get(DRAFT_TYPE_THESIS, 0) >= 1,
           f"分布={by_t}")
    _check("fact 类草稿≥1（海光出货 / 星网估值）", by_t.get(DRAFT_TYPE_FACT, 0) >= 1)
    _check("risk_case 草稿≥1（光模块 ASP 价格战）", by_t.get(DRAFT_TYPE_RISK_CASE, 0) >= 1)
    _check("catalyst 草稿≥1（H2 招标）", by_t.get(DRAFT_TYPE_CATALYST, 0) >= 1)
    _check("decision 草稿≥1（调入推荐池）", by_t.get(DRAFT_TYPE_DECISION, 0) >= 1)

    # 星网锐捷估值那条 score 应最高
    drafts_sorted = sorted(r["drafts"], key=lambda d: -d.confidence)
    top = drafts_sorted[0]
    _check("top 草稿 confidence ≥ 0.80（星网估值带证据）",
           top.confidence >= 0.80, f"top={top.draft_id} conf={top.confidence}")
    _check(f"top 草稿 approval_status='auto_ready'",
           top.approval_status == APPROVAL_AUTO_READY,
           f"status={top.approval_status}")

    # 纯流水账 2 条应 NOT 进 draft
    signal_texts = [(e.text, e.score) for e in r["signals"]]
    liushui_scores = [s for t, s in signal_texts if "沪指" in t or "北向" in t or "成交额" in t]
    _check("纯流水账条目 score 都 < 0.6（不进 draft）",
           liushui_scores and all(s < 0.60 for s in liushui_scores),
           f"scores={liushui_scores}")

    return r["drafts"]


# ============================================================================
# 阶段 8-2：周报压缩（验收：连续 5 日 → 至少 1 条 strategy / decision / risk case）
# ============================================================================
def case_p8_weekly_compression(daily_drafts):
    print("\n=== 阶段 8-2：周报压缩（5 天合并 → 稳定知识对象） ===")

    # 造 5 天相似草稿：DCI 主题每天都提到
    drafts = list(daily_drafts)
    # 再补 4 天"同主题 + 略有差异"的草稿，模拟一周 5 份日报
    for day in range(2, 6):
        for i, text in enumerate([
            ("DCI", "DCI 需求持续真实，本周 DCI 800G 端口出货同比 +190%~+220%"),
            ("DCI", "AI 算力 ETF 本周净 +880 亿，DCI 主题仅 +42 亿 → 叙事竞争仍强"),
            ("688041.SH", "海光 DCU Q1 出货同比 +210%，Q2 指引环比 +25%"),
            ("300394.SZ", "光模块 ASP 企稳，毛利率持平 → 价格战风险缓解"),
            ("002396.SZ", "星网锐捷 WACC 8.5% → 目标市值 260 亿，上行 +40.5% 未变化"),
        ]):
            ek, tx = text
            drafts.append(WikiDraft(
                draft_id=f"wd_day{day}_{i}",
                source_id=f"daily_2026072{day}",
                draft_type=(DRAFT_TYPE_THESIS if ek == "DCI" else
                            (DRAFT_TYPE_FACT if ek == "688041.SH" else
                             (DRAFT_TYPE_RISK_CASE if ek == "300394.SZ" else DRAFT_TYPE_FACT))),
                entity_type=("theme" if ek == "DCI" else "company"),
                entity_id=ek,
                title=tx[:30] + ("…" if len(tx) > 30 else ""),
                summary=tx,
                candidate_category="日报草稿",
                governance_status=GOVERNANCE_STATUS_REVIEW_REQUIRED,
                approval_status=APPROVAL_PENDING,
                confidence=0.70,
            ))

    compressor = WeeklyCompressor()
    stos = compressor.compress(drafts, week_label="2026-W30")
    _check("压缩后得到 ≥ 4 个稳定知识对象（DCI/海光/天孚/星网 至少 4 类）",
           len(stos) >= 4, f"实际类型/实体数={[(s.draft_type,s.entity_id) for s in stos]}")

    # DCI 那组应该 evidence_robustness ≥ 4 天（每天都写了 2 条，至少 4 天）
    dci_stos = [s for s in stos if s.entity_id == "DCI"]
    _check("DCI 主题有 1 条稳定对象", len(dci_stos) == 1, f"{[(s.draft_type,s.entity_id) for s in stos]}")
    s = dci_stos[0]
    _check(f"DCI 证据健壮性 ≥ 4 天", s.evidence_robustness_days >= 4,
           f"实际 {s.evidence_robustness_days}")
    _check("DCI governance_priority medium/high（主题类 medium）",
           s.governance_priority in ("medium", "high"),
           f"priority={s.governance_priority}")
    _check("stos 可转 WikiDraft 再接治理链", s.to_wiki_draft() is not None)

    # 矛盾构造：光模块风险 第 1 天写 ASP -12% 有价格战风险，第 4 天写企稳风险缓解
    # → 理论上应该有 contradiction_notes，但 WeeklyCompressor 的矛盾检测基于 regex 关键词
    # 第 1 天的草稿来自 DailyDraftEngine："光模块 2026 Q2 ASP -12%，存在价格战风险..."，
    # 第 4 天的草稿写了 "ASP 企稳，毛利率持平 → 价格战风险缓解" → 应该命中 (价格战 对 毛利率持平 / 风险缓解)
    risk_300394 = [x for x in stos if x.entity_id == "300394.SZ"]
    if risk_300394:
        rk = risk_300394[0]
        _check("光模块条目 contradiction 已标记（第 1 天 vs 第 4 天观点冲突，应命中）",
               len(rk.contradiction_notes) >= 1,
               f"contradiction={rk.contradiction_notes}，priority={rk.governance_priority}")
    return stos


# ============================================================================
# 阶段 10-1：SourceManifest + IngestDraft 4 步治理链（draft→ready→review→import）
# ============================================================================
def case_p10_wiki_governance(stos):
    print("\n=== 阶段 10：Wiki 治理链（登记源→抽草稿→治理扫描→人工 approve→import 正式 wiki） ===")

    svc = WikiGovernanceService()

    # 1) SourceManifest：登记 3 份来源（2 份日报 + 1 份研究卡 + 1 份风险）
    for sid, stype, etype, eid, path, title in [
        ("daily_20260723", "daily_report", "system", "ALL",
         "06_reports/daily/daily_20260723.md", "2026-07-23 日报"),
        ("research_card_688041", "research_card", "company", "688041.SH",
         "02_research/stocks/688041_SH_Hygon.md", "海光信息个股深度 V3"),
        ("risk_alert_300394", "risk_alert", "company", "300394.SZ",
         "05_risk/alerts/risk_300394_asp_decline.md", "300394.SZ ASP 下降风险"),
    ]:
        svc.register_source(SourceManifestEntry(
            source_id=sid, source_type=stype, entity_type=etype,
            entity_id=eid, source_path=path, title=title,
            tags=[stype, eid],
        ))
    _check("SourceManifest 登记 3 份来源", len(svc.manifest.list()) == 3)

    # 2) ingest 周报压缩的稳定对象 → WikiDraft → IngestDraft
    for s in stos:
        wd = s.to_wiki_draft()
        svc.ingest_wiki_draft(wd)
    # 再 ingest 1 条"完全同 source_id 重复导入" → 应该被标 duplicate_source
    dup_wd = WikiDraft(
        draft_id="wd_dup_should_block", source_id="daily_20260723",
        draft_type=DRAFT_TYPE_FACT, entity_type="company", entity_id="XXXX.SH",
        title="重复导入测试", summary="同 source_id，应该被 duplicate_source 拦",
        governance_status=GOVERNANCE_STATUS_REVIEW_REQUIRED,
        approval_status=APPROVAL_PENDING, confidence=0.75,
    )
    svc.ingest_wiki_draft(dup_wd)
    # 再 ingest 1 条"格式不完整 draft_type 非法" → 会被 WikiDraft.__post_init__ 先拦掉（不是治理链拦）
    try:
        WikiDraft(
            draft_id="wd_empty_bad", source_id="daily_9999999",
            draft_type="INVALID_TYPE_WHICH_DOES_NOT_EXIST",
            entity_type="company", entity_id="YYYY.SH",
            title="", summary="",  # 空标题+空摘要
            governance_status="review_required", approval_status="pending_manual_review",
            confidence=0.7,
        )
    except ValueError:
        pass
    # 再 ingest 1 条合法 draft_type 但 title/summary 为空的 → 被治理链 format_incomplete 拦
    empty_wd2 = WikiDraft(
        draft_id="wd_empty_goodtype", source_id="daily_9999999_v2",
        draft_type=DRAFT_TYPE_FACT, entity_type="company", entity_id="YYYY",
        title="", summary="",
        governance_status=GOVERNANCE_STATUS_REVIEW_REQUIRED,
        approval_status=APPROVAL_PENDING, confidence=0.7,
    )
    svc.ingest_wiki_draft(empty_wd2)

    # 3) scan 治理
    scan = svc.scan_queue()
    _check("治理 scan 出 review 队列 3 档（ready/review/blocked）",
           (scan.get("counts_ready", -1) >= 0 and scan.get("counts_review", -1) >= 0
            and scan.get("counts_blocked", -1) >= 0),
           f"ready/review/blocked = {scan['counts_ready']}/{scan['counts_review']}/{scan['counts_blocked']}")
    _check("至少有 1 条 blocked（重复 / 格式缺失会被拦）", scan["counts_blocked"] >= 1,
           f"blocked drafts={[(d.draft_id, d.reason_code) for d in scan['buckets'][GOVERNANCE_STATUS_BLOCKED]]}")

    # 4) 人工 review：对 1 条 blocked 里的 reject → reopen → approve（验收：3 种状态链路）
    pending = scan["buckets"][GOVERNANCE_STATUS_REVIEW_REQUIRED]
    _check("review_required 列表里有 DCI 主题 / 公司研究（我们至少有 ≥ 1 条）",
           len(pending) >= 1)

    # 主链路 1：pending → approved → import
    if pending:
        target1 = pending[0].draft_id
        svc.review_draft(target1, "approve", reviewer="投资经理", comment="观点扎实，允许导入")
        # 主链路 2：另一条 pending → reject → reopen → approve
    if len(pending) >= 2:
        target2 = pending[1].draft_id
        rj = svc.review_draft(target2, "reject", reviewer="研究员",
                              comment="证据不足，需补充 Q2 指引原件",
                              reason_code="insufficient_evidence")
        _check(f"reject 后 {target2} approval_status=rejected + reason_code 非空",
               rj.approval_status == APPROVAL_REJECTED and bool(rj.reason_code),
               f"after reject: status={rj.approval_status} reason={rj.reason_code}")
        ro = svc.review_draft(target2, "reopen", reviewer="研究员",
                              comment="已补公告 PDF，现可复核")
        _check(f"reopen 后 approval_status=reopened，状态回到 review 链路",
               ro.approval_status == APPROVAL_REOPENED)
        ap = svc.review_draft(target2, "approve", reviewer="投资经理",
                              comment="补充证据已看，通过")
        _check(f"再次 approve 后 approval_status=approved",
               ap.approval_status == APPROVAL_APPROVED)

    # 5) import → WikiEntry
    newly = svc.import_approved()
    _check("import_approved 至少 2 条正式 Wiki 页（1 条 ready + 1 条 approve/reopen/approve）",
           len(newly) >= 2, f"newly wiki 数={len(newly)}；review_counts={scan['approval_counts']}")
    _check(f"wiki_store 正式页≥2，状态均为 active",
           all(w.status == WIKI_STATUS_ACTIVE for w in svc.wiki_store.values())
           and len(svc.wiki_store) >= 2,
           f"store 大小={len(svc.wiki_store)}")

    return svc, newly


# ============================================================================
# 阶段 10-2：Wiki 体检（长期未更新 → stale / 孤儿页 / 缺来源 / 风险案例无处置）
# ============================================================================
def case_p10_wiki_linter(svc: WikiGovernanceService, newly: list[WikiEntry]):
    print("\n=== 阶段 10-2 / 阶段 9：Wiki 体检 Lint → backlog 清单 ===")

    # 先手动构造 3 条 wiki：1 条 60 天未更新、1 条孤儿无来源、1 条风险案例无处置
    from datetime import datetime, timezone, timedelta
    old1 = WikiEntry(wiki_id="wiki_old_stale", entity_id="XXXX.SH", entity_type="company",
                     title="过期条目 60 天没看", content_md="# 过期\n很久很久以前的知识。",
                     category="行业研究",
                     last_reviewed_at=(datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
                     source_draft_ids=["wd_old1"], backlink_ids=[])
    orphan = WikiEntry(wiki_id="wiki_orphan", entity_id="YYYY", entity_type="theme",
                       title="短孤儿", content_md="没什么内容", category="其他",
                       source_draft_ids=[], tags=[], backlink_ids=[])
    risk_bad = WikiEntry(wiki_id="wiki_risk_no_resolution", entity_id="ZZZZ.SZ",
                         entity_type="company", category="风险案例",
                         title="风险案例：价格战", content_md="2026 年 Q2 ASP -12%，有价格战风险",
                         source_draft_ids=["wd_risk_old"], backlink_ids=["wiki_old_stale"])
    svc.wiki_store[old1.wiki_id] = old1
    svc.wiki_store[orphan.wiki_id] = orphan
    svc.wiki_store[risk_bad.wiki_id] = risk_bad

    bl = svc.run_lint(stale_days=30)
    severities = [b["issue"] for b in bl]
    _check("backlog 至少 4 条 (stale + orphan + missing_source + risk_case_no_resolution)",
           len(bl) >= 4, f"backlog={bl}")
    _check("long stale 条目出现在 backlog 且 status 被标为 STALE",
           "stale_entry" in severities and old1.status == WIKI_STATUS_STALE,
           f"statuses={[(b['issue'], b['severity']) for b in bl]}; old1.status={old1.status}")
    _check("孤儿页问题被检出（无 backlink 且内容短）", "orphan_page" in severities)
    _check("缺来源的条目被检出（orphan 无 source_draft_ids）", "missing_source" in severities)
    _check("风险案例没后续处置被检出（严重度 high）", "risk_case_no_resolution" in severities,
           f"severities={severities}")

    # 最后：整个服务可序列化导出（便于 dump 备份）
    export = svc.export_wiki_to_json()
    _wkeys = (
        list(export["wiki_entries"].keys())
        if isinstance(export["wiki_entries"], dict)
        else [e["wiki_id"] for e in export["wiki_entries"][:3]]
    )
    _check("svc.export_wiki_to_json 有 wiki_count ≥ 5 （2 imported + 3 test = 5）",
           export.get("wiki_count", 0) >= 5,
           f"wiki_count={export.get('wiki_count')}；前3个wiki_ids={_wkeys}")
    _check("export 里 source_manifest.entries 有 3 条来源登记",
           export["source_manifest"].get("count", 0) >= 3)


# ============================================================================
# 主入口
# ============================================================================
def main():
    print("======== 阶段 8 + 阶段 10 单文件测试（日报/周报压缩 → Wiki 治理链 → Lint backlog） ========")
    d = case_p8_daily_engine()
    s = case_p8_weekly_compression(d)
    svc, newly = case_p10_wiki_governance(s)
    case_p10_wiki_linter(svc, newly)
    print("\n" + "=" * 72)
    total = _PASS + _FAIL
    if _FAIL == 0:
        print(f"ALL PASSED  ✅  {_PASS}/{total}")
        return 0
    print(f"FAILED  ❌  {_FAIL}/{total} failed，{_PASS} passed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
