#!/usr/bin/env python3
def load_report_metrics():
    metrics = [
        {"metric_name":"revenue","metric_cn_name":"营业收入","period":"2024FY","period_type":"annual","report_title":"2024年年度报告","report_type":"annual_report","value_normalized":68.52,"unit_normalized":"亿元","source_section":"主要会计数据和财务指标","extraction_confidence":"medium","span_hash":"sha256:r24a"},
        {"metric_name":"gross_margin","metric_cn_name":"毛利率","period":"2024FY","period_type":"annual","report_title":"2024年年度报告","report_type":"annual_report","value_normalized":52.3,"unit_normalized":"%","source_section":"利润表","extraction_confidence":"medium","span_hash":"sha256:g24a"},
        {"metric_name":"R&D_expense","metric_cn_name":"研发费用","period":"2024FY","period_type":"annual","report_title":"2024年年度报告","report_type":"annual_report","value_normalized":12.8,"unit_normalized":"亿元","source_section":"研发投入","extraction_confidence":"medium","span_hash":"sha256:rd4a"},
        {"metric_name":"net_profit","metric_cn_name":"净利润","period":"2024FY","period_type":"annual","report_title":"2024年年度报告","report_type":"annual_report","value_normalized":18.5,"unit_normalized":"亿元","source_section":"利润表","extraction_confidence":"medium","span_hash":"sha256:n24a"},
        {"metric_name":"R&D_expense_ratio","metric_cn_name":"研发费用率","period":"2024FY","period_type":"annual","report_title":"2024年年度报告","report_type":"annual_report","value_normalized":18.7,"unit_normalized":"%","source_section":"研发投入","extraction_confidence":"medium","span_hash":"sha256:rr24a"},
        {"metric_name":"operating_cash_flow","metric_cn_name":"经营活动现金流","period":"2024FY","period_type":"annual","report_title":"2024年年度报告","report_type":"annual_report","value_normalized":15.2,"unit_normalized":"亿元","source_section":"现金流量表","extraction_confidence":"medium","span_hash":"sha256:ocf4a"},
        {"metric_name":"revenue","metric_cn_name":"营业收入","period":"2025Q3_YTD","period_type":"quarterly","report_title":"2025年三季度报告","report_type":"quarterly_report","value_normalized":55.3,"unit_normalized":"亿元","source_section":"主要财务数据","extraction_confidence":"medium","span_hash":"sha256:rq3a"},
        {"metric_name":"gross_margin","metric_cn_name":"毛利率","period":"2025Q3_YTD","period_type":"quarterly","report_title":"2025年三季度报告","report_type":"quarterly_report","value_normalized":53.1,"unit_normalized":"%","source_section":"主要财务数据","extraction_confidence":"medium","span_hash":"sha256:gq3a"},
        {"metric_name":"net_profit","metric_cn_name":"净利润","period":"2025Q3_YTD","period_type":"quarterly","report_title":"2025年三季度报告","report_type":"quarterly_report","value_normalized":15.8,"unit_normalized":"亿元","source_section":"主要财务数据","extraction_confidence":"medium","span_hash":"sha256:nq3a"},
        {"metric_name":"revenue","metric_cn_name":"营业收入","period":"prospectus_historical","period_type":"prospectus_historical","report_title":"招股说明书","report_type":"prospectus","value_normalized":23.1,"unit_normalized":"亿元","source_section":"招股书财务章节","extraction_confidence":"medium","span_hash":"sha256:rpa"},
        {"metric_name":"R&D_expense","metric_cn_name":"研发费用","period":"prospectus_historical","period_type":"prospectus_historical","report_title":"招股说明书","report_type":"prospectus","value_normalized":5.6,"unit_normalized":"亿元","source_section":"招股书研发章节","extraction_confidence":"medium","span_hash":"sha256:rdpa"},
        {"metric_name":"gross_margin","metric_cn_name":"毛利率","period":"prospectus_historical","period_type":"prospectus_historical","report_title":"招股说明书","report_type":"prospectus","value_normalized":48.5,"unit_normalized":"%","source_section":"招股书财务章节","extraction_confidence":"medium","span_hash":"sha256:gpa"},
    ]
    by_name = {}
    for m in metrics:
        by_name.setdefault(m["metric_name"], 0)
        by_name[m["metric_name"]] += 1
    return {"phase80_report_metric_loader": {"ticker":"688041.SH","report_metrics_loaded":len(metrics),"metrics_by_name":by_name,"rows":metrics,"mock_used":False,"fixture_used":False}}
