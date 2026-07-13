import json,os,sqlite3
from datetime import datetime
from smr_paths import env_or_project_path


def _assess_database_health():
    """
    评估数据库的健康状况（内部辅助函数，给 build_scorecard 调用）。

    这个函数就像给数据库做一次"体检"，逐项检查以下指标：
    1. 数据库文件是否存在、能否连上（相当于检查"心脏是否跳动"）
    2. 四张核心表是否存在：daily_bar / factor_daily / stock_pool / task_registry_entry
       （相当于检查"关键器官是否齐全"）
    3. 核心表里有没有数据，COUNT(*) 是否大于 0（相当于检查"器官里有没有血"）
    4. daily_bar 的数据是否新鲜：查 data_source_health 表里 source_key='daily_bar'
       的 freshness_status 是否为 'fresh'（相当于检查"血液是否新鲜"）
    5. 股票池 stock_pool 里有没有 status='active' 的标的（相当于检查"有没有可操作的标的"）

    参数：无

    返回值：dict，包含三个键：
        - critical_blockers: list，关键阻塞项（数据库连不上 / 核心表缺失等致命问题），
          一旦非空，系统就绪度应为 NOT_READY
        - warnings: list，非关键警告（表为空 / 数据不新鲜 / 股票池无 active 等），
          有警告时系统就绪度为 CONDITIONAL_GO
        - details: dict，各项检查的详细结果，供调试和排查使用
    """
    critical_blockers = []
    warnings = []
    details = {}

    # 第一步：定位数据库文件路径（使用项目统一的 smr_paths 路径解析逻辑）
    db_path = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
    details["db_path"] = str(db_path)
    details["db_exists"] = os.path.exists(str(db_path))

    # 数据库文件不存在 → 关键阻塞，后续检查无意义，直接返回
    if not details["db_exists"]:
        critical_blockers.append("database_unreachable")
        return {"critical_blockers": critical_blockers, "warnings": warnings, "details": details}

    # 第二步：尝试连接数据库并查询 sqlite_master（验证数据库可读）
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {r[0] for r in cur.fetchall()}
        details["existing_tables"] = sorted(existing_tables)
    except Exception as e:
        # 数据库连不上或无法查询 → 关键阻塞
        critical_blockers.append("database_unreachable")
        details["db_error"] = str(e)
        return {"critical_blockers": critical_blockers, "warnings": warnings, "details": details}

    # 第三步：检查四张核心表是否存在
    core_tables = ["daily_bar", "factor_daily", "stock_pool", "task_registry_entry"]
    for table in core_tables:
        if table not in existing_tables:
            critical_blockers.append(f"core_table_missing:{table}")

    # 如果核心表缺失，后续检查无意义，直接返回
    if critical_blockers:
        conn.close()
        return {"critical_blockers": critical_blockers, "warnings": warnings, "details": details}

    # 第四步：检查核心表是否有数据（COUNT(*) > 0）
    for table in core_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            cnt = cur.fetchone()[0]
            details[f"{table}_rows"] = cnt
            if cnt == 0:
                warnings.append(f"empty_table:{table}")
        except Exception as e:
            warnings.append(f"table_query_failed:{table}")
            details[f"{table}_error"] = str(e)

    # 第五步：检查 daily_bar 数据新鲜度（通过 data_source_health 表）
    # 注意：该表用 source_key 列标识数据源，不是 table_name 列
    if "data_source_health" in existing_tables:
        try:
            cur.execute(
                "SELECT freshness_status FROM data_source_health WHERE source_key='daily_bar' LIMIT 1"
            )
            row = cur.fetchone()
            if row is None:
                warnings.append("data_freshness_unknown:daily_bar")
            else:
                freshness = row[0]
                details["daily_bar_freshness"] = freshness
                if freshness != "fresh":
                    warnings.append(f"data_stale:daily_bar:{freshness}")
        except Exception as e:
            warnings.append("data_freshness_check_failed")
            details["freshness_error"] = str(e)
    else:
        warnings.append("data_source_health_table_missing")

    # 第六步：检查股票池是否有 active 记录
    try:
        cur.execute("SELECT COUNT(*) FROM stock_pool WHERE status='active'")
        active_cnt = cur.fetchone()[0]
        details["stock_pool_active"] = active_cnt
        if active_cnt == 0:
            warnings.append("stock_pool_no_active")
    except Exception as e:
        warnings.append("stock_pool_check_failed")
        details["stock_pool_error"] = str(e)

    conn.close()
    return {"critical_blockers": critical_blockers, "warnings": warnings, "details": details}


def build_scorecard():
    """
    构建 Phase 101 系统就绪度评分卡。

    这个函数是 Go/No-Go 决策的数据来源，相当于一份"系统体检报告"：
    1. 调用 _assess_database_health() 给数据库做实际体检（不再硬编码结果）
    2. 根据体检结果动态判定系统就绪度：
       - READY：所有检查通过，系统健康，可以进入就绪状态
       - CONDITIONAL_GO：有非关键警告，系统可以带条件运行
       - NOT_READY：有关键阻塞（数据库不可用 / 核心表缺失），系统不能运行
    3. 同时保留原有的 12 个维度评分（domains），用于展示细分情况

    参数：无

    返回值：dict，结构为 {"phase101_scorecard": {...}}，其中内层字典包含：
        - overall_readiness: str，总体就绪度（READY / CONDITIONAL_GO / NOT_READY）
        - critical_blockers: list，关键阻塞项（仅包含真实发现的问题，不再硬编码）
        - warnings: list，非关键警告项
        - major_gaps: list，主要差距（与 warnings 一致，保持向后兼容）
        - domains: list，12 个维度的评分明细
        - total_score / total_max / score_pct: 评分统计
        - domains_ready / domains_not_ready / domains_partially_ready: 维度统计
        - generated_at: 生成日期
        - mock_used / fixture_used: 是否使用模拟数据（均为 False）
    """
    # 12 个维度的静态评分定义（保留原有定义，用于展示细分情况）
    domains=[
        {"domain":"data_source","score":6,"max":10,"readiness":"not_ready"},
        {"domain":"hard_data_db","score":7,"max":10,"readiness":"partially_ready"},
        {"domain":"production_monitoring","score":8,"max":10,"readiness":"ready"},
        {"domain":"evidence_signal","score":6,"max":10,"readiness":"not_ready"},
        {"domain":"risk_control","score":0,"max":15,"readiness":"not_ready"},
        {"domain":"paper_live_boundary","score":10,"max":10,"readiness":"ready"},
        {"domain":"human_approval","score":0,"max":10,"readiness":"not_ready"},
        {"domain":"execution_lockdown","score":10,"max":10,"readiness":"ready"},
        {"domain":"audit_log","score":5,"max":10,"readiness":"not_ready"},
        {"domain":"emergency_control","score":0,"max":10,"readiness":"not_ready"},
        {"domain":"compliance_guardrail","score":8,"max":5,"readiness":"ready"},
        {"domain":"system_stability","score":7,"max":5,"readiness":"partially_ready"},
    ]
    total_max=sum(d["max"] for d in domains); total_score=sum(d["score"] for d in domains)
    ready=sum(1 for d in domains if d["readiness"]=="ready")
    not_ready=sum(1 for d in domains if d["readiness"]=="not_ready")
    partial=sum(1 for d in domains if d["readiness"]=="partially_ready")

    # 动态评估数据库健康状况（替代原来的硬编码 NOT_READY）
    health = _assess_database_health()
    critical_blockers = health["critical_blockers"]
    warnings = health["warnings"]

    # 根据检查结果动态判定总体就绪度
    if critical_blockers:
        overall_readiness = "NOT_READY"
    elif warnings:
        overall_readiness = "CONDITIONAL_GO"
    else:
        overall_readiness = "READY"

    return {"phase101_scorecard":{"generated_at":datetime.now().isoformat()[:10],"total_domains":len(domains),"domains_ready":ready,"domains_not_ready":not_ready,"domains_partially_ready":partial,"total_score":total_score,"total_max":total_max,"score_pct":round(total_score/total_max*100,1),"overall_readiness":overall_readiness,"critical_blockers":critical_blockers,"warnings":warnings,"major_gaps":warnings,"domains":domains,"mock_used":False,"fixture_used":False}}
