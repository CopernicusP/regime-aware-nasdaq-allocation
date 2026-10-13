"""Independent invariants for consequential financial calculations."""
from pathlib import Path
import sys,unittest,copy,math
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import engine as e
import macro_vintages as mv
from additional_experiments import ledger,benchmark_weights

class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.panels={n:mv.load_panel(n)for n in ['pcpi','ipm']}
    def test_months_unique_contiguous_and_finite(self):
        self.assertEqual(len(e.D),330);np.testing.assert_array_equal(np.diff(e.D),1)
        self.assertTrue(np.isfinite(e.R).all());self.assertTrue((e.R>-1).all())
    def test_cash_reference_exact_prior_month(self):
        rates={x['month']:float(x['cash_yield_pct_source'])for x in e.read(e.ROOT/'raw/qqq_warmup_and_bill_rates.csv')}
        for row in e.DATA:
            prev=e.label(e.mn(row['month'])-1);self.assertEqual(row['cash_yield_reference'],prev)
            self.assertAlmostEqual(float(row['CASH']),rates[prev]/1200-.0009/12,places=14)
    def test_independent_metrics_and_accounting(self):
        for name in ['QQQ','RegimeRule','BoydSimple']:
            s=e.simulate(name);m=e.metrics(s);nav=100000.;peak=nav;dd=0.;lastpeak=0;longest=0
            for j,r in enumerate(s['r'],1):
                nav*=1+float(r);peak=max(peak,nav);dd=max(dd,1-nav/peak)
                if nav>=peak*(1-1e-10):
                    if j-lastpeak>1:longest=max(longest,j-lastpeak)
                    lastpeak=j
                else:longest=max(longest,j-lastpeak)
            self.assertAlmostEqual(nav,s['path'][-1],places=6)
            self.assertAlmostEqual(m['cagr'],math.expm1(math.log(nav/100000.)*12/321),places=12)
            self.assertAlmostEqual(m['max_dd'],dd,places=12);self.assertEqual(m['longest_water_months'],longest)
            np.testing.assert_allclose(s['W'].sum(1),1,atol=1e-12);self.assertTrue((s['W']>=0).all())
    def test_initial_deployment_cost_hand_value(self):
        w=np.array([1,0,0,0,0.]);s=ledger('2000-01','2000-01',lambda _:w,'fixture',cost=.001)
        expect=100000/1.001*(1+e.R[np.searchsorted(e.D,e.mn('2000-01')),0])
        self.assertAlmostEqual(s['path'][-1],expect,places=8)
    def test_future_returns_do_not_change_multiple_decisions(self):
        oldr=e.R.copy();oldp=e.P.copy();oldest=e.EST
        try:
            for month in ['2000-01','2008-09','2016-01','2022-01']:
                e.R[:]=oldr;e.P[:]=oldp;e.EST=e.Estimator();i=np.searchsorted(e.D,e.mn(month));pre=np.array([.3,.1,.2,.1,.3])
                before={n:e.target(n,i,pre)[0]for n in ['RegimeRule','BoydSimple','BoydRidge']}
                e.R[i:,:4]=.07;e.P=np.vstack([np.ones(5),np.cumprod(1+e.R,axis=0)]);e.EST=e.Estimator()
                for name,w in before.items():np.testing.assert_allclose(e.target(name,i,pre)[0],w,rtol=0,atol=1e-11)
        finally:e.R[:]=oldr;e.P=oldp;e.EST=oldest
    def test_training_label_horizon_matured(self):
        for i in range(9,len(e.D)):
            self.assertLessEqual(e.EST.get(i).known_label_last,i)
    def test_macro_future_vintage_is_irrelevant(self):
        s=e.mn('2008-10');base,meta=mv.feature_row(s,self.panels)
        altered={name:{v:(vals if v<=s-1 else {d:x*3 for d,x in vals.items()})for v,vals in p.items()}for name,p in self.panels.items()}
        after,meta2=mv.feature_row(s,altered);np.testing.assert_array_equal(base,after);self.assertEqual(meta,meta2)
    def test_macro_exact_same_vintage_ratios(self):
        s=e.mn('2022-06');x,meta=mv.feature_row(s,self.panels);ref=s-2
        cp=self.panels['pcpi'][e.mn(meta['pcpi_vintage'])];ip=self.panels['ipm'][e.mn(meta['ipm_vintage'])]
        np.testing.assert_allclose(x,[cp[ref]/cp[ref-12]-1,(cp[ref]/cp[ref-12]-1)-(cp[ref-6]/cp[ref-18]-1),ip[ref]/ip[ref-12]-1],atol=0,rtol=0)
        for key,v in meta.items():self.assertLessEqual(e.mn(v),s-1)
    def test_macro_missing_exact_lag_rejected(self):
        with self.assertRaises(ValueError):mv.feature_row(e.mn('2025-12'),self.panels)
    def test_latest_cpi_matches_inherited_levels(self):
        values=self.panels['pcpi'][max(self.panels['pcpi'])];count=0
        for d,x in e.MAC.items():
            if d in values and np.isfinite(x[0]):self.assertEqual(x[0],values[d]);count+=1
        self.assertGreater(count,300)
    def test_frozen_control_calibration_dates(self):
        for r in e.read(e.OUT/'matched_control_weights.csv'):
            if r['design']=='validation_frozen':self.assertEqual(r['calibration_end'],'2015-12')
        for name in ['RegimeRule','BoydSimple']:
            _,w,target=benchmark_weights(name,'2010-01','2015-12')
            s=ledger('2010-01','2015-12',lambda _:w,'check')
            self.assertAlmostEqual(np.std(s['r'],ddof=1)*np.sqrt(12),target,places=10)
    def test_bootstrap_family_complete(self):
        rows=e.read(e.OUT/'bootstrap_conditional.csv');self.assertEqual(len(rows),12)
        for r in rows:
            self.assertEqual(int(r['n_boot']),20000)
            self.assertAlmostEqual(float(r['bonferroni_p']),min(1,12*float(r['centered_one_sided_p'])),places=14)
    def test_classifier_outcomes_end_in_declared_period(self):
        r=next(r for r in e.read(e.OUT/'classifier_horizon_audit.csv')if r['scope']=='outcome_bounded')
        self.assertEqual(r['last_outcome'],'2025-12');self.assertEqual(int(r['n']),118)

if __name__=='__main__':unittest.main(verbosity=2)
