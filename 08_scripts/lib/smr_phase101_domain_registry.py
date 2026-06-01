import json,os
def build_domain_registry():
    domains=[
        {"domain_id":"ds","name":"data_source_coverage_and_health","category":"data","weight":10,"description":"评估数据源覆盖范围、健康状态、冗余度"},
        {"domain_id":"db","name":"hard_data_db_population_and_refresh","category":"data","weight":10,"description":"评估 hard data DB 填充率、刷新机制、增量更新"},
        {"domain_id":"pm","name":"production_monitoring_and_alerting","category":"ops","weight":10,"description":"评估生产监控、告警、source health board"},
        {"domain_id":"ev","name":"evidence_and_signal_validation","category":"signal","weight":10,"description":"评估 evidence 可用性、signal 可靠性、cannot-conclude guard"},
        {"domain_id":"rc","name":"risk_control_architecture","category":"risk","weight":15,"description":"评估 risk control 架构、仓位限制、风控规则"},
        {"domain_id":"pl","name":"paper_live_boundary","category":"safety","weight":10,"description":"评估 paper vs live 边界、资金隔离、路由隔离"},
        {"domain_id":"ha","name":"human_approval_gate","category":"safety","weight":10,"description":"评估人工审批 gate 的存在性和完整性"},
        {"domain_id":"el","name":"execution_lockdown","category":"safety","weight":10,"description":"评估 execution lockdown 和 live path 禁用状态"},
        {"domain_id":"al","name":"audit_log_and_decision_trace","category":"compliance","weight":10,"description":"评估审计日志、决策溯源、证据链完整性"},
        {"domain_id":"ec","name":"emergency_control_and_kill_switch","category":"risk","weight":10,"description":"评估紧急控制、kill switch、强制中止能力"},
        {"domain_id":"cg","name":"compliance_and_guardrail","category":"compliance","weight":5,"description":"评估合规 guardrail、交易术语检测、建议过滤"},
        {"domain_id":"st","name":"overall_system_stability","category":"ops","weight":5,"description":"评估系统稳定性、错误恢复、历史运行记录"}
    ]
    return {"phase101_domain_registry":{"total_domains":len(domains),"domains":domains,"mock_used":False,"fixture_used":False}}
