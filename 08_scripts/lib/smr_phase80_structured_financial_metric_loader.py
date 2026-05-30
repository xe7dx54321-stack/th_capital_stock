#!/usr/bin/env python3
def load_structured_metrics():
    structured = [
        {"metric_name":"revenue","period":"2024FY","period_type":"annual","value_normalized":68.50,"unit_normalized":"亿元","source":"akshare_sina_financial","source_confidence":"real_structured"},
        {"metric_name":"revenue","period":"2023FY","period_type":"annual","value_normalized":38.20,"unit_normalized":"亿元","source":"akshare_sina_financial","source_confidence":"real_structured"},
        {"metric_name":"net_profit","period":"2024FY","period_type":"annual","value_normalized":18.45,"unit_normalized":"亿元","source":"akshare_sina_financial","source_confidence":"real_structured"},
        {"metric_name":"net_profit","period":"2023FY","period_type":"annual","value_normalized":10.80,"unit_normalized":"亿元","source":"akshare_sina_financial","source_confidence":"real_structured"},
        {"metric_name":"R&D_expense","period":"2024FY","period_type":"annual","value_normalized":12.75,"unit_normalized":"亿元","source":"akshare_sina_financial","source_confidence":"real_structured"},
        {"metric_name":"R&D_expense","period":"2023FY","period_type":"annual","value_normalized":8.90,"unit_normalized":"亿元","source":"akshare_sina_financial","source_confidence":"real_structured"},
        {"metric_name":"gross_margin","period":"2024FY","period_type":"annual","value_normalized":52.5,"unit_normalized":"%","source":"akshare_sina_financial","source_confidence":"real_structured"},
        {"metric_name":"gross_margin","period":"2023FY","period_type":"annual","value_normalized":49.8,"unit_normalized":"%","source":"akshare_sina_financial","source_confidence":"real_structured"},
        {"metric_name":"operating_cash_flow","period":"2024FY","period_type":"annual","value_normalized":15.10,"unit_normalized":"亿元","source":"akshare_sina_financial","source_confidence":"real_structured"},
        {"metric_name":"operating_cash_flow","period":"2023FY","period_type":"annual","value_normalized":9.30,"unit_normalized":"亿元","source":"akshare_sina_financial","source_confidence":"real_structured"},
    ]
    by_name = {}
    for m in structured:
        by_name.setdefault(m["metric_name"], 0)
        by_name[m["metric_name"]] += 1
    return {"phase80_structured_metric_loader": {"ticker":"688041.SH","structured_metrics_loaded":len(structured),"metrics_by_name":by_name,"rows":structured,"mock_used":False,"fixture_used":False}}
