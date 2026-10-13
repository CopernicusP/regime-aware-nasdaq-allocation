"""Build frozen monthly total-return research data; no network and no trading.
1999 warm-up quotes explicitly transcribed from the web pages in warmup_sources.csv.
"""
from pathlib import Path
import csv,json,shutil,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
PR=ROOT/'raw'
def read(p):
 with open(p,encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows):
 with open(p,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Frozen sources are packaged under raw/. No dependency on previous archives.
for required in ['prior_returns.csv','macro_current_vintage.csv','qqq_warmup_and_bill_rates.csv']:
 if not (PR/required).exists():raise FileNotFoundError(f'Missing frozen input: {required}')
# This file contains no embedded vendor prices. Supply documented local inputs.
for required in ['warmup_1999.csv','warmup_sources.csv']:
 if not (PR/required).exists():raise FileNotFoundError(f'Missing frozen input: {required}')
warm_rows=read(PR/'warmup_1999.csv')
months=[r['month'] for r in warm_rows]
assert months==[f'1999-{m:02d}' for m in range(3,13)]
warm={a:[float(r[a]) for r in warm_rows] for a in ['QQQ','US','BOND','GOLD']}
rates={r['month']:float(r['cash_yield_pct_source']) for r in read(PR/'qqq_warmup_and_bill_rates.csv')}
def prior_month(m):
 y,mm=map(int,m.split('-'));return f'{y if mm>1 else y-1}-{mm-1 if mm>1 else 12:02d}'
rows=[]
for j in range(1,10):
 m=months[j];d={'month':m}
 for a,vals in warm.items():
  d[a]=vals[j]/vals[j-1]-1
  if a=='GOLD':d[a]=(1+d[a])*(1-.004)**(1/12)-1
 d['CASH']=rates[prior_month(m)]/1200-.0009/12
 d['cash_yield_reference']=prior_month(m);d['SPY']='';d['stage']='warmup';rows.append(d)
for r in read(PR/'prior_returns.csv'):
 m=r['month'];d={'month':m,'QQQ':float(r['QQQ']),'US':float(r['VTI_proxy']),'BOND':float(r['BND_proxy']),'GOLD':float(r['Gold_proxy']),'CASH':rates[prior_month(m)]/1200-.0009/12,'cash_yield_reference':prior_month(m),'SPY':float(r['SPY']),'stage':'evaluation'};rows.append(d)
write(ROOT/'raw/monthly_returns.csv',rows)
meta={'assets':['QQQ','US','BOND','GOLD','CASH'],'warmup':'1999-03 to1999-12; nine observed monthly returns, expanding early windows','research_period':'2000-01 to2026-09; 321 returns','cash':'previous-month TB3MS simple monthly equivalent minus assumed9bp annual fund expense; not actual bill total returns; min can be slightly negative','source_coverage':'QQQ actual; US VTSMX until May2001 thenVTI; BOND VBMFX untilApr2007 thenBND; GOLD spot/custody proxy untilNov2004 thenGLD','inflation':'current-vintage CPIAUCSL; missing2025-10 not filled for signals; last available2026-08','taxes':'personal taxes not modeled; hypothetical commissions/spreads/FX only','quality':'Prices rounded2decimals; inherited inputs spot-checked, not fully independent daily audit.'}
(ROOT/'raw/data_notes.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print(len(rows),sum(r['stage']=='evaluation' for r in rows))
