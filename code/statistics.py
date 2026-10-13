"""Paired block bootstrap of realized strategy returns, including centered-null tests.
This conditions on fitted policies and does NOT repeat the historical search.
"""
import json
import numpy as np
import engine as e

def run():
 rng=np.random.default_rng(260912);rows=[];B=20000;family=12
 for a,b in [('2000-01','2026-09'),('2016-01','2025-12')]:
  q=e.simulate('QQQ',a,b);lq=np.log1p(q['r']);n=len(lq);starts=rng.integers(0,n,size=(B,int(np.ceil(n/12))));ix=((starts[:,:,None]+np.arange(12))%n).reshape(B,-1)[:,:n]
  for name in ['Vol15','RegimeRule','BoydSimple','BoydRidge','RegimeRobust','ProbabilityRobust']:
   s=e.simulate(name,a,b);delta=np.log1p(s['r'])-lq;obs=12*delta.mean();boot=12*delta[ix].mean(1);null=boot-obs
   p=(np.sum(null>=obs)+1)/(B+1)
   lo,hi=np.quantile(boot,[.025,.975]);blo,bhi=np.quantile(boot,[.025/family,1-.025/family])
   rows.append({'strategy':name,'start':a,'end':b,'annual_log_growth_difference':obs,'paired_CI95_low':lo,'paired_CI95_high':hi,'familywise_CI95_low':blo,'familywise_CI95_high':bhi,'centered_one_sided_p':p,'bonferroni_p':min(1,p*family),'n_boot':B,'block_months':12,'interpretation':'conditional on realized fitted strategy returns; not end-to-end; not unknown lifetime research selection corrected'})
 e.write(e.OUT/'bootstrap_conditional.csv',rows)
 print('Paired tests',len(rows),'Bonferroni discoveries',sum(r['bonferroni_p']<.05 and r['annual_log_growth_difference']>0 for r in rows))

if __name__=='__main__':run()
