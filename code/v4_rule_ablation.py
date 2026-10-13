"""Sequential R-component attribution; diagnostics, not new strategy selection.

Hold the asset panel, monthly clock, accounting and 2pp band fixed. Add risk
scaling, state-dependent templates/budgets, then independent bond/gold gates.
The order is explicit and includes interactions; it is not a Shapley or causal
estimate of an economically invariant component contribution.
"""
from pathlib import Path
import csv,json
import numpy as np
import engine as E
ROOT=Path(__file__).resolve().parents[1]
NAMES=['Template','Scale only','States + scale','Full R']

def simulate(case,start='2000-01',end='2026-09'):
    take=np.where((E.D>=E.mn(start))&(E.D<=E.mn(end)))[0]
    hold=np.r_[np.zeros(4),100000.]; path=[100000.];rs=[];orders=[];turn=[];fees=[];W=[];logs=[];laststate=None
    for k,i in enumerate(take):
        state,score,eligible,_=E.signals(i)
        if case in ('Template','Scale only'):state=2
        budget=1.0 if case=='Template' else (.15 if case=='Scale only' else [0.08,.12,.15][state])
        cap=1.0 if case=='Template' else [.25,.65,.95][state]
        w=np.array([[.10,0,.35,.25,.30],[.30,.15,.20,.15,.20],[.65,.20,.10,.05,0.]][state])
        cov=E.EST.get(i,'ridge',36).cov
        if case=='Full R':
            for j in (2,3):
                if not eligible[j]:w[4]+=w[j];w[j]=0
        if case!='Template':
            risk=np.sqrt(12*w[:4]@cov@w[:4]);a=min(1,budget/max(risk,1e-8));w[:4]*=a;w[4]=1-w[:4].sum()
        val=float(hold.sum());pre=hold/val
        safe=np.sqrt(12*pre[:4]@cov@pre[:4])<=budget*1.001 and pre[:2].sum()<=cap+1e-7
        traded=k==0 or not(laststate==state and safe and np.max(np.abs(w-pre))<.02)
        if traded:
            lo,hi=0.,val
            for _ in range(70):
                nv=(lo+hi)/2;tv=nv if k==0 else np.abs(nv*w-hold).sum()
                if nv+.001*tv>val:hi=nv
                else:lo=nv
            nv=(lo+hi)/2;tr=nv*w if k==0 else np.abs(nv*w-hold);fee=val-nv;hold=nv*w
            count=int((tr/val>1e-6).sum());turn.append(float(tr.sum()/val))
        else:fee=0.;count=0;turn.append(0.)
        post=hold/hold.sum();hold*=1+E.R[i];after=float(hold.sum());rs.append(after/val-1);path.append(after);W.append(post)
        orders.append(count);fees.append(fee);logs.append({'solver_success':True});laststate=state
    return {'name':case,'dates':E.D[take],'r':np.array(rs),'path':np.array(path),'W':np.array(W),'log':logs,'two_way':np.array(turn),'orders':np.array(orders),'fees':np.array(fees),'terminal_after_liquidation_fx':path[-1],'start_capital':100000.}

def main():
    results=[];checks=[]
    for start,end in [('2000-01','2026-09'),('2016-01','2025-12')]:
        benchmark=E.simulate('QQQ',start=start,end=end)
        for case in NAMES:
            s=simulate(case,start,end);m=E.metrics(s,benchmark);m['diagnostic']='Sequential; no retuning';results.append(m)
            if case=='Full R':
                ref=E.simulate('RegimeRule',start=start,end=end)
                error=float(np.max(np.abs(s['path']/ref['path']-1)))
                assert error<1e-9,error
                checks.append({'start':start,'end':end,'independent_full_R_max_relative_path_error':error})
    E.write(ROOT/'outputs/v4_rule_ablation.csv',results)
    (ROOT/'audit/v4_ablation_verification.json').write_text(json.dumps({'checks':checks,'policy_selected':False,'scope':'Sequential additions; effects depend on order and interactions.'},indent=2))
    table=['\\begin{tabular}{@{}lrrrrrr@{}}\\toprule',' & \\multicolumn{3}{c}{2000--2026} & \\multicolumn{3}{c}{2016--2025}\\\\','Component sequence & CAGR & MDD & Water & CAGR & MDD & Water\\\\\\midrule']
    for case in NAMES:
        a,b=[x for x in results if x['strategy']==case]
        table.append(case+' & '+' & '.join([f"{100*a['cagr']:.2f}",f"{100*a['max_dd']:.2f}",str(a['longest_water_months']),f"{100*b['cagr']:.2f}",f"{100*b['max_dd']:.2f}",str(b['longest_water_months'])])+r'\\')
    table.extend(['\\bottomrule','\\end{tabular}'])
    (ROOT/'manuscript/tables/v4_ablation.tex').write_text('\n'.join(table)+'\n')
    for r in results:print(r['strategy'],r['start'],*[round(100*r[k],2)for k in ['cagr','max_dd']],r['longest_water_months'])
if __name__=='__main__':main()
