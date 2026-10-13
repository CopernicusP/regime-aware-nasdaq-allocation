"""Finite, offline 2026 follow-up. Original raw files and parameters never change.
Yahoo bars are vendor historical OHLC (split-adjustment conventions retained).
Adjusted opens are explicitly total-return units, not fabricated observed quotes.
"""
from pathlib import Path
import json, hashlib, sys
import numpy as np
import pandas as pd
import exchange_calendars as xc
import engine as e
ROOT=e.ROOT; SRC=ROOT/'audit/followup/source'; OUT=ROOT/'outputs/followup'; OUT.mkdir(exist_ok=True)
TICKERS=['QQQ','VTI','BND','GLD','BIL','SPY']
BASE_R=e.R.copy();BASE_P=e.P.copy();BASE_SPY=e.SPY.copy()

def load(ticker):
    p=SRC/f'{ticker}_daily.json'; raw=json.loads(p.read_text())['chart']['result'][0]
    q=raw['indicators']['quote'][0]
    idx=pd.to_datetime(raw['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
    d=pd.DataFrame(q,index=idx);d['adjclose']=raw['indicators']['adjclose'][0]['adjclose']
    d['dividend']=0.
    for x in raw.get('events',{}).get('dividends',{}).values():
        day=pd.to_datetime(x['date'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
        if day in d.index:d.loc[day,'dividend']+=x['amount']
    assert not d.index.duplicated().any(),ticker
    assert d.index.is_monotonic_increasing,ticker
    assert d[['open','high','low','close','adjclose']].notna().all().all(),ticker
    assert (d[['open','high','low','close','adjclose']]>0).all().all(),ticker
    assert (d['high']+1e-5>=d[['open','close']].max(axis=1)).all(),ticker
    assert (d['low']-1e-5<=d[['open','close']].min(axis=1)).all(),ticker
    d['factor']=d.adjclose/d.close;d['adjopen']=d.open*d.factor
    return d,raw.get('events',{}).get('splits',{})

def install(r,spy=None):
    e.R=np.array(r,copy=True);e.P=np.vstack([np.ones(5),np.cumprod(1+e.R,axis=0)])
    e.SPY=BASE_SPY.copy()if spy is None else spy.copy()
    e.EST=e.Estimator();e.ESTM=e.Estimator(True)

def summary(s,scope):
    r=s['r'];p=np.r_[1.,np.cumprod(1+r)]
    dd=1-p/np.maximum.accumulate(p)
    return dict(scope=scope,strategy=s['name'],start=e.label(int(s['dates'][0])),end=e.label(int(s['dates'][-1])),months=len(r),cagr=p[-1]**(12/len(r))-1,vol=np.std(r,ddof=1)*np.sqrt(12),max_dd=max(dd),terminal=p[-1],solver_failures=sum(not z.get('solver_success',True)for z in s['log']))

def fee_solve(hold,w,cost,initial=False):
    nav=hold.sum();lo=0.;hi=nav
    for _ in range(55):
        after=(lo+hi)/2;trade=after*w if initial else np.abs(after*w-hold)
        if after+cost*trade.sum()>nav:hi=after
        else:lo=after
    after=(lo+hi)/2
    return after*w,nav-after

def daily_sim(name,start,end,mode,cost,panels):
    """Signal/pre-trade state uses close only. Orders retain that target at open.
    Monthly period includes initial wait in external cash for next-open branch.
    Each intervening session marks total-return units at actual adjusted close.
    """
    ids=np.where((e.D>=e.mn(start))&(e.D<=e.mn(end)))[0]
    dates=panels['QQQ'].index
    C=np.column_stack([panels[t].adjclose.reindex(dates)for t in TICKERS[:5]])
    O=np.column_stack([panels[t].adjopen.reindex(dates)for t in TICKERS[:5]])
    loc={d:i for i,d in enumerate(dates)}
    hold=np.array([0.,0.,0.,0.,100000.]);navs=[hold.sum()];daily=[hold.sum()];logs=[];laststate=None
    for n,i in enumerate(ids):
        month=e.label(int(e.D[i]));sigmonth=e.label(int(e.D[i]-1))
        before=dates[dates.strftime('%Y-%m')==sigmonth][-1]
        sessions=dates[dates.strftime('%Y-%m')==month];first=sessions[0];finish=sessions[-1]
        pre=hold/hold.sum()
        if name=='Trend10_QQQ_Reserve':
            q=float(e.P[i,0]>e.P[max(0,i-9):i+1,0].mean());w=np.array([q,0,0,0,1-q]);info={'state':None};reb=True
        else:
            w,info,est=e.target(name,i,pre,cost=cost)
            reb=n==0 or name!='QQQ'
            safety=np.sqrt(12*pre[:4]@est.cov@pre[:4])<=info['vol_budget']*1.001 and pre[:2].sum()<=info['equity_cap']+1e-7
            if reb and n>0 and name!='QQQ'and laststate==info['state']and safety and np.max(np.abs(w-pre))<.02:reb=False
        frozen_w=w.copy();close_nav=hold.sum();fee=0.
        if mode=='boundary_close':
            if reb:hold,fee=fee_solve(hold,w,cost,n==0)
            prev=before
            for day in sessions:
                hold*=C[loc[day]]/C[loc[prev]];daily.append(hold.sum());prev=day
        else:
            # No gap return on undeployed external cash. Subsequent positions carry gap.
            if n>0:hold*=O[loc[first]]/C[loc[before]]
            if reb:hold,fee=fee_solve(hold,frozen_w,cost,n==0)
            hold*=C[loc[first]]/O[loc[first]];daily.append(hold.sum());prev=first
            for day in sessions[1:]:
                hold*=C[loc[day]]/C[loc[prev]];daily.append(hold.sum());prev=day
        assert np.isfinite(hold).all()and(hold>=0).all()
        navs.append(hold.sum());logs.append(dict(signal_close=str(before.date()),execution_date=str((before if mode=='boundary_close'else first).date()),month=month,traded=reb,fee=fee,nav=hold.sum(),signal_nav=close_nav,solver_success=info.get('solver_success',True),**{a:float(w[k])for k,a in enumerate(e.ASSETS)}));laststate=info['state']
    navs=np.array(navs);dv=np.array(daily);dmax=float(np.max(1-dv/np.maximum.accumulate(dv)))
    return dict(name=name,dates=e.D[ids],r=navs[1:]/navs[:-1]-1,log=logs,daily_max_dd=dmax)

def reconcile(d):
    start=pd.Timestamp('2008-09-30');end=pd.Timestamp('2009-09-30');dd=d.loc[start:end]
    base=dd.close.iloc[0];p=dd.close.values;dist=dd.dividend.values
    ex=float(np.prod((p[1:]+dist[1:])/p[:-1])-1)
    # Dividends accrue as receivables on ex date, then buy at that month's final close.
    shares=1.;cash=0.;month_gross=[]
    for month,block in dd.iloc[1:].groupby(dd.iloc[1:].index.to_period('M')):
        cash+=shares*block.dividend.sum();shares+=cash/block.close.iloc[-1];cash=0.
        month_gross.append(dict(month=str(month),dividend_per_share=float(block.dividend.sum()),close=float(block.close.iloc[-1])))
    monthend=shares*dd.close.iloc[-1]/base-1
    frozen=36.62/33.54-1
    adj=dd.adjclose.iloc[-1]/dd.adjclose.iloc[0]-1
    lo=(36.62-.005)/(33.54+.005)-1;hi=(36.62+.005)/(33.54-.005)-1
    # Without reinvestment, positive entitled distributions imply total terminal wealth >= price-only wealth.
    result=dict(period_start=str(start.date()),period_end=str(end.date()),vendor_start_close=float(base),sec_exchange_start_close=38.91,vendor_end_close=float(p[-1]),price_return=float(p[-1]/base-1),daily_ex_date_return=ex,monthend_reinvestment_return=float(monthend),adjusted_close_return=float(adj),frozen_monthly_return=frozen,issuer_market_return=.0841,issuer_nav_return=.0844,issuer_nav_start=39.20,issuer_nav_end=42.29,rounding_interval=[lo,hi],frozen_minus_daily_bp=float((frozen-adj)*1e4),timing_difference_bp=float((ex-monthend)*1e4),issuer_gap_remaining_bp=float((adj-.0841)*1e4),yahoo_dividends_rounded_3dp=month_gross,pay_date_method='Not imputed: actual payment dates unavailable in downloaded chart. Same-endpoint nonnegative distribution lower bound used instead.',conclusion='Not fully reconciled. SEC and vendor corroborate 38.91 start close. Issuer 8.41% is below the 8.5839% endpoint price-only return; timing alone cannot reconcile on these endpoints. 2010 issuer prospectus specifies consolidated close and ex-date reinvestment. Exact underlying issuer quotes remain unavailable; a report error or endpoint-field inconsistency is possible, not established.')
    (OUT/'qqq_reconciliation.json').write_text(json.dumps(result,indent=2));return result

def run():
    panels={};qa=[]
    cal=xc.get_calendar('XNYS',start='2011-12-01',end='2026-10-01');expected=cal.sessions_in_range('2011-12-30','2026-09-30').tz_localize(None)
    for t in TICKERS:
        d,splits=load(t);panels[t]=d
        actual=d.loc['2011-12-30':'2026-09-30'].index
        missing=expected.difference(actual);extra=actual.difference(expected)
        qa.append(dict(ticker=t,rows=len(d),first=str(d.index[0].date()),last=str(d.index[-1].date()),live_rows=len(actual),missing_sessions=[str(x.date())for x in missing],extra_sessions=[str(x.date())for x in extra],split_events=splits,sha256=hashlib.sha256((SRC/f'{t}_daily.json').read_bytes()).hexdigest()))
        assert len(missing)==len(extra)==0,(t,missing,extra)
    (OUT/'daily_panel_quality.json').write_text(json.dumps(qa,indent=2))
    rec=reconcile(panels['QQQ']);print('RECONCILIATION',json.dumps({k:v for k,v in rec.items()if not isinstance(v,(list,dict))}),flush=True)
    monthly={t:panels[t].adjclose.groupby(panels[t].index.to_period('M')).last().pct_change()for t in TICKERS}
    r=BASE_R.copy()
    for i,m in enumerate(e.D):
        if pd.Period(e.label(m),'M')in monthly['QQQ'].index:r[i,0]=monthly['QQQ'].get(pd.Period(e.label(m),'M'))
    assert np.isfinite(r).all()
    rows=[]
    for scenario,rr in [('frozen',BASE_R),('QQQ_daily_adjusted_replacement',r)]:
        install(rr)
        for name in ['QQQ','RegimeRule','BoydSimple']:
            rows.append(summary(e.simulate(name),scenario))
    e.write(OUT/'qqq_alternate_source_metrics.csv',rows)
    ids=np.where((e.D>=e.mn('2008-10'))&(e.D<=e.mn('2009-09')))[0];g=np.prod(1+BASE_R[ids,0]);sens=[]
    for shock in [-.01,.01]:
        factor=(g+shock)/g
        for placement in ['uniform']+[e.label(e.D[j])for j in ids]:
            rr=BASE_R.copy()
            ix=ids if placement=='uniform'else np.where(e.D==e.mn(placement))[0]
            rr[ix,0]=(1+rr[ix,0])*factor**(1/len(ix))-1
            assert abs(np.prod(1+rr[ids,0])-(g+shock))<1e-12
            install(rr)
            for name in ['QQQ','RegimeRule','BoydSimple']:
                z=summary(e.simulate(name),f'stress_{shock:+.2f}_{placement}');z.update(horizon_return_shock_bp=int(shock*1e4),placement=placement);sens.append(z)
        print('STRESS DONE',shock,flush=True)
    e.write(OUT/'qqq_fixed_range_metrics.csv',sens)
    rows=[];paths=[]
    rr=BASE_R.copy();spy=BASE_SPY.copy()
    for k,t in enumerate(TICKERS[:5]):
        for i,m in enumerate(e.D):
            val=monthly[t].get(pd.Period(e.label(m),'M'),np.nan)
            if np.isfinite(val):rr[i,k]=val
    for i,m in enumerate(e.D):
        val=monthly['SPY'].get(pd.Period(e.label(m),'M'),np.nan)
        if np.isfinite(val):spy[i]=val
    install(rr,spy)
    for start,end in [('2012-01','2026-09'),('2016-01','2025-12')]:
        for mode in ['boundary_close','next_open']:
            for cost in [.001,.0025]:
                for name in ['QQQ','RegimeRule','BoydSimple','Trend10_QQQ_Reserve']:
                    s=daily_sim(name,start,end,mode,cost,panels);z=summary(s,mode);z.update(cost=cost,daily_max_dd=s['daily_max_dd']);rows.append(z)
                    paths.extend([dict(strategy=name,start=start,end=end,mode=mode,cost=cost,**x)for x in s['log']])
        print('DAILY DONE',start,end,flush=True)
    e.write(OUT/'execution_metrics.csv',rows);e.write(OUT/'execution_logs_PRIVATE.csv',paths)
    e.write(OUT/'daily_monthly_returns_PRIVATE.csv',[dict(month=e.label(int(m)),**{a:float(rr[i,k])for k,a in enumerate(e.ASSETS)},SPY=float(spy[i]))for i,m in enumerate(e.D)])
    install(BASE_R)
    # Immutable input proof; read manifest recorded before this follow-up.
    (OUT/'run_summary.json').write_text(json.dumps(dict(qqq_sensitivity_rows=len(sens),execution_rows=len(rows),original_raw_overwritten=False,parameter_retuning=False,provenance='Yahoo public chart, not CRSP/WRDS or IBKR; daily replacement may share upstream lineage with Digrin',publication_scope='aggregate research statistics only; raw bars, paths and figure-level histories private'),indent=2))
if __name__=='__main__':run()
