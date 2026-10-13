"""Generate follow-up tables directly from executed numerical output."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'outputs/followup';T=ROOT/'manuscript/tables'
N={'QQQ':'QQQ','RegimeRule':'R','BoydSimple':'M','Trend10_QQQ_Reserve':'Trend10'}
def table(name,headers,rows,cols):
 s='\\begin{tabular}{@{}'+cols+'@{}}\\toprule\n'+' & '.join(headers)+'\\\\\\midrule\n'
 s+='\n'.join(' & '.join(r)+'\\\\'for r in rows)+'\n\\bottomrule\\end{tabular}\n';(T/name).write_text(s)
def main():
 q=json.loads((O/'qqq_reconciliation.json').read_text());rows=[]
 for title,key in [('Frozen adjusted monthly prices','frozen_monthly_return'),('Daily adjusted closes','adjusted_close_return'),('Daily ex-date reinvestment','daily_ex_date_return'),('Month-end reinvestment','monthend_reinvestment_return'),('Unadjusted-for-dividend close ratio','price_return'),('Issuer market total return','issuer_market_return'),('Issuer NAV total return','issuer_nav_return')]:rows.append([title,f'{100*q[key]:.4f}'])
 table('qqq_followup.tex',['Convention','Return (\\%)'],rows,'lr')
 a=pd.read_csv(O/'qqq_alternate_source_metrics.csv');b=pd.read_csv(O/'qqq_fixed_range_metrics.csv');rows=[]
 for n in ['QQQ','RegimeRule','BoydSimple']:
  for source,title in [('frozen','Frozen'),('QQQ_daily_adjusted_replacement','Daily QQQ')]:
   x=a[(a.strategy==n)&(a.scope==source)].iloc[0];rows.append([N[n],title,f'{100*x.cagr:.3f}',f'{100*x.max_dd:.3f}'])
  x=b[b.strategy==n];rows.append([N[n],'Fixed stress range',f'{100*x.cagr.min():.3f}--{100*x.cagr.max():.3f}',f'{100*x.max_dd.min():.3f}--{100*x.max_dd.max():.3f}'])
 table('qqq_sensitivity.tex',['Method','Inputs','CAGR','Max. DD'],rows,'llrr')
 d=pd.read_csv(O/'execution_metrics.csv');rows=[]
 for start,label in [('2012-01','2012--2026'),('2016-01','2016--2025')]:
  for name in N:
   for mode,clock in [('boundary_close','Close'),('next_open','Next open')]:
    x=d[(d.start==start)&(d.strategy==name)&(d.scope==mode)&(d.cost==.001)].iloc[0]
    rows.append([label,N[name],clock,f'{100*x.cagr:.2f}',f'{100*x.max_dd:.2f}',f'{100*x.daily_max_dd:.2f}'])
 table('daily_execution.tex',['Period','Method','Clock','CAGR','Month DD','Daily DD'],rows,'lllrrr')
 rows=[]
 for start,label in [('2012-01','2012--2026'),('2016-01','2016--2025')]:
  for name in N:
   x=d[(d.start==start)&(d.strategy==name)&(d.scope=='next_open')&(d.cost==.0025)].iloc[0]
   rows.append([label,N[name],f'{100*x.cagr:.2f}',f'{100*x.max_dd:.2f}',f'{100*x.daily_max_dd:.2f}'])
 table('daily_cost25.tex',['Period','Method','CAGR','Month DD','Daily DD'],rows,'llrrr')
if __name__=='__main__':main()
