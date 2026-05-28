#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

def build(conn,ticker):
    return {'phase': 'phase55', 'framework_generalization': {
        'generic_capabilities': [
            'financial_metric_schema',
            'financial_source_availability',
            'financial_statement_loader',
            'metric_normalization',
            'quarterly_signal_calculation',
            'financial_signal_classification'],
        'industry_template_capabilities': [
            'industry_specific_financial_variable_mapping'],
        'single_ticker_pilot': [
            '300308.SZ financial-to-thesis impact mapping'],
        'not_assumed_to_generalize': [
            '300308-specific thesis claims',
            'AI optical module product variable mapping'],
        'next_required_for_generalization': [
            'add industry templates',
            'test on second ticker',
            'connect structured financial data source'],
        'note': '300308.SZ pilot proves framework capability. Single-ticker logic does NOT automatically generalize to all stocks.'
    }}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true')
    p.add_argument('--markdown',action='store_true')
    args=p.parse_args()
    r=build(None,args.ticker)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
