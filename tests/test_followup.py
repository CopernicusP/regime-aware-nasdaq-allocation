"""Focused empirical follow-up checks; daily files require private authorized inputs."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import followup_research as f
class ExecutionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.panels={t:f.load(t)[0]for t in f.TICKERS}
  import pandas as pd
  rr=f.BASE_R.copy()
  for k,t in enumerate(f.TICKERS[:5]):
   d=cls.panels[t];m=d.adjclose.groupby(d.index.to_period('M')).last().pct_change()
   for i,n in enumerate(f.e.D):
    v=m.get(pd.Period(f.e.label(n),'M'),np.nan)
    if np.isfinite(v):rr[i,k]=v
  cls.rr=rr
 def setUp(self):f.install(self.rr)
 def tearDown(self):f.install(f.BASE_R)
 def test_independent_monthly_accounting(self):
  for name in ['QQQ','RegimeRule','BoydSimple']:
   a=f.daily_sim(name,'2016-01','2025-12','boundary_close',.001,self.panels)
   b=f.e.simulate(name,'2016-01','2025-12',cost=.001)
   np.testing.assert_allclose(a['r'],b['r'],atol=2e-10,rtol=0)
 def test_buy_hold_observed_open_identity(self):
  a=f.daily_sim('QQQ','2016-01','2025-12','next_open',0.,self.panels)
  d=self.panels['QQQ'];expected=d.loc['2025-12-31','adjclose']/d.loc['2016-01-04','adjopen']
  self.assertAlmostEqual(np.prod(1+a['r']),expected,11)
  self.assertEqual(a['log'][0]['signal_close'],'2015-12-31');self.assertEqual(a['log'][0]['execution_date'],'2016-01-04')
 def test_target_frozen_before_open(self):
  p={t:d.copy()for t,d in self.panels.items()};p['QQQ'].loc['2016-01-04','adjopen']*=1.05
  a=f.daily_sim('RegimeRule','2016-01','2016-01','next_open',.001,self.panels)
  b=f.daily_sim('RegimeRule','2016-01','2016-01','next_open',.001,p)
  self.assertEqual([a['log'][0][x]for x in f.e.ASSETS],[b['log'][0][x]for x in f.e.ASSETS])
  self.assertNotEqual(a['log'][0]['nav'],b['log'][0]['nav'])
 def test_cost_self_financing(self):
  h=np.array([43.,17.,21.,9.,10.]);w=np.array([.2,.1,.3,.2,.2]);new,fee=f.fee_solve(h,w,.0025)
  self.assertAlmostEqual(new.sum()+fee,h.sum(),12)
  self.assertAlmostEqual(fee,.0025*abs(new-h).sum(),12)
if __name__=='__main__':unittest.main()
