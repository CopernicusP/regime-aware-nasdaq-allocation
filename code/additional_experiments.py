"""Pre-recorded retrospective attribution controls and start-date sensitivity."""
import json
import numpy as np
from scipy.optimize import brentq
import engine as e

def ledger(start,end,weight_fn,name,cost=.001):
    ids=np.where((e.D>=e.mn(start))&(e.D<=e.mn(end)))[0]
    hold=np.array([0.,0.,0.,0.,100000.]);path=[hold.sum()];weights=[];turns=[];fees=[];logs=[];orders=[]
    for k,i in enumerate(ids):
        nav=hold.sum();w=np.asarray(weight_fn(i),float)
        assert np.isfinite(w).all() and w.min()>=0 and abs(w.sum()-1)<1e-12
        lo,hi=0.,nav
        for _ in range(60):
            mid=(lo+hi)/2
            trade=mid*w if k==0 else abs(mid*w-hold)
            if mid+cost*trade.sum()>nav:hi=mid
            else:lo=mid
        after=(lo+hi)/2;trade=after*w if k==0 else abs(after*w-hold)
        hold=after*w*(1+e.R[i]);path.append(hold.sum());weights.append(w);turns.append(trade.sum()/nav);fees.append(nav-after);orders.append((trade>nav*1e-6).sum())
        logs.append({'solver_success':True})
    path=np.array(path);weights=np.array(weights)
    return {'name':name,'dates':e.D[ids],'r':path[1:]/path[:-1]-1,'path':path,'W':weights,'log':logs,'two_way':np.array(turns),'orders':np.array(orders),'fees':np.array(fees),'terminal_after_liquidation_fx':path[-1]*(1-cost),'start_capital':100000.,'fx_initial':0.}

def const_sim(w,a,b,name):return ledger(a,b,lambda i:w,name)

def trend_sim(a,b):
    def rule(i):
        q=float(e.P[i,0]>e.P[max(0,i-9):i+1,0].mean())
        return np.array([q,0,0,0,1-q])
    return ledger(a,b,rule,'Trend10_QQQ_Reserve')

def benchmark_weights(name,a,b):
    active=e.simulate(name,a,b)
    mean_w=active['W'].mean(0);target=np.std(active['r'],ddof=1)*np.sqrt(12)
    def f(q):return np.std(const_sim(np.array([q,0,0,0,1-q]),a,b,'calibration')['r'],ddof=1)*np.sqrt(12)-target
    q=brentq(f,0.,1.,xtol=1e-12) if f(0)*f(1)<0 else (0. if abs(f(0))<abs(f(1)) else 1.)
    return mean_w,np.array([q,0,0,0,1-q]),target

def run():
    rows=[];specs=[];tests=[];paths=[];rng=np.random.default_rng(13102026)
    for a,b,ca,cb,label in [('2000-01','2026-09','2000-01','2026-09','hindsight_full_sample'),('2016-01','2025-12','2010-01','2015-12','validation_frozen')]:
        qqq=e.simulate('QQQ',a,b)
        for name in ['RegimeRule','BoydSimple']:
            mean_w,risk_w,vol=benchmark_weights(name,ca,cb)
            specs += [{'active':name,'design':label,'calibration_start':ca,'calibration_end':cb,'comparator':c,'target_validation_vol':vol,**dict(zip(e.ASSETS,map(float,w)))} for c,w in [('MeanWeights',mean_w),('RiskMatchedQQQ',risk_w)]]
            results=[e.simulate(name,a,b),const_sim(mean_w,a,b,name+'_MeanWeights'),const_sim(risk_w,a,b,name+'_RiskMatchedQQQ'),trend_sim(a,b)]
            for s in results:
                m=e.metrics(s,qqq);m.update(active=name,design=label,mean_equity=float(s['W'][:,:2].sum(1).mean()));rows.append(m)
                paths += [{'active':name,'design':label,'strategy':s['name'],'month':e.label(int(d)),'net_return':float(r)} for d,r in zip(s['dates'],s['r'])]
            if label=='validation_frozen':
                active=results[0]
                for s in results[1:]:
                    delta=np.log1p(active['r'])-np.log1p(s['r']);n=len(delta);B=9999;L=12
                    starts=rng.integers(0,n,size=(B,int(np.ceil(n/L))));ix=((starts[:,:,None]+np.arange(L))%n).reshape(B,-1)[:,:n]
                    boot=12*delta[ix].mean(1);obs=12*delta.mean();pv=(1+np.sum(boot-obs>=obs))/(B+1)
                    tests.append({'active':name,'comparator':s['name'],'annual_log_growth_difference':obs,'low95':float(np.quantile(boot,.025)),'high95':float(np.quantile(boot,.975)),'one_sided_p':pv,'bonferroni_six_p':min(1,6*pv),'B':B,'block':L,'design':'Retrospective exploratory; conditional on realized policies'})
    e.write(e.OUT/'matched_control_metrics.csv',rows);e.write(e.OUT/'matched_control_weights.csv',specs);e.write(e.OUT/'matched_control_tests.csv',tests);e.write(e.OUT/'matched_control_paths.csv',paths)
    rolling=[]
    for years in [5,10]:
        for year in range(2000,2026-years+1):
            a=f'{year}-01';b=f'{year+years-1}-12';q=e.simulate('QQQ',a,b);qm=e.metrics(q)
            for name in ['RegimeRule','BoydSimple']:
                m=e.metrics(e.simulate(name,a,b))
                rolling.append({'strategy':name,'years':years,'start':a,'end':b,'cagr':m['cagr'],'qqq_cagr':qm['cagr'],'cagr_difference':m['cagr']-qm['cagr'],'max_dd':m['max_dd'],'qqq_max_dd':qm['max_dd'],'dd_reduction':qm['max_dd']-m['max_dd'],'water':m['longest_water_months'],'qqq_water':qm['longest_water_months']})
    e.write(e.OUT/'rolling_start_metrics.csv',rolling)
    summary=[]
    for name in ['RegimeRule','BoydSimple']:
        for years in [5,10]:
            r=[x for x in rolling if x['strategy']==name and x['years']==years]
            summary.append({'strategy':name,'years':years,'windows':len(r),'growth_wins':sum(x['cagr_difference']>0 for x in r),'drawdown_wins':sum(x['dd_reduction']>0 for x in r),'median_growth_difference':float(np.median([x['cagr_difference'] for x in r])),'min_growth_difference':min(x['cagr_difference'] for x in r),'max_growth_difference':max(x['cagr_difference'] for x in r),'overlap_warning':'Windows overlap; counts are descriptive, not binomial trials.'})
    e.write(e.OUT/'rolling_start_summary.csv',summary)
    blocks=[]
    for a,b in [('2000-01','2026-09'),('2016-01','2025-12')]:
        q=e.simulate('QQQ',a,b)
        for name in ['RegimeRule','BoydSimple']:
            s=e.simulate(name,a,b);delta=np.log1p(s['r'])-np.log1p(q['r']);obs=12*delta.mean();n=len(delta)
            for L in [6,12,24]:
                ix=((rng.integers(0,n,size=(9999,int(np.ceil(n/L))))[:,:,None]+np.arange(L))%n).reshape(9999,-1)[:,:n]
                bt=12*delta[ix].mean(1)
                blocks.append({'strategy':name,'start':a,'end':b,'block':L,'B':9999,'observed':obs,'low95':float(np.quantile(bt,.025)),'high95':float(np.quantile(bt,.975))})
    e.write(e.OUT/'block_length_sensitivity.csv',blocks)
    print(json.dumps({'matched_rows':len(rows),'rolling_windows_times_methods':len(rolling),'comparator_tests':len(tests)},indent=2))
if __name__=='__main__':run()
