"""Independent peak/trough/recovery episode ledger, preserving calendar gaps."""
import json
import numpy as np
import engine as e
from macro_vintages import load_panel

def episodes(dates,wealth):
    peak=0;trough=0;active=False;out=[]
    for j in range(1,len(wealth)):
        if wealth[j]>=wealth[peak]*(1-1e-10):
            if active:
                out.append(dict(peak=e.label(int(dates[peak])),trough=e.label(int(dates[trough])),recovery_or_last=e.label(int(dates[j])),duration_months=int(dates[j]-dates[peak]),trough_to_recovery_months=int(dates[j]-dates[trough]),depth=1-wealth[trough]/wealth[peak],right_censored=False))
            peak=j;trough=j;active=False
        else:
            active=True
            if wealth[j]<wealth[trough]:trough=j
    if active:
        out.append(dict(peak=e.label(int(dates[peak])),trough=e.label(int(dates[trough])),recovery_or_last=e.label(int(dates[-1])),duration_months=int(dates[-1]-dates[peak]),trough_to_recovery_months=None,depth=1-wealth[trough]/wealth[peak],right_censored=True))
    return out

def run():
    logs=e.read(e.OUT/'monthly_paths_weights.csv');pan=load_panel('pcpi');cpi=pan[max(pan)];allrows=[];summary=[]
    for name in ['QQQ','SPY','RegimeRule','BoydSimple','Vol15']:
        rs=[r for r in logs if r['strategy']==name];dates=np.r_[e.mn('1999-12'),[e.mn(r['return_month'])for r in rs]];values=np.r_[100000.,[float(r['nav'])for r in rs]]
        for kind in ['nominal','real']:
            if kind=='real':
                keep=[i for i,d in enumerate(dates)if d<=e.mn('2025-12')and d in cpi];dd=dates[keep];vv=np.array([values[i]*cpi[e.mn('1999-12')]/cpi[dates[i]]for i in keep])
            else:dd=dates;vv=values
            ep=episodes(dd,vv);allrows += [dict(strategy=name,basis=kind,**x)for x in ep]
            m=max(x['duration_months']for x in ep);long=[x for x in ep if x['duration_months']==m];summary.append(dict(strategy=name,basis=kind,longest_duration_months=m,all_longest_episodes_recovered=all(not x['right_censored']for x in long),longest_episodes=long))
    e.write(e.OUT/'recovery_episodes.csv',allrows)
    (e.ROOT/'audit/recovery_audit.json').write_text(json.dumps(summary,indent=2))
    assert all(x['all_longest_episodes_recovered']for x in summary)
    print([(x['strategy'],x['basis'],x['longest_duration_months'])for x in summary])
if __name__=='__main__':run()
