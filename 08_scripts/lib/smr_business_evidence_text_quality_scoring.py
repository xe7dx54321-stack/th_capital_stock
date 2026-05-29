#!/usr/bin/env python3
"""Business evidence text quality scoring - Phase 66."""
from typing import Any

QUALITY_GRADES=["high_business_signal","usable_business_signal","usable_with_warnings","financial_context_only","low_signal","rejected"]

def score_text_quality(text:str,source_type:str="other",publish_date:str="")->dict[str,Any]:
    if not text or len(text)<100: return {"quality_grade":"rejected","score":0,"reason":"too_short","allowed_usage":"none"}
    score=50;reasons=[]
    length=len(text)
    if length>5000: score+=10;reasons.append("good_length")
    elif length>2000: score+=5
    else: score-=5;reasons.append("short_text")
    biz_kw=["800G","1.6T","1.6 T","光模块","光通信","硅光","CPO","LPO","出货","交付","量产","客户","产能","扩产","订单","能见度","ASP","毛利率"]
    kw_count=sum(1 for kw in biz_kw if kw.lower() in text.lower())
    if kw_count>=5: score+=20;reasons.append("high_business_relevance")
    elif kw_count>=2: score+=10;reasons.append("moderate_business_relevance")
    else: reasons.append("low_business_relevance")
    st_weights={"investor_relations_record":90,"performance_briefing_or_earnings_call":85,"annual_report":70,"semiannual_report":65,"quarterly_report":60,"major_announcement":55,"other_announcement":40}
    st_weight=st_weights.get(source_type,40)
    score=int(score*0.6+st_weight*0.4)
    disclaimer_kw=["风险提示","免责","声明"]
    disc_count=sum(1 for d in disclaimer_kw if d in text[:500])
    if disc_count>=2: score-=10;reasons.append("heavy_disclaimer")
    table_kw=["单位：","项目","本期发生额","上期发生额","合计","总计"]
    table_count=sum(1 for t in table_kw if t in text)
    if table_count>=8: score-=5;reasons.append("heavy_table_noise")
    fin_only_kw=["营业收入","营业成本","净利润","归属于母公司","基本每股收益","加权平均"]
    fin_count=sum(1 for f in fin_only_kw if f in text)
    biz_count=kw_count
    if fin_count>biz_count*3 and kw_count<2: score-=15;reasons.append("financial_data_only")
    score=max(0,min(score,99))
    if score>=80: grade="high_business_signal"
    elif score>=65: grade="usable_business_signal"
    elif score>=50: grade="usable_with_warnings"
    elif fin_count>biz_count*2: grade="financial_context_only"
    elif score>=30: grade="low_signal"
    else: grade="rejected"
    usage="deep_business_evidence_extraction" if grade in ("high_business_signal","usable_business_signal") else ("usable_with_caution" if grade=="usable_with_warnings" else ("financial_context_only" if grade=="financial_context_only" else "none"))
    return {"quality_grade":grade,"score":score,"reasons":reasons,"keyword_hit_count":kw_count,"text_length":length,"allowed_usage":usage}

def score_texts(texts:list[dict])->dict[str,Any]:
    results=[];grades_count={g:0 for g in QUALITY_GRADES}
    for t in texts:
        q=score_text_quality(t.get("text",""),t.get("source_type","other"),t.get("publish_date",""))
        q["source_id"]=t.get("source_id","")
        q["title"]=(t.get("title","") or "")[:80]
        grades_count[q["quality_grade"]]=grades_count.get(q["quality_grade"],0)+1
        results.append(q)
    return {"texts_checked":len(texts),"high_business_signal":grades_count.get("high_business_signal",0),"usable_business_signal":grades_count.get("usable_business_signal",0),"usable_with_warnings":grades_count.get("usable_with_warnings",0),"financial_context_only":grades_count.get("financial_context_only",0),"low_signal":grades_count.get("low_signal",0),"rejected":grades_count.get("rejected",0),"rows":sorted(results,key=lambda x:-x["score"])}
