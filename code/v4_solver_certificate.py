"""Independent numerical upper bounds for the M allocation problems.

The M objective is linear in an L1-cost epigraph. Supporting hyperplanes
of its convex quadratic risk set yield LP outer approximations. HiGHS
therefore supplies an upper bound on the attainable objective; a feasible
incumbent supplies a lower bound. These are numerical, not exact-arithmetic
certificates and certify estimated one-period problems, not future returns.
"""
from __future__ import annotations
from pathlib import Path
import csv, json
import numpy as np
from scipy.optimize import linprog
import engine as E
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'audit'; OUT.mkdir(exist_ok=True)

def upper_bound(mu,cov,pre,w,tolerance=2e-8,max_cuts=160):
    A=np.zeros((28,9)); b=np.zeros(28)
    A[0,:4]=1;b[0]=1
    A[1,:2]=1;b[1]=.95
    A[2:7,:4]=E.MAP;A[2:7,4:]=-np.eye(5);b[2:7]=pre-E.const
    A[7:12,:4]=-E.MAP;A[7:12,4:]=-np.eye(5);b[7:12]=E.const-pre
    A[12:,:4]=E.relative
    obj=np.r_[-mu,np.full(5,.001)]
    bounds=list(zip(np.zeros(9),[.85,.6,.6,.35,1.01,1.01,1.01,1.01,1.01]))
    wr=w[:4].copy()
    risk=float(12*wr@cov@wr)
    if risk>.15**2:wr*=.15/np.sqrt(risk)
    primal=np.r_[wr,np.abs(E.MAP@wr+E.const-pre)]
    low=float(-obj@primal)
    primal_violation=max(float(np.max(A@primal-b)),float(12*wr@cov@wr-.15**2),0.)
    cuts=[]; rhs=[]
    def cut(x):
        row=np.r_[24*cov@x,np.zeros(5)]
        cuts.append(row);rhs.append(.15**2+float(12*x@cov@x))
    cut(wr)
    for j in range(4):
        x=np.zeros(4);x[j]=.15/np.sqrt(12*cov[j,j]);cut(x)
    high=np.nan;status='iteration_limit';n=0
    for n in range(max_cuts):
        fit=linprog(obj,A_ub=np.vstack([A,np.array(cuts)]),b_ub=np.r_[b,rhs],bounds=bounds,method='highs',options={'dual_feasibility_tolerance':1e-9,'primal_feasibility_tolerance':1e-9})
        if not fit.success:
            status='lp_failure:'+fit.message;break
        high=float(-fit.fun)
        gap=high-low
        if gap<=tolerance and gap>=-1e-8:
            status='bounded';break
        cut(fit.x[:4])
    return {'lower_objective':low,'upper_objective':high,'gap_monthly_objective':float(high-low),'gap_basis_points':float((high-low)*1e4),'primal_constraint_violation':primal_violation,'lp_iterations':n+1,'status':status}

def main():
    data=E.simulate('BoydSimple')
    pre=np.r_[np.zeros(4),1.]
    results=[]
    for log in data['log']:
        i=int(log['return_index'])
        e=E.EST.get(i,'simple',36)
        # Audit the candidate generated even when the no-trade band retained holdings.
        w,info=E.optimize_weights(e.mu,e.cov,e.se,pre,cap=.95,vol=.15,penalty=0,cost=.001)
        r=upper_bound(e.mu,e.cov,pre,w)
        r.update(month=log['return_month'],original_solver_success=info['solver_success'],no_trade_band=not log['traded'])
        results.append(r)
        post=np.array([log[x]for x in E.ASSETS]);pre=post*(1+E.R[i])/(1+post@E.R[i])
    E.write(OUT/'v4_solver_bounds.csv',results)
    summary={'method':'M / BoydSimple','problems':len(results),'bounded':sum(r['status']=='bounded'for r in results),'objective_tolerance':2e-8,'max_gap_basis_points':max(r['gap_basis_points']for r in results),'max_primal_constraint_violation':max(r['primal_constraint_violation']for r in results),'max_lp_iterations':max(r['lp_iterations']for r in results),'independent_algorithm':'SciPy HiGHS LP outer approximation vs SLSQP primal','interpretation':'Numerical bounds on fitted one-period problems only. No exact arithmetic, economic forecast or out-of-sample certification.'}
    (OUT/'v4_solver_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
