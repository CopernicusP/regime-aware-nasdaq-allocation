"""Vendor-free computational demonstration. Every observation is FICTIONAL.
Runs the unchanged core in an isolated temporary directory; cannot overwrite research data.
"""
from pathlib import Path
import tempfile,subprocess,sys,shutil,json,csv,argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=Path('synthetic_demo_output'));a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 rng=np.random.default_rng(20261013);rows=[];macro=[]
 for i in range(330):
  n=1999*12+3+i;m=f'{n//12:04d}-{n%12+1:02d}';common=rng.normal(0,.035)
  rr=np.array([.006+1.3*common+rng.normal(0,.02),.004+common+rng.normal(0,.01),.001+rng.normal(0,.012),.002+rng.normal(0,.035),.0015])
  rows.append(dict(month=m,**dict(zip(['QQQ','US','BOND','GOLD','CASH'],rr)),SPY=.004+common));macro.append(dict(month=m,CPIAUCSL=100*np.exp(.002*i),IPMAN=100*np.exp(.001*i)))
 with tempfile.TemporaryDirectory(prefix='regime_FICTIONAL_')as td:
  p=Path(td);(p/'code').mkdir();(p/'raw').mkdir();shutil.copy2(ROOT/'code/engine.py',p/'code/engine.py')
  for file,values in [('monthly_returns.csv',rows),('macro_current_vintage.csv',macro)]:
   with(p/'raw'/file).open('w',newline='')as z:w=csv.DictWriter(z,fieldnames=values[0].keys());w.writeheader();w.writerows(values)
  child="import engine as e,json; r=[e.metrics(e.simulate(n,'2000-01','2005-12')) for n in ['QQQ','RegimeRule','BoydSimple']]; print(json.dumps({'warning':'FICTIONAL OBSERVATIONS; NOT EMPIRICAL PERFORMANCE','seed':20261013,'results':r},indent=2))"
  run=subprocess.run([sys.executable,'-c',child],cwd=p/'code',capture_output=True,text=True,check=True)
  (a.output/'FICTIONAL_demo_results.json').write_text(run.stdout)
  (a.output/'README.txt').write_text('Entirely fictional normal-factor observations. Illustrates the actual core accounting and allocation code. Cannot reproduce empirical paper statistics. Obtain licensed inputs according to docs/DATA_ACCESS.md for research replication.\n')
  print(a.output/'FICTIONAL_demo_results.json')
if __name__=='__main__':main()
