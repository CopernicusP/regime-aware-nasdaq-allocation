"""Additional diagnostics for the English editorial release.
No new strategy selection. Uses frozen v2 policies and returns.
Run from any directory: python code/editorial_audit.py
"""
from pathlib import Path
import csv,json,hashlib,sys,platform
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rs):
 if not rs:raise ValueError('No records')
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def reconcile():
 checks=[]
 for name in ['metrics.csv','crisis_periods.csv','classifier_eval.csv','real_performance.csv','sensitivities.csv','bootstrap_conditional.csv','audit_tests.csv','hindsight_static_grid.csv','bootstrap_pipeline_draws.csv','bootstrap_pipeline_summary.csv']:
  p=ROOT/'outputs'/name;ref=ROOT/'reference_outputs'/name
  if not p.exists():continue
  a=read(p);b=read(ref);assert len(a)==len(b),(name,'rowcount')
  err=0.;bad=[]
  for i,(x,y) in enumerate(zip(a,b)):
   assert set(x)==set(y),(name,'columns')
   for k in x:
    try:
     u,v=float(x[k]),float(y[k]);d=abs(u-v)
     if np.isnan(u)and np.isnan(v):continue
     err=max(err,d)
     if not np.isclose(u,v,rtol=1e-8,atol=1e-9,equal_nan=True):bad.append((i,k,u,v))
    except ValueError:
     if x[k]!=y[k]:bad.append((i,k,x[k],y[k]))
  assert not bad,(name,bad[:4])
  checks.append({'file':name,'rows':len(a),'max_absolute_numeric_change':err,'passed':True})
 write(ROOT/'audit/recomputed_vs_v2.csv',checks)
 return checks

def diagnostics():
 logs=read(ROOT/'outputs/monthly_paths_weights.csv')
 rr=read(ROOT/'raw/monthly_returns.csv');returnmap={r['month']:np.array([float(r[a])for a in ['QQQ','US','BOND','GOLD','CASH']])for r in rr}
 serial=[];fee=[]
 for name in ['QQQ','RegimeRule','BoydSimple']:
  allrows=[r for r in logs if r['strategy']==name]
  for start,end in [('2000-01','2026-09'),('2016-01','2025-12')]:
   rows=[r for r in allrows if start<=r['return_month']<=end]
   x=np.array([float(r['net_return'])-returnmap[r['return_month']][4] for r in rows]);n=len(x);u=x-x.mean()
   gamma=np.array([np.dot(u[k:],u[:n-k])/n for k in range(12)])
   var12=12*gamma[0]+2*np.dot(np.arange(11,0,-1),gamma[1:])
   serial.append({'strategy':name,'start':start,'end':end,'path_scope':'slice of full-history strategy; not fresh-start subperiod','n':n,'iid_scaled_sharpe':float(np.sqrt(12)*x.mean()/x.std(ddof=1)),'serial_adjusted_12month_arithmetic_sharpe':float(12*x.mean()/np.sqrt(var12)) if var12>0 else float('nan'),'lag1_autocorrelation':float(gamma[1]/gamma[0]),'note':'Stationary finite-horizon arithmetic-sum diagnostic with 11 sample autocovariances, not a CAGR or significance test'})
  if name=='QQQ':continue
  cagrvals=[]
  for c in [0.,.00025,.001,.0025]:
   hold=np.array([0.,0.,0.,0.,100000.]);totalfee=0.
   for k,row in enumerate(allrows):
    value=hold.sum()
    if row['traded']=='True':
     w=np.array([float(row[a])for a in ['QQQ','US','BOND','GOLD','CASH']]);low,high=0.,value
     for _ in range(70):
      after=(low+high)/2;tr=after if k==0 else np.abs(after*w-hold).sum()
      if after+c*tr>value:high=after
      else:low=after
     nv=(low+high)/2;totalfee+=value-nv;hold=nv*w
    hold*=1+returnmap[row['return_month']]
   g=(hold.sum()/100000.)**(12/len(allrows))-1;cagrvals.append(g)
   fee.append({'strategy':name,'per_side_cost_bps':c*10000,'cagr':g,'terminal_100k':hold.sum(),'dollar_fees':totalfee,'policy':'Replay original base-case trade dates and post-trade target weights; no re-optimization'})
  assert all(a>=b-1e-10 for a,b in zip(cagrvals,cagrvals[1:])),('nonmonotone fixed-policy fees',name)
 write(ROOT/'outputs/serial_sharpe_diagnostic.csv',serial);write(ROOT/'outputs/fixed_policy_fee_replay.csv',fee)
 return serial,fee

if __name__=='__main__':
 s,f=diagnostics()
 print(json.dumps({'scope':'Fresh fixed-policy fee and serial-dependence diagnostics only; inherited reconciliation is separate','fee_replay_rows':len(f),'serial_rows':len(s)},indent=2))
