"""
通用配置加载器，替代所有 smr_phase*_config.py 文件

使用方式：
from smr_config_loader import ConfigLoader

# 方式1：直接加载配置
cfg = ConfigLoader.get_config('phase100')

# 方式2：通过 phase 编号加载
cfg = ConfigLoader.get_phase_config(100)

# 方式3：获取特定配置项
pipeline_order = ConfigLoader.get_config('phase100')['production']['pipeline_order']
"""

from pathlib import Path
import json
from typing import Optional, Dict, Any
import inspect
from datetime import date


class ConfigLoader:
    """
    通用配置加载器
    
    功能：
    - 缓存机制避免重复读取文件
    - 支持通过 phase 编号或名称加载配置
    - 提供默认配置文件命名映射
    - 自动处理编码问题
    """
    
    _cache: Dict[str, Dict[str, Any]] = {}
    
    # 默认配置文件映射表
    # key: phase 编号, value: 配置文件名
    _config_map: Dict[int, str] = {
        69: "phase69_multi_ticker_universe.json",
        75: "phase75_fallback_html_real_execute.json",
        76: "phase76_pdf_recovery_known_url_breakthrough.json",
        77: "phase77_pdf_evidence_quality_rules.json",
        78: "phase78_generic_hard_tech_chinese_keywords.json",
        79: "phase79_quantitative_metric_schema.json",
        80: "phase80_report_quant_consistency_rules.json",
        81: "phase81_time_series_watchlist_monitoring.json",
        82: "phase82_multi_ticker_financial_coverage.json",
        83: "phase83_hk_us_financial_adapters.json",
        84: "phase84_scheduled_daily_monitoring.json",
        85: "phase85_valuation_integration.json",
        85: "phase85b_valuation_source_hardening_closeout.json",
        86: "phase86_expectation_market_pricing.json",
        87: "phase87_external_source_integration.json",
        88: "phase88_external_daily_signal_delta.json",
        89: "phase89_unified_daily_intelligence.json",
        90: "phase90_scheduled_automation_delivery.json",
        91: "phase91_information_source_reality_audit.json",
        92: "phase92_order_contract_tender_sources.json",
        93: "phase93_customer_capex_supply_chain_sources.json",
        94: "phase94_product_pricing_management_guidance.json",
        95: "phase95_300394_688041_gap_close.json",
        96: "phase96_peer_benchmark_hard_data.json",
        97: "phase97_automated_db_refresh.json",
        98: "phase98_live_source_monitoring.json",
        99: "phase99_self_healing_failover.json",
        100: "phase100_continuous_production.json",
        101: "phase101_live_trading_readiness.json",
        102: "phase102_backtest_readiness.json",
        103: "phase103_risk_control_readiness.json",
        104: "phase104_human_approval_readiness.json",
        105: "phase105_kill_switch_readiness.json",
        106: "phase106_readiness_integration.json",
        107: "phase107_paper_trading_boundary.json",
        108: "phase108_paper_execution_readiness.json",
        109: "phase109_operator_identity_readiness.json",
        110: "phase110_operator_assignment_manifest.json",
        111: "phase111_personal_owner_mode.json",
        112: "phase112_opportunity_radar.json",
        113: "phase113_cross_source_scoring.json",
        114: "phase114_catalyst_inflection_detector.json",
        115: "phase115_candidate_board.json",
        116: "phase116_watchlist_research_loop.json",
        117: "phase117_master_daily_runner.json",
        118: "phase118_system_health.json",
        119: "phase119_continuous_improvement.json",
        120: "phase120_project_closeout.json",
        121: "phase121_external_source_expansion.json",
        122: "phase122_daily_research_brief.json",
        123: "phase123_owner_feedback_memory.json",
        124: "phase124_decision_journal.json",
        125: "phase125_outcome_tracking.json",
        126: "phase126_signal_effectiveness_review.json",
        127: "phase127_mainline_closeout.json",
        128: "phase128_external_source_probe.json",
        129: "phase129_official_source_fallback.json",
        130: "phase130_300394_cninfo_resolution.json",
        131: "phase131_300394_alternative_integration.json",
        132: "phase132_688041_valuation_hardening.json",
        133: "phase133_seasonal_analytics.json",
        134: "phase134_personal_research_console.json",
        135: "phase135_owner_feedback_integration.json",
        136: "phase136_deep_dive_workflow.json",
        137: "phase137_deep_dive_execution.json",
        138: "phase138_thesis_library.json",
        139: "phase139_scheduled_local_run.json",
        140: "phase140_system_hardening.json",
        141: "phase141_html_dashboard.json",
        142: "phase142_ticker_detail_pages.json",
        143: "phase143_cross_link_navigation.json",
        144: "phase144_feedback_workflow.json",
        145: "phase145_agent_orchestration.json",
        146: "phase146_agent_memory_queue.json",
        147: "phase147_ticker_onboarding.json",
        148: "phase148_candidate_activation.json",
        149: "phase149_agent_instructions.json",
        150: "phase150_watchlist_tiering.json",
        151: "phase151_auto_candidate_discovery.json",
        152: "phase152_candidate_admission_scoring.json",
        153: "phase153_candidate_onboarding_review.json",
        154: "phase154_multi_agent_research_loop.json",
        155: "phase155_agent_loop_scheduling.json",
        156: "phase156_owner_activation_review.json",
        157: "phase157_owner_decision_input_workflow.json",
        158: "phase158_owner_decision_ui.json",
        159: "phase159_owner_decision_submission.json",
        160: "phase160_owner_decision_example_pack.json",
        161: "phase161_owner_decision_ui_feedback.json",
        162: "phase162_real_network_candidate_hydration.json",
        163: "phase163_candidate_hydration_live_execute.json",
        164: "phase164_candidate_hydration_console.json",
        165: "phase165_readiness_repair_research_packets.json",
        166: "phase166_live_evidence_fill.json",
        167: "phase167_owner_review_packet_console.json",
        168: "phase168_owner_decision_submission.json",
        169: "phase169_owner_decision_authoring_guide.json",
        170: "phase170_owner_input_validation.json",
        171: "phase171_owner_final_apply_confirmation.json",
        172: "phase172_formal_coverage_apply_execution.json",
        173: "phase173_owner_decision_preparation.json",
        174: "phase174_post_apply_coverage_console.json",
        175: "phase175_research_task_runner.json",
        176: "phase176_coverage_state_reconciliation.json",
        177: "phase177_deep_dive_packets.json",
        178: "phase178_packet_review_workflow.json",
        179: "phase179_owner_review_input_processing.json",
        180: "phase180_brief_packet_integration_preview.json",
        181: "phase181_owner_review_authoring_pack.json",
        182: "phase182_intelligence_scout_prompt_pack.json",
        183: "phase183_dirty_intelligence_inbox.json",
        184: "phase184_dirty_intelligence_triage.json",
        185: "phase185_cross_check_gate.json",
        186: "phase186_simulated_scout_cross_check.json",
        187: "phase187_real_web_scout_pilot.json",
        188: "phase188_real_source_lead_ingestion.json",
        189: "phase189_ifind_capability_probe.json",
        190: "phase190_ifind_structured_snapshot.json",
        191: "phase191_ifind_metric_hardening.json",
        192: "phase192_ifind_daily_monitoring.json",
        193: "phase193_ifind_daily_monitoring_bridge.json",
        194: "phase194_ifind_daily_monitoring_apply.json",
        195: "phase195_ifind_dirty_source_adapter.json",
        196: "phase196_ifind_cross_check_bridge.json",
        197: "phase197_cn_a_web_scout_expansion.json",
        198: "phase198_ifind_bridge_rerun.json",
        199: "phase199_real_cross_source_verification.json",
        200: "phase200_dirty_to_clean_classifier.json",
        201: "phase201_clean_evidence_store.json",
        202: "phase202_evidence_packet_integration_preview.json",
        203: "phase203_hk_us_evidence_chain_expansion.json",
        204: "phase204_hk_us_real_verification_store_backfill.json",
        205: "phase205_unified_evidence_packet_coverage_refresh.json",
        206: "phase206_formal_packet_apply_owner_approval_workflow.json",
        207: "phase207_formal_packet_apply_execution.json",
        207: "phase207b_owner_approval_simulation.json",
        207: "phase207c_test_suite_health.json",
    }
    
    @classmethod
    def get_config(cls, phase_name: str, config_name: Optional[str] = None) -> Dict[str, Any]:
        """
        加载指定 phase 的配置
        
        Args:
            phase_name: phase 名称（如 'phase100'）
            config_name: 配置文件名（可选，默认为 f"{phase_name}.json"）
        
        Returns:
            配置字典
        
        Raises:
            FileNotFoundError: 配置文件不存在时
        """
        if config_name is None:
            config_name = f"{phase_name}.json"
        
        cache_key = f"{phase_name}:{config_name}"
        
        # 返回缓存
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        # 查找配置文件
        config_dir = cls._get_config_dir()
        config_file = config_dir / config_name
        
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        # 读取并解析
        with open(config_file, "r", encoding="utf-8-sig") as f:
            cls._cache[cache_key] = json.load(f)
        
        return cls._cache[cache_key]
    
    @classmethod
    def get_phase_config(cls, phase_num: int) -> Dict[str, Any]:
        """
        根据 phase 编号加载配置
        
        Args:
            phase_num: phase 编号（如 100）
        
        Returns:
            配置字典
        
        Example:
            >>> cfg = ConfigLoader.get_phase_config(100)
            >>> print(cfg['production']['pipeline_order'])
        """
        config_name = cls._config_map.get(phase_num, f"phase{phase_num}.json")
        return cls.get_config(f"phase{phase_num}", config_name)
    
    @classmethod
    def _get_config_dir(cls) -> Path:
        """获取配置目录路径"""
        return Path(__file__).resolve().parent.parent.parent / "config"
    
    @classmethod
    def clear_cache(cls):
        """清空缓存（用于测试）"""
        cls._cache.clear()
    
    @classmethod
    def get_config_path(cls, phase_num: int) -> Path:
        """获取配置文件路径"""
        config_name = cls._config_map.get(phase_num, f"phase{phase_num}.json")
        return cls._get_config_dir() / config_name


# ====================
# 兼容旧 API 的便捷函数
# ====================

def load_config() -> Dict[str, Any]:
    """
    兼容旧代码的配置加载函数
    
    从调用者文件名自动推断 phase 编号
    保持与原有 smr_phase*_config.py 的 API 兼容
    
    Returns:
        配置字典
    """
    # 从调用栈获取调用者信息
    stack = inspect.stack()
    if len(stack) >= 2:
        caller_frame = stack[1]
        caller_file = Path(caller_frame.filename)
        
        # 从文件名提取 phase 编号
        file_name = caller_file.name
        if file_name.startswith("smr_phase") and "_config.py" in file_name:
            phase_str = file_name.replace("smr_phase", "").replace("_config.py", "")
            try:
                phase_num = int(phase_str)
                return ConfigLoader.get_phase_config(phase_num)
            except ValueError:
                pass
    
    # 默认返回空配置（向后兼容）
    return {}


def get_pipeline_order() -> Optional[list]:
    """
    获取生产流水线顺序（兼容旧 API）
    
    Returns:
        pipeline_order 列表，或 None
    """
    try:
        cfg = ConfigLoader.get_phase_config(100)
        return cfg.get("production", {}).get("pipeline_order")
    except FileNotFoundError:
        return None


def get_reports_dir() -> Optional[str]:
    """
    获取报告目录（兼容旧 API）
    
    Returns:
        报告目录路径，或 None
    """
    try:
        cfg = ConfigLoader.get_phase_config(100)
        return cfg.get("reports", {}).get("output_dir")
    except FileNotFoundError:
        return None


def is_reports_gitignored() -> bool:
    """
    检查报告是否被 gitignore（兼容旧 API）
    
    Returns:
        是否被 gitignore
    """
    try:
        cfg = ConfigLoader.get_phase_config(100)
        return cfg.get("reports", {}).get("gitignored", False)
    except FileNotFoundError:
        return False


def is_manual_assignment_only() -> bool:
    """
    检查是否仅手动分配（兼容旧 API）
    
    Returns:
        是否仅手动分配
    """
    try:
        cfg = ConfigLoader.get_phase_config(110)
        return cfg.get("assignment", {}).get("manual_assignment_only", False)
    except FileNotFoundError:
        return False
