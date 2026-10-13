"""Prespecified sensitivity, self-financing audit, causal checks and descriptive frontiers.
Run after engine.py. No live orders, no network requests."""
from __future__ import annotations
import json,itertools,math
import numpy as np
import engine as e
O=e.OUT
CORE=['Vol15','RegimeRule','BoydSimple','BoydRidge','RegimeRobust','ProbabilityRobust']

def run():
 rows=[]
 specs=[('base',{}),('cost_2.5bp',{'cost':.00025}),('cost_25bp',{'cost':.0025}),('risk_12pct',{'vol':.12}),('risk_18pct',{'vol':.18}),('delay_one_month',{'delay':1}),('cash_realized_zero',{'cash_zero':True}),('no_trade_band_zero',{'band':0}),('flat_0.35',{'flat':.35}),('flat_1.99',{'flat':1.99}),('flat_1.99_1million',{'flat':1.99,'capital':1000000}),('FX_3bp_each_end',{'fx':.0003}),('FX_100bp_each_end',{'fx':.01})]
 bench=e.simulate('QQQ')
 for n in ['RegimeRule','BoydSimple','RegimeRobust','Vol15']:
  for tag,kw in specs:
   s=e.simulate(n,**kw);r=e.metrics(s,bench);r.update(case=tag,assumptions=json.dumps(kw));rows.append(r)
 for tag,kw in [('no_state_constraints',{'no_regime':True}),('mean_penalty_0',{'no_uncertainty':True}),('mean_penalty_half',{'penalty':.5}),('cov12',{'covwindow':12}),('cov60',{'covwindow':60}),('MA8',{'ma':8}),('MA12',{'ma':12})]:
  s=e.simulate('RegimeRobust',**kw);r=e.metrics(s,bench);r.update(case=tag,assumptions=json.dumps(kw));rows.append(r)
 e.RISK_FLOOR_ANNUAL=[.12,.10,.04,.10];e.EST.cache.clear();e.ESTM.cache.clear()
 for n in ['RegimeRule','BoydSimple','RegimeRobust']:
  s=e.simulate(n);r=e.metrics(s,bench);r.update(case='risk_floor_12_10_4_10',assumptions='variance floors to stress rounded low-price historical proxies');rows.append(r)
 e.RISK_FLOOR_ANNUAL=None;e.EST.cache.clear();e.ESTM.cache.clear()
 e.write(O/'sensitivities.csv',rows)
 # A second accounting implementation uses physical dollar holdings before/after trading.
 audits=[]
 for n in e.METHODS:
  s=e.simulate(n);hold=np.array([0.,0,0,0,100000.]);path=[100000.];i0=int(np.searchsorted(e.D,e.mn('2000-01')))
  for k,log in enumerate(s['log']):
   if log['traded']:
    val=hold.sum();w=s['W'][k];lo=0.;hi=val
    # Monotone bisection rather than main engine's fixed point.
    for _ in range(70):
     after=(lo+hi)/2;turn=np.abs(after*w-hold).sum() if k else after*w.sum()
     if after+.001*turn>val:hi=after
     else:lo=after
    hold=(lo+hi)/2*w
   r=e.R[i0+k].copy()
   if n=='SPY':r[0]=e.SPY[i0+k]
   hold*=1+r;path.append(hold.sum())
  err=float(np.max(np.abs(np.array(path)/s['path']-1)))
  budget_max=max([12*s['W'][k,:4]@e.EST.get(i0+k,'simple'if n=='BoydSimple'else'ridge').cov@s['W'][k,:4]-log['vol_budget']**2 for k,log in enumerate(s['log'])] or [0])
  audits.append({'strategy':n,'independent_accounting_max_relative_error':err,'weights_sum_error':float(np.max(np.abs(s['W'].sum(1)-1))),'minimum_weight':float(s['W'].min()),'lookahead_mature_label_violations':sum(x['train_label_end_index']>x['signal_index']for x in s['log']),'solver_failures':sum(not x.get('solver_success',True)for x in s['log']),'maximum_optimizer_estimated_variance_slack_violation':budget_max if n not in ['QQQ','SPY','Vol15','RegimeRule']else None})
  assert err<1e-9
 # Future information perturbation: corrupt later returns and rebuild features/cache.
 cut=int(np.searchsorted(e.D,e.mn('2016-01')));savedR=e.R.copy();savedP=e.P.copy();savedE=e.EST;savedM=e.ESTM
 before={n:e.target(n,cut,np.array([.4,.2,.1,.1,.2]))[0]for n in CORE}
 e.R[cut:,:4]+=np.array([.1,-.1,.05,-.05]);e.P=np.vstack([np.ones(5),np.cumprod(1+e.R,axis=0)]);e.EST=e.Estimator();e.ESTM=e.Estimator(True)
 causal={n:float(np.max(np.abs(e.target(n,cut,np.array([.4,.2,.1,.1,.2]))[0]-before[n])))for n in CORE}
 e.R[:]=savedR;e.P=savedP;e.EST=savedE;e.ESTM=savedM
 assert max(causal.values())<1e-10
 e.write(O/'audit_tests.csv',audits)
 (O/'causal_check.json').write_text(json.dumps({'perturbation_cut':'2016-01 onward changed; Dec2015 signal unchanged','max_weight_error':causal,'not_a_daily_execution_audit':True},indent=2))
 # Complete state transitions and pooled state-average realized allocations, descriptive only.
 rr=[];trans=[]
 for n in ['RegimeRule','BoydSimple','RegimeRobust']:
  s=e.simulate(n);prev=None
  for x in s['log']:
   if n=='RegimeRule' and x['state']!=prev:trans.append({k:x[k]for k in ['signal_month','return_month','score','state','QQQ','US','BOND','GOLD','CASH']});prev=x['state']
  for state in [0,1,2]:
   ix=np.array([x['state']==state for x in s['log']]);v=s['W'][ix].mean(0);rr.append({'strategy':n,'state':state,'months':int(ix.sum()),**{a:float(v[k])for k,a in enumerate(e.ASSETS)}})
 e.write(O/'state_average_weights.csv',rr);e.write(O/'state_transitions.csv',trans)
 # Ex-post 10%-step static simplex frontier: all 1001 portfolios, no deployment claim.
 start=int(np.searchsorted(e.D,e.mn('2000-01')));rets=e.R[start:];months=e.D[start:];alloc=[]
 for q in range(11):
  for u in range(11-q):
   for b in range(11-q-u):
    for g in range(11-q-u-b):alloc.append(np.array([q,u,b,g,10-q-u-b-g])/10)
 a=np.array(alloc);pre=a.copy();wealth=np.ones(len(a))/(1+.001);path=[np.ones(len(a))];prev=np.ones(len(a));out=[]
 for t,d in enumerate(months):
  if t>0 and (d%12+1)in(1,4,7,10):
   f=np.ones(len(a))
   for _ in range(15):f=1-.001*np.abs(f[:,None]*a-pre).sum(1)
   wealth*=f;pre=a.copy()
  gr=1+pre@rets[t];wealth*=gr;pre=pre*(1+rets[t])/gr[:,None];path.append(wealth.copy())
 pp=np.array(path);ret=pp[1:]/pp[:-1]-1
 for k in range(len(a)):
  c=wealth[k]**(12/len(months))-1;v=np.std(ret[:,k],ddof=1)*np.sqrt(12);dd=float(np.max(1-pp[:,k]/np.maximum.accumulate(pp[:,k])));out.append({'id':k,'cagr':float(c),'vol':float(v),'max_dd':dd,**{name:float(a[k,j])for j,name in enumerate(e.ASSETS)}})
 for r in out:r['pareto_cagr_vol']=not any(t['cagr']>=r['cagr']and t['vol']<=r['vol']and(t['cagr']>r['cagr']or t['vol']<r['vol'])for t in out)
 e.write(O/'hindsight_static_grid.csv',out)
 (O/'hindsight_grid_notes.json').write_text(json.dumps({'count':len(out),'label':'EX POST descriptive, not predictive optimization or validation-selected strategy','asset_caps_not_applied':'static simplex includes100%gold and100%cash; optimizer caps differ; not same feasible-set competition','maximum_CAGR':max(out,key=lambda r:r['cagr'])},indent=2))
 print('Sensitivity runs',len(rows),'independent audits',len(audits),'causalcheck',max(causal.values()),'grid',len(out))

if __name__=='__main__':run()
