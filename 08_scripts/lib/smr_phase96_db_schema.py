import json,os
def build_hard_data_db_schema():
    fields={
        "record_id":"string","ticker":"string",
        "hard_data_category":"enum[order_contract,customer_capex,supply_chain,product_pricing,management_guidance,valuation_pricing]",
        "source_phase":"string","source_file":"string",
        "field_name":"string","field_value":"any","unit":"string","currency":"string",
        "data_type":"enum[reported_structured,derived_from_reported,text_evidence,proxy_estimate,peer_context_only,unknown,unavailable,source_exhausted]",
        "period":"string","as_of_date":"string",
        "confidence":"enum[high,medium,low]","source_trace":"string","limitation":"string","cannot_conclude":"array[string]"
    }
    return {"phase96_hard_data_db_schema":{"schema_version":"v1","table_name":"hard_data_records","fields":fields,"total_fields":len(fields),"mock_used":False,"fixture_used":False}}
