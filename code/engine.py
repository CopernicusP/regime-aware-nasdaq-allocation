"""Regime-aware robust allocation, monthly research extension v2.
Not a replication of daily Boyd et al.; no trading or network calls.
Requires numpy, scipy; Python>=3.10.  python code/engine.py
"""
from __future__ import annotations
from pathlib import Path
import csv,json,math,hashlib,itertools
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize, LinearConstraint, Bounds
from scipy.special import expit
from scipy.stats import rankdata
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
ASSETS=['QQQ','US','BOND','GOLD','CASH']; BASE=np.array([.5,.2,.2,.1,0.]); PRIOR=np.array([.06,.045,.01,.005])/12

def read(p):
 with open(p,encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows):
 if not rows:return
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with open(p,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)
def mn(s):y,m=map(int,s.split('-'));return y*12+m-1
def label(m):return f'{m//12:04d}-{m%12+1:02d}'
DATA=read(ROOT/'raw/monthly_returns.csv');D=np.array([mn(x['month'])for x in DATA]);R=np.array([[float(x[a])for a in ASSETS]for x in DATA]);P=np.vstack([np.ones(5),np.cumprod(1+R,axis=0)])
SPY=np.array([float(x['SPY'])if x['SPY'] else np.nan for x in DATA])
MAC={mn(x['month']):np.array([float(x[a])if x[a]else np.nan for a in ['CPIAUCSL','IPMAN']])for x in read(ROOT/'raw/macro_current_vintage.csv')}

def weighted_cov(x,half=6):
 n=len(x);a=np.exp(-np.log(2)*np.arange(n-1,-1,-1)/half);a/=a.sum();mu=a@x;cov=(x-mu).T@(a[:,None]*(x-mu))/max(1-(a*a).sum(),.1);return .75*cov+.25*np.diag(np.diag(cov))+np.eye(x.shape[1])*1e-8

def signals(i,ma=10):
 # P[i] observed at prior month-end; R[i] is next unknown monthly return.
 def mean(k):return P[max(0,k-ma+1):k+1].mean(0)
 avg=mean(i);old=mean(max(0,i-3));lag=min(6,i);mom=P[i]/P[i-lag]-1
 trend=P[i]>avg;score=int(sum(int(trend[j])+int(mom[j]>mom[4])+int(avg[j]>old[j])for j in [0,1]))
 state=2 if score>=5 else 0 if score<=1 else 1
 eligible=trend & (mom>mom[4]);eligible[4]=True
 return state,score,eligible,avg

def features(i,macro=False):
 v=[]
 for j in range(4):
  h=R[max(0,i-12):i,j];s=R[max(0,i-3):i,j];vol=np.std(h,ddof=1)if len(h)>1 else .02
  v.extend([P[i,j]/P[max(0,i-6),j]-1,P[i,j]/P[max(0,i-12),j]-1,P[i,j]/P[max(0,i-9):i+1,j].mean()-1,np.log(max(np.std(s,ddof=1)if len(s)>1 else vol,1e-4)/max(vol,1e-4))])
 v.extend([P[i,0]/np.max(P[max(0,i-12):i+1,0])-1,R[max(0,i-1),4]*12])
 if macro:
  ref=(D[i] if i<len(D) else D[-1]+1)-3 # signal-month minus2
  # Carry historical known value ONLY backward, no future interpolation.
  vals=[]
  for delta in [0,6,12,18]:
   k=ref-delta
   while (k not in MAC or not np.all(np.isfinite(MAC[k])))and k>=min(MAC):k-=1
   vals.append(MAC.get(k,np.array([np.nan,np.nan])))
  a,b,c,d=vals
  v.extend([a[0]/c[0]-1,(a[0]/c[0]-1)-(b[0]/d[0]-1),a[1]/c[1]-1])
 return np.array(v)

@dataclass
class Estimates:
 cov:np.ndarray
 mu:np.ndarray
 se:np.ndarray
 fitted:bool
 p:float
 basep:float
 known_label_last:int

class Estimator:
 def __init__(self,macro=False):
  self.X=np.array([features(i,macro)for i in range(9,len(D)+1)])
  self.idx=np.arange(9,len(D)+1);self.macro=macro
  self.cache={}
 def get(self,i,kind='ridge',covwindow=36):
  key=(i,kind,covwindow)
  if key in self.cache:return self.cache[key]
  hist=R[max(0,i-covwindow):i,:4]-R[max(0,i-covwindow):i,4,None]
  cov=weighted_cov(hist)
  if RISK_FLOOR_ANNUAL is not None:
   floor=np.asarray(RISK_FLOOR_ANNUAL)**2/12;cov+=np.diag(np.maximum(floor-np.diag(cov),0))
  a=np.exp(-np.log(2)*np.arange(len(hist)-1,-1,-1)/12);a/=a.sum()
  ew=a@hist;pred=.5*ew+.5*PRIOR;se=np.sqrt(np.diag(cov)/max(len(hist)/3,3));fitted=False;p=np.nan;basep=np.nan
  ids=self.idx[(self.idx+3<=i)&(self.idx>=i-123)]
  last=int(ids[-1]+3) if len(ids)else-1
  if len(ids)>=60:
   XX=self.X[ids-9];valid=np.isfinite(XX).all(1);ids=ids[valid];XX=XX[valid]
   YY=np.array([(np.prod(1+R[j:j+3,:4],axis=0)-np.prod(1+R[j:j+3,4]))/3 for j in ids])
   if len(ids)>=60:
    rho=np.exp(-np.log(2)*np.arange(len(ids)-1,-1,-1)/60);rho/=rho.sum();xm=rho@XX;xs=np.sqrt(rho@((XX-xm)**2));xs=np.maximum(xs,1e-4)
    Z=(XX-xm)/xs;z=(self.X[i-9]-xm)/xs;ym=rho@YY
    B=np.linalg.solve(Z.T@(rho[:,None]*Z)+10*np.eye(Z.shape[1]),Z.T@(rho[:,None]*(YY-ym)))
    pr=ym+z@B;res=YY-(ym+Z@B);se=np.sqrt(rho@(res**2))/np.sqrt(max(1/(rho@rho)/3,3));se=np.maximum(se,.00025)
    if kind=='ridge':pred=.5*pr+.5*PRIOR
    y=np.array([float(np.prod(1+R[j:j+3,0])-1<=-.10)for j in ids]);basep=(y.sum()+1)/(len(y)+2)
    # Four chosen state features; causal logistic, unpenalized intercept.
    cols=[2,0,3,16];zz=np.c_[np.ones(len(Z)),Z[:,cols]];zznow=np.r_[1,z[cols]]
    def obj(b):
     xb=zz@b;loss=np.mean(np.logaddexp(0,xb)-y*xb)+.5*np.sum(b[1:]**2)
     grad=zz.T@(expit(xb)-y)/len(y)+np.r_[0,b[1:]];return loss,grad
    b0=np.r_[np.log(basep/(1-basep)),np.zeros(4)]
    fit=minimize(obj,b0,jac=True,method='BFGS',options={'gtol':1e-8,'maxiter':60});p=float(expit(zznow@fit.x));fitted=True
  est=Estimates(cov,np.clip(pred,-.025,.025),se,fitted,p,basep,last);self.cache[key]=est;return est
EST=Estimator();ESTM=Estimator(True)

# Convex epigraph formulation: w4 and u5>=abs(full_w-pre_w).
MAP=np.vstack([np.eye(4),-np.ones(4)]);const=np.r_[np.zeros(4),1.]
RISK_FLOOR_ANNUAL=None
SIGNS=np.array(list(itertools.product([-1.,1.],repeat=4)));relative=SIGNS@(np.eye(4)-BASE[:4,None]@np.ones((1,4)))-np.ones((16,4))
SOLVER_LOG=[]
def optimize_weights(mu,cov,se,pre,cap=.95,vol=.15,penalty=.25,cost=.001):
 M=np.zeros((28,9));lb=np.full(28,-np.inf);ub=np.zeros(28)
 M[0,:4]=1;ub[0]=1;M[1,:2]=1;ub[1]=cap
 M[2:7,:4]=MAP;M[2:7,4:]=-np.eye(5);ub[2:7]=pre-const
 M[7:12,:4]=-MAP;M[7:12,4:]=-np.eye(5);ub[7:12]=const-pre
 M[12:,:4]=relative
 def obj(x):
  w=x[:4];sd=np.sqrt(np.dot(se*w,se*w)+1e-16)
  f=(-mu@w+penalty*sd+cost*x[4:].sum())*100
  grad=np.r_[-mu+penalty*(se*se*w)/sd,np.ones(5)*cost]*100
  return f,grad
 def risk(x):return vol**2-12*x[:4]@cov@x[:4]
 def jac(x):return np.r_[-24*cov@x[:4],np.zeros(5)]
 w0=np.array([.01,.01,.01,.01]);x0=np.r_[w0,np.abs(MAP@w0+const-pre)+.001]
 fit=minimize(obj,x0,jac=True,method='SLSQP',bounds=Bounds(np.zeros(9),np.r_[.85,.60,.60,.35,np.ones(5)*1.01]),constraints=[LinearConstraint(M,lb,ub),{'type':'ineq','fun':risk,'jac':jac}],options={'maxiter':160,'ftol':1e-10})
 feas=min(float(risk(fit.x)),float(np.min(ub-M@fit.x)),float(np.min(fit.x)))
 okay=fit.success and feas>=-1e-6
 w=np.clip(fit.x[:4],0,1)if okay else np.zeros(4); w=np.r_[w,max(0,1-w.sum())];w/=w.sum()
 return w,{'solver_success':bool(okay),'solver_message':str(fit.message),'min_constraint_slack':feas,'objective':float(fit.fun/100),'iterations':int(fit.nit)}

METHODS=['QQQ','SPY','Static_70_20_10','Static_50_20_20_10','Vol15','RegimeRule','BoydSimple','BoydRidge','RegimeRobust','ProbabilityRobust','MacroRidge_Exploratory']

def target(name,i,pre,vol=.15,penalty=.25,ma=10,cost=.001,no_regime=False,no_uncertainty=False,covwindow=36):
 st,score,eligible,_=signals(i,ma);e=(ESTM if name=='MacroRidge_Exploratory' else EST).get(i,'simple'if name=='BoydSimple'else'ridge',covwindow)
 d={'signal_month':label(int((D[i] if i<len(D) else D[-1]+1)-1)),'state':st,'score':score,'p3m_loss10':e.p,'base_rate':e.basep,'fitted':e.fitted,'train_label_end_index':e.known_label_last,'signal_index':i}
 if name in ('QQQ','SPY'):w=np.array([1,0,0,0,0.]);budget=1.;cap=1.
 elif name=='Static_70_20_10':w=np.array([.7,0,.2,.1,0.]);budget=1.;cap=1.
 elif name=='Static_50_20_20_10':w=BASE.copy();budget=1.;cap=1.
 elif name=='Vol15':
  sigma=np.std(R[max(0,i-12):i,0],ddof=1)*np.sqrt(12);q=min(1,vol/max(sigma,.001));w=np.array([q,0,0,0,1-q]);budget=vol;cap=1.
 elif name=='RegimeRule':
  w=np.array([[.10,0,.35,.25,.30],[.30,.15,.20,.15,.20],[.65,.20,.10,.05,0.]][st]);budget=vol*np.array([8/15,12/15,1])[st];cap=[.25,.65,.95][st]
  for a in [2,3]:
   if not eligible[a]:w[4]+=w[a];w[a]=0
  s=np.sqrt(12*w[:4]@e.cov@w[:4]);f=min(1,budget/max(s,1e-8));w[:4]*=f;w[4]=1-w[:4].sum()
 else:
  budget=vol;cap=.95
  if name=='RegimeRobust'and not no_regime:budget*=np.array([8/15,12/15,1])[st];cap=[.25,.65,.95][st]
  if name=='ProbabilityRobust'and np.isfinite(e.p):budget*=1-.5*e.p;cap=.95-.7*e.p
  k=0 if name in ('BoydSimple','BoydRidge','MacroRidge_Exploratory')or no_uncertainty else penalty
  w,info=optimize_weights(e.mu,e.cov,e.se,pre,cap,budget,k,cost);d.update(info)
 d.update(vol_budget=budget,equity_cap=cap,cov_qqq_ann=np.sqrt(e.cov[0,0]*12),mu_qqq_month=e.mu[0])
 return w,d,e

def simulate(name,start='2000-01',end='2026-09',cost=.001,flat=0,capital=100000,fx=.0,delay=0,band=.02,vol=.15,penalty=.25,ma=10,cash_zero=False,no_regime=False,no_uncertainty=False,covwindow=36,override=None):
 take=np.where((D>=mn(start))&(D<=mn(end)))[0];pre=np.array([0,0,0,0,1.]);W=[];nav=capital*(1-fx);path=[nav];ret=[];logs=[];trade=[];norders=[];fees=[];laststate=None
 for n,i in enumerate(take):
  j=max(9,i-delay);w,info,e=target(name,j,pre,vol,penalty,ma,cost,no_regime,no_uncertainty,covwindow)
  if override is not None:w=np.asarray(override).copy()
  static=name.startswith('Static')or override is not None
  reb=n==0 or (name not in ('QQQ','SPY')and (not static or (D[i]%12+1)in(1,4,7,10)))
  safety=(np.sqrt(12*pre[:4]@e.cov@pre[:4])<=info['vol_budget']*1.001 and pre[:2].sum()<=info['equity_cap']+1e-7)
  if reb and n>0 and name not in ('QQQ','SPY')and not static and laststate==info['state']and safety and np.max(np.abs(w-pre))<band:reb=False
  if reb:
   f=1.
   for _ in range(20):
    tr=np.abs(f*w-pre) if n>0 else f*w
    orders=int((tr>1e-6).sum());f=1-cost*tr.sum()-flat*orders/nav
   tr=np.abs(f*w-pre)if n>0 else f*w;orders=int((tr>1e-6).sum());fee=nav*(1-f);nav*=f;post=w.copy()
  else:f=1.;tr=np.zeros(5);orders=0;fee=0;post=pre.copy()
  r=R[i].copy()
  if name=='SPY':r[0]=SPY[i]
  if cash_zero:r[4]=0
  gross=1+post@r;nav*=gross;pre=post*(1+r)/gross
  W.append(post);path.append(nav);ret.append(f*gross-1);trade.append(tr.sum());norders.append(orders);fees.append(fee)
  info.update(return_month=label(int(D[i])),return_index=int(i),turnover_two_way=float(tr.sum()),order_count=orders,traded=bool(reb),cost_cash=fee,net_return=f*gross-1,nav=nav,**{a:float(post[k])for k,a in enumerate(ASSETS)})
  logs.append(info);laststate=info['state']
 # End liquidation cost is disclosed separately; base NAV remains an invested portfolio.
 terminal_net=nav*(1-cost)-flat*int((pre>1e-6).sum());terminal_net*=1-fx
 return {'name':name,'dates':D[take],'r':np.array(ret),'path':np.array(path),'W':np.array(W),'log':logs,'two_way':np.array(trade),'orders':np.array(norders),'fees':np.array(fees),'terminal_after_liquidation_fx':terminal_net,'start_capital':capital,'fx_initial':fx}

def metrics(s,bench=None):
 rr=s['r'];n=len(rr);nav=s['path']/s['start_capital'];dd=1-nav/np.maximum.accumulate(nav);neg=rr<0;rf=np.array([R[np.searchsorted(D,d),4]for d in s['dates']]);ex=rr-rf
 # Duration includes the recovery endpoint; unrecovered episodes are right-censored.
 m=0;lastpeak=0;endoflong=0;long_censored=False;in_dd=False
 for j in range(1,len(nav)):
  if dd[j]<=1e-10:
   if in_dd and j-lastpeak>m:m=j-lastpeak;endoflong=j;long_censored=False
   lastpeak=j;in_dd=False
  else:
   in_dd=True
   if j-lastpeak>m:m=j-lastpeak;endoflong=j;long_censored=True
 if endoflong<len(nav)-1:long_censored=False
 cagr=(nav[-1])**(12/n)-1;vol=np.std(rr,ddof=1)*np.sqrt(12);sh=np.mean(ex)/max(np.std(ex,ddof=1),1e-12)*np.sqrt(12)
 # Observed 95% CVaR, monthly; a distributional statistic, not a limit.
 tail=np.sort(rr)[:max(1,math.ceil(.05*n))];gap=0
 if bench is not None:
  b=bench['path']/bench['path'][0];peak=0
  for j in range(1,len(b)):
   if b[j]>=b[peak]-1e-12:peak=j
   else:gap=max(gap,(b[j]/b[peak]-1)-(nav[j]/nav[peak]-1))
 result={'strategy':s['name'],'start':label(int(s['dates'][0])),'end':label(int(s['dates'][-1])),'months':n,'cagr':cagr,'vol':vol,'sharpe_arithmetic_excess':sh,'max_dd':float(dd.max()),'longest_water_months':m,'water_right_censored':bool(long_censored and dd[-1]>1e-10),'ulcer':float(np.sqrt(np.mean(dd**2))),'cvar95_month':float(-tail.mean()),'calmar':float(cagr/max(dd.max(),1e-9)),'turnover_two_way_annual':float(s['two_way'].sum()*12/n),'orders_per_year':float(s['orders'].sum()*12/n),'terminal_100k':float(nav[-1]*100000),'extra_loss_qqq_pp':float(gap*100),'total_explicit_fees':float(s['fees'].sum()),'terminal_after_liquidation_fx':s['terminal_after_liquidation_fx'],'solver_failures':sum(not x.get('solver_success',True)for x in s['log'])}
 return result


def real_metrics(s,end='2025-12'):
 ix=np.where(s['dates']<=mn(end))[0];m0=int(s['dates'][0])-1;base=MAC.get(m0,[np.nan])[0];levels=[1.];ds=[m0]
 for j in ix:
  cp=MAC.get(int(s['dates'][j]),[np.nan])[0]
  if np.isfinite(cp):levels.append(s['path'][j+1]/s['path'][0]*base/cp);ds.append(int(s['dates'][j]))
 v=np.array(levels);dd=1-v/np.maximum.accumulate(v);peak=0;m=0;in_dd=False
 for j in range(1,len(v)):
  if dd[j]<=1e-10:
   if in_dd:m=max(m,ds[j]-ds[peak])
   peak=j;in_dd=False
  else:in_dd=True;m=max(m,ds[j]-ds[peak])
 return {'strategy':s['name'],'start':label(m0+1),'end':label(ds[-1]),'real_cagr':float(v[-1]**(12/(ds[-1]-m0))-1),'real_max_dd':float(dd.max()),'real_water_months':m,'missing_cpi_observation_skipped':'2025-10; no interpolation','real_terminal_100k':float(v[-1]*100000)}

def main():
 logs=[];rows=[];allres={}
 for name in METHODS:
  s=simulate(name);allres[name]=s;logs.extend([{'strategy':name,**x}for x in s['log']])
 for a,b in [('2000-01','2026-09'),('2000-01','2009-12'),('2010-01','2015-12'),('2016-01','2025-12'),('2012-01','2026-09'),('2026-01','2026-09')]:
  q=allres['QQQ']if a=='2000-01'and b=='2026-09'else simulate('QQQ',a,b)
  for name in METHODS:
   s=allres[name]if a=='2000-01'and b=='2026-09'else simulate(name,a,b);rows.append(metrics(s,q))
 write(OUT/'metrics.csv',rows);write(OUT/'monthly_paths_weights.csv',logs)
 write(OUT/'real_performance.csv',[real_metrics(allres[n])for n in METHODS])
 periods=[('Dotcom_2000_2002','2000-01','2002-12'),('Recovery_2003_2007','2003-01','2007-12'),('GFC_2008','2008-01','2008-12'),('GFC_peak_window','2007-11','2009-02'),('Bull_2009_2019','2009-01','2019-12'),('COVID_Q1','2020-01','2020-03'),('COVID_full','2020-01','2020-12'),('Tightening_2022','2022-01','2022-12'),('Bull_2023_2026','2023-01','2026-09')];pr=[]
 for n,s in allres.items():
  for tag,a,b in periods:
   rr=s['r'][(s['dates']>=mn(a))&(s['dates']<=mn(b))];pr.append({'strategy':n,'period':tag,'total_return':float(np.prod(1+rr)-1)})
 write(OUT/'crisis_periods.csv',pr)
 # Fix selection on2010-2015 only; report forward historical audit regardless of its outcome.
 cand=[r for r in rows if r['start']=='2010-01'and r['end']=='2015-12'and r['strategy']in['Vol15','RegimeRule','BoydSimple','BoydRidge','RegimeRobust','ProbabilityRobust']]
 for r in cand:r['selection_score']=math.log1p(r['cagr'])-.5*r['vol']**2;r['eligible']=r['max_dd']<=.30 and r['turnover_two_way_annual']<=6 and r['longest_water_months']<=48
 elig=[r for r in cand if r['eligible']];selected=max(elig,key=lambda r:r['selection_score'])['strategy'] if elig else'NO_ELIGIBLE_STRATEGY'
 write(OUT/'validation_selection.csv',cand);(OUT/'selection.json').write_text(json.dumps({'selection_period':'2010-2015','selected':selected,'historical_audit':'2016-2025; previously seen history, not external untouched sample','not_current_trade_instruction':True},indent=2))
 # Loss classifier evaluation, no threshold search, only fully matured future labels.
 cp=[];raw=[]
 for i in range(9,len(D)-2):
  e=EST.get(i)
  if not np.isfinite(e.p):continue
  y=int(np.prod(1+R[i:i+3,0])-1<=-.10);raw.append({'signal_month':label(int((D[i] if i<len(D) else D[-1]+1)-1)),'next3m_loss10':y,'probability':e.p,'baseline_probability':e.basep})
 for start,end in [('2010-01','2015-12'),('2016-01','2025-12')]:
  r=[x for x in raw if start<=x['signal_month']<=end];y=np.array([x['next3m_loss10']for x in r]);p=np.array([x['probability']for x in r]);b=np.array([x['baseline_probability']for x in r]);rank=rankdata(p);pos=y==1;auc=(rank[pos].sum()-pos.sum()*(pos.sum()+1)/2)/(pos.sum()*(~pos).sum())
  cp.append({'start':start,'end':end,'n':len(y),'events':int(y.sum()),'brier':float(np.mean((p-y)**2)),'baseline_brier':float(np.mean((b-y)**2)),'brier_skill':float(1-np.mean((p-y)**2)/np.mean((b-y)**2)),'auc':float(auc),'predicted_event_average':float(p.mean()),'observed_event_frequency':float(y.mean())})
 write(OUT/'classifier_eval.csv',cp);write(OUT/'classifier_predictions.csv',raw)
 # Regime score is descriptive and cannot be called a calibrated probability.
 states=[{'signal_month':label(int((D[i] if i<len(D) else D[-1]+1)-1)),'state':signals(i)[0],'score':signals(i)[1]}for i in range(9,len(D))];write(OUT/'regimes.csv',states)
 for r in rows:
  if (r['start'],r['end'])in [('2000-01','2026-09'),('2016-01','2025-12')]:print(r['start'],r['strategy'],f"CAGR {r['cagr']:.2%} DD{r['max_dd']:.2%} Sharpe{r['sharpe_arithmetic_excess']:.2f} Water{r['longest_water_months']} gap{r['extra_loss_qqq_pp']:.2f} failures{r['solver_failures']}")
 print('VALIDATION_CHOICE',selected,'CLASSIFIER',cp)
 return allres
if __name__=='__main__':main()
