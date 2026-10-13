"""Bounded exploratory pipeline bootstrap for two price-only policies.
100 paired circular blocks (12 months); indicators, covariance, forecasts and trades
are reconstructed, but full development/validation model selection is NOT repeated.
Fixed-cash data resampling also assumes a stationary mixture of historical regimes.
"""
import json, hashlib, argparse
import numpy as np
import engine as e

class FastPriceEstimator:
 def __init__(self):self.cache={}
 def get(self,i,kind='ridge',covwindow=36):
  key=(i,covwindow)
  if key not in self.cache:
   h=e.R[max(0,i-covwindow):i,:4]-e.R[max(0,i-covwindow):i,4,None];cov=e.weighted_cov(h);a=np.exp(-np.log(2)*np.arange(len(h)-1,-1,-1)/12);a/=a.sum();mu=np.clip(.5*(a@h)+.5*e.PRIOR,-.025,.025)
   self.cache[key]=e.Estimates(cov,mu,np.sqrt(np.diag(cov)/max(len(h)/3,3)),False,np.nan,np.nan,-1)
  return self.cache[key]

def run(fresh=False):
 savedR=e.R.copy();savedP=e.P.copy();original=e.EST
 expected={n:e.simulate(n)['r']for n in ['RegimeRule','BoydSimple']}
 e.EST=FastPriceEstimator();error={n:float(np.max(np.abs(e.simulate(n)['r']-expected[n])))for n in expected}
 assert max(error.values())<1e-9
 rng=np.random.default_rng(411992);rows=[]
 checkpoint=e.OUT/'bootstrap_pipeline_draws.csv'
 fingerprint_path=e.OUT/'bootstrap_pipeline_fingerprint.json'
 inputs=[e.ROOT/'protocol.json',e.ROOT/'raw/monthly_returns.csv',e.ROOT/'code/engine.py',e.ROOT/'code/end_to_end_check.py']
 fingerprint={str(x.relative_to(e.ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in inputs}
 if fresh:
  checkpoint.unlink(missing_ok=True);fingerprint_path.unlink(missing_ok=True)
 if checkpoint.exists():
  if not fingerprint_path.exists() or json.loads(fingerprint_path.read_text())!=fingerprint:
   raise RuntimeError('Checkpoint input/code fingerprint is missing or changed. Run with --fresh; never reuse results after changing data or rules.')
 fingerprint_path.write_text(json.dumps(fingerprint,indent=2))
 if checkpoint.exists():
  rows=[{k:(v if k=='strategy' else int(v) if k=='rep' else float(v))for k,v in r.items()}for r in e.read(checkpoint)]
 completed=max([r['rep']for r in rows],default=-1)+1
 for b in range(100):
  starts=rng.integers(0,len(e.R),size=int(np.ceil(len(e.R)/12)));ix=((starts[:,None]+np.arange(12))%len(e.R)).reshape(-1)[:len(e.R)]
  if b<completed:continue
  e.R[:]=savedR[ix];e.P=np.vstack([np.ones(5),np.cumprod(1+e.R,axis=0)]);e.EST=FastPriceEstimator()
  q=e.simulate('QQQ');qm=e.metrics(q,q)
  for n in expected:
   s=e.simulate(n);m=e.metrics(s,q);rows.append({'rep':b,'strategy':n,'cagr_difference':m['cagr']-qm['cagr'],'log_growth_difference':np.log1p(m['cagr'])-np.log1p(qm['cagr']),'sharpe_difference':m['sharpe_arithmetic_excess']-qm['sharpe_arithmetic_excess'],'dd_reduction':qm['max_dd']-m['max_dd'],'water_reduction_months':qm['longest_water_months']-m['longest_water_months']})
  if b%10==9:e.write(e.OUT/'bootstrap_pipeline_draws.csv',rows);print('pipeline',b+1,flush=True)
 e.R[:]=savedR;e.P=savedP;e.EST=original
 out=[]
 for n in expected:
  for metric in ['cagr_difference','log_growth_difference','sharpe_difference','dd_reduction','water_reduction_months']:
   x=np.array([r[metric]for r in rows if r['strategy']==n]);out.append({'strategy':n,'metric':metric,'median':float(np.median(x)),'low95':float(np.quantile(x,.025)),'high95':float(np.quantile(x,.975)),'fraction_nonpositive':float(np.mean(x<=0)),'replications':100,'not_a_pvalue':True})
 e.write(e.OUT/'bootstrap_pipeline_summary.csv',out)
 (e.OUT/'pipeline_bootstrap_notes.json').write_text(json.dumps({'fast_path_exact_original_maxerror':error,'full_model_selection_repeated':False,'cash_returns_resampled_jointly':True,'CPI_not_involved':True,'n_boot':100,'monthly_blocks':12,'tail_quantiles_coarse':True,'no_statistical_significance_claim':True},indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--fresh',action='store_true');args=parser.parse_args();run(fresh=args.fresh)
