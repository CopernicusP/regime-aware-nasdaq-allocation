"""Offline evidence checks. These checks do not authorize live trading.

Input snippets are transcribed source checkpoints; daily corporate-action and
full historical-vintage data are required separately for a full execution study.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import csv, json, math, hashlib
import numpy as np
import pandas as pd
import exchange_calendars as xc

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'checks/data'; OUT=ROOT/'checks/results'

def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding='utf-8-sig') as f: return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows: raise ValueError('No rows to write')
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def month_shift(month: str,n: int) -> str:
    p=pd.Period(month,freq='M')+n
    return str(p)

def issuer_checks() -> dict:
    monthly=pd.read_csv(ROOT/'raw/monthly_returns.csv').set_index('month')
    mapping={'QQQ':'QQQ','VTI':'US','BND':'BOND','GLD':'GOLD'}
    rows=[]
    for x in read_csv(DATA/'issuer_return_checkpoints.csv'):
        n=int(x['horizon_months']); end=x['end_month']
        start=month_shift(end,1-n)
        z=monthly.loc[start:end,mapping[x['ticker']]].astype(float)
        if len(z)!=n or z.isna().any(): raise ValueError('Incomplete checkpoint coverage')
        gross=float((1+z).prod()); expected=float(x['issuer_return_percent'])
        computed=100*(gross**(12/n)-1) if n>12 else 100*(gross-1)
        rows.append({**x,'computed_return_percent':computed,'difference_bp':100*(computed-expected),
                     'interpretation':'COHERENCE_CHECK_ONLY' if x['source_date_status']=='CONSISTENT_DATE' else 'EXCLUDED_SOURCE_DATE_CONFLICT'})
    write_csv(OUT/'issuer_return_comparison.csv',rows)
    eligible=[x for x in rows if x['source_date_status']=='CONSISTENT_DATE']
    return dict(eligible_windows=len(eligible),eligible_funds=3,excluded_windows=len(rows)-len(eligible),
                max_abs_difference_bp=max(abs(x['difference_bp']) for x in eligible),
                scope='Aggregated issuer total-return checkpoints, NOT complete raw-price or corporate-action validation',
                equivalence='Market-close versus midpoint, reinvestment and rounding conventions can differ; no statistical pass threshold selected')

def macro_checks() -> dict:
    frozen=pd.read_csv(ROOT/'raw/macro_current_vintage.csv').set_index('month')
    levels=[]
    for x in read_csv(DATA/'original_macro_level_samples.csv'):
        old=float(x['value']);new=float(frozen.loc[x['observation_month'],x['series']])
        levels.append({**x,'frozen_later_value':new,'level_difference':new-old})
    write_csv(OUT/'macro_level_revisions.csv',levels)
    rates=[]
    for x in read_csv(DATA/'original_macro_growth_samples.csv'):
        m=x['observation_month']; a=float(frozen.loc[m,x['series']]);b=float(frozen.loc[month_shift(m,-1),x['series']])
        new=100*(a/b-1);old=float(x['published_value'])
        rates.append({**x,'frozen_later_growth_percent':new,'difference_pp':new-old,
                      'outside_original_rounding_interval':abs(new-old)>float(x['rounding_halfwidth_pp'])+1e-12})
    write_csv(OUT/'macro_growth_revisions.csv',rates)
    # Both levels are taken from the SAME 2008-10-16 release snapshot.
    bymonth={x['observation_month']:float(x['value']) for x in levels}
    old=100*(bymonth['2008-09']/bymonth['2008-08']-1)
    new=100*(float(frozen.loc['2008-09','CPIAUCSL'])/float(frozen.loc['2008-08','CPIAUCSL'])-1)
    return dict(level_checks=len(levels),growth_checks=len(rates),release_snapshots=4,
                growth_discrepancies_beyond_published_rounding=sum(x['outside_original_rounding_interval'] for x in rates),
                cpi_2008_09_original_mom_percent=old,cpi_2008_09_later_mom_percent=new,
                scope='Dated source snapshots and revision checks; full month-by-month as-of panel not acquired')

def select_snapshot(rows: list[dict],series: str,asof: str) -> dict[str,dict]:
    """Select one release snapshot, never a patchwork of later revised levels."""
    cutoff=datetime.fromisoformat(asof)
    if cutoff.tzinfo is None: raise ValueError('As-of time must be timezone aware')
    groups={}
    for r in rows:
        if r['series']!=series: continue
        released=datetime.fromisoformat(r['available_at'])
        if released.tzinfo is None: raise ValueError('Release time must be timezone aware')
        if released>cutoff: continue
        groups.setdefault((released,r['vintage_id']),[]).append(r)
    if not groups: raise ValueError('No available snapshot')
    chosen=groups[max(groups)]
    out={}
    for r in chosen:
        month=r['observation_month']
        if month>cutoff.strftime('%Y-%m'): raise ValueError('Future observation')
        if month in out: raise ValueError('Duplicate observation in vintage')
        out[month]=r
    if len({r['units'] for r in chosen})!=1: raise ValueError('Mixed adjustment/index basis')
    return out

def snapshot_growth(snapshot: dict[str,dict],month: str,lag: int) -> float:
    earlier=month_shift(month,-lag)
    if month not in snapshot or earlier not in snapshot: raise ValueError('Missing exact lag; interpolation prohibited')
    a=float(snapshot[month]['value']);b=float(snapshot[earlier]['value'])
    if a<=0 or b<=0: raise ValueError('Non-positive index')
    return a/b-1

def session_calendar() -> dict:
    return xc.get_calendar('XNYS',start='1999-01-01',end='2026-11-10')

def execution_clock() -> dict:
    cal=session_calendar(); schedule=cal.schedule
    months=pd.read_csv(ROOT/'raw/monthly_returns.csv')['month']
    months=months[(months>='2000-01')&(months<='2026-09')]
    rows=[]
    for month in months:
        period=pd.Period(month,freq='M');previous=period-1
        before=schedule.loc[str(previous.start_time.date()):str(previous.end_time.date())]
        after=schedule.loc[str(period.start_time.date()):str(period.end_time.date())]
        signal=before.iloc[-1]['close'];opening=after.iloc[0]['open']
        assert signal<opening
        rows.append(dict(return_month=month,signal_session=str(before.index[-1].date()),
                         signal_close_utc=signal.isoformat(),first_execution_session=str(after.index[0].date()),
                         first_execution_open_utc=opening.isoformat(),delay_hours=(opening-signal).total_seconds()/3600))
    write_csv(OUT/'monthly_execution_clock.csv',rows)
    counts=dict(months=len(rows),min_delay_hours=min(x['delay_hours'] for x in rows),max_delay_hours=max(x['delay_hours'] for x in rows),
                calendar='XNYS',calendar_package_version=xc.__version__,status='SCHEDULE_MAPPING_ONLY',
                scope='Calendar-derived first regular-session opening after prior month-end close; not a fill record')
    return counts

def next_open_step(old_holdings: np.ndarray,overnight_gross: np.ndarray,intraday_gross: np.ndarray,
                   target: np.ndarray,cost_rates: np.ndarray) -> dict:
    """Accounting bridge for independently validated total-return factors.

    Old holdings earn the close-to-open move. Target weights start at the open.
    All factors must have the same action-adjusted basis. For a cash reserve
    replace its gross factors with actual accrued interest, not stock returns.
    This routine does NOT infer distributions, split factors, executable prices,
    settlement availability or next-month decisions from sparse quotes.
    """
    h,ov,iday,w,c=[np.asarray(z,dtype=float) for z in (old_holdings,overnight_gross,intraday_gross,target,cost_rates)]
    if len({z.shape for z in (h,ov,iday,w,c)})!=1 or h.ndim!=1: raise ValueError('Incompatible shapes')
    if not all(np.isfinite(z).all() for z in (h,ov,iday,w,c)): raise ValueError('Nonfinite values')
    if (h<0).any() or (ov<=0).any() or (iday<=0).any() or (w<0).any() or (c<0).any() or (c>=.1).any(): raise ValueError('Invalid factors/weights/costs')
    if not np.isclose(w.sum(),1,atol=1e-12,rtol=0): raise ValueError('Weights must sum to one including reserve')
    pre=h*ov;v=float(pre.sum());lo,hi=0.0,v
    for _ in range(100):
        mid=(lo+hi)/2;f=mid+float((c*np.abs(mid*w-pre)).sum())-v
        if f>0:hi=mid
        else:lo=mid
    after=(lo+hi)/2;new=after*w;fee=float((c*np.abs(new-pre)).sum())
    if abs(v-after-fee)>max(v,1)*1e-10:raise AssertionError('Self financing residual')
    final=new*iday
    return dict(pretrade_wealth=v,posttrade_wealth=after,fees=fee,end_wealth=float(final.sum()),end_holdings=final.tolist())

def quote_spots() -> dict:
    rows=[]
    for x in read_csv(DATA/'daily_quote_spot_samples.csv'):
        a,b,c=map(float,(x['previous_close'],x['next_open'],x['next_close']))
        rows.append({**x,'close_to_next_open_percent':100*(b/a-1),'next_open_to_close_percent':100*(c/b-1),
                     'use':'Provisional price-geometry example, not a strategy-return estimate'})
    write_csv(OUT/'next_open_quote_spots.csv',rows)
    return dict(spot_pairs=len(rows),status='PROVISIONAL_SECONDARY_SEARCH_TABLE',full_strategy_replay=False)

def readiness() -> dict:
    expected=['independent_daily_prices.csv','corporate_actions_and_distributions.csv','macro_asof_panel.csv','data_rights_manifest.json']
    absent=[x for x in expected if not (ROOT/'checks/external'/x).exists()]
    # Supplying filenames alone never grants approval: cross-source and semantic
    # validations must be completed and independently reviewed.
    return dict(live_or_public_data_clearance=False,full_daily_backtest_performed=False,
                missing_external_inputs=absent,status='NOT_CLEARED',
                required_review='Complete source-level coverage, corporate actions, original instrument clocks, as-of releases and documented rights')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'issuer_checkpoints':issuer_checks(),'macro_revisions':macro_checks(),'execution_calendar':execution_clock(),
            'daily_quote_spots':quote_spots(),'readiness':readiness()}
    (OUT/'external_check_summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
