"""Offline final diagnostics with explicit source and horizon conventions."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
from scipy.stats import rankdata
import engine as e
from editorial_audit import diagnostics
ROOT=e.ROOT

def run():
    diagnostics()
    cp=e.read(ROOT/'outputs/classifier_predictions.csv');cl=[]
    # Inherited origin-window assessment extends outcomes into March 2026.
    for scope,start,end in [('origin_window','2016-01','2025-12'),('outcome_bounded','2015-12','2025-09')]:
        rs=[x for x in cp if start<=x['signal_month']<=end]
        y=np.array([int(x['next3m_loss10'])for x in rs]);p=np.array([float(x['probability'])for x in rs]);b=np.array([float(x['baseline_probability'])for x in rs]);positive=y==1
        auc=(rankdata(p)[positive].sum()-positive.sum()*(positive.sum()+1)/2)/(positive.sum()*(~positive).sum())
        cl.append(dict(scope=scope,first_signal=start,last_signal=end,last_outcome=e.label(e.mn(end)+3),n=len(rs),events=int(y.sum()),brier=np.mean((p-y)**2),baseline_brier=np.mean((b-y)**2),auc=auc))
    e.write(e.OUT/'classifier_horizon_audit.csv',cl)
    risk=[]
    for a,b in [('2000-01','2026-09'),('2016-01','2025-12')]:
        for name in ['QQQ','SPY','Vol15','RegimeRule','BoydSimple']:
            s=e.simulate(name,a,b);m=e.metrics(s);rf=e.R[np.searchsorted(e.D,s['dates']),4];ex=s['r']-rf
            downside=np.sqrt(np.mean(np.minimum(ex,0)**2))
            risk.append(dict(strategy=name,start=a,end=b,months=len(ex),sortino_reserve_threshold=float(np.sqrt(12)*ex.mean()/downside),cvar95_month=m['cvar95_month'],turnover_two_way_annual=m['turnover_two_way_annual'],orders_per_year=m['orders_per_year'],scope='Sortino is a standardized monthly summary; denominator includes all months, threshold is modeled reserve return'))
    e.write(e.OUT/'downside_turnover_metrics.csv',risk)
    # Recompute original source-return mapping, not just compare output hashes.
    price={(r['ticker'],r['month']):float(r['price'])for r in e.read(ROOT/'raw/raw_adjusted_prices.csv')}
    err=[]
    for row in e.read(ROOT/'raw/prior_returns.csv'):
        m=row['month'];prev=e.label(e.mn(m)-1)
        for a,col in [('QQQ','QQQ'),('US','VTI_proxy'),('BOND','BND_proxy'),('GOLD','Gold_proxy'),('SPY','SPY')]:
            src=row.get(col+'_source')or'SPY';gross=price[src,m]/price[src,prev]
            if src=='GOLD_SPOT':gross*=(1-.004)**(1/12)
            err.append({'asset':a,'month':m,'absolute_error':abs(gross-1-float(row[col]))})
    audit={'comparisons':len(err),'max_absolute_error':max(x['absolute_error']for x in err),'scope':'Independent reconstruction from inherited adjusted prices; not vendor-independent authentication'}
    (ROOT/'audit/raw_to_return_reconstruction.json').write_text(json.dumps(audit,indent=2))
    assert audit['max_absolute_error']<1e-12
    print(json.dumps({'classifier':cl,'raw':audit},indent=2))

if __name__=='__main__':run()
