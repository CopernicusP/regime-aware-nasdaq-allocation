"""Synthetic accounting fixtures and historical calendar/as-of checks.
No fixture is treated as an observed security return or reported performance.
"""
from __future__ import annotations
import copy, unittest
import numpy as np
from validation import select_snapshot,snapshot_growth,next_open_step,session_calendar

def row(month,value,available='2008-10-16T08:30:00-04:00',vintage='original'):
 return dict(series='CPI',observation_month=month,value=value,available_at=available,vintage_id=vintage,units='same SA basis')
class ValidationTests(unittest.TestCase):
 def test_unreleased_value_rejected(self):
  with self.assertRaises(ValueError):select_snapshot([row('2008-09',218.813)],'CPI','2008-09-30T16:00:00-04:00')
 def test_release_minute_gate(self):
  with self.assertRaises(ValueError):select_snapshot([row('2008-09',218.813)],'CPI','2008-10-16T08:29:00-04:00')
  self.assertIn('2008-09',select_snapshot([row('2008-09',218.813)],'CPI','2008-10-16T08:30:00-04:00'))
 def test_future_revision_does_not_leak(self):
  a=[row('2008-08',218.880),row('2008-09',218.813)]
  original=select_snapshot(a,'CPI','2008-10-31T16:00:00-04:00')
  b=a+[row('2008-08',500,'2009-01-01T08:30:00-05:00','later'),row('2008-09',1000,'2009-01-01T08:30:00-05:00','later')]
  self.assertEqual(original,select_snapshot(b,'CPI','2008-10-31T16:00:00-04:00'))
 def test_one_snapshot_exact_lag(self):
  snap=select_snapshot([row('2008-08',218.880),row('2008-09',218.813)],'CPI','2008-10-31T16:00:00-04:00')
  self.assertAlmostEqual(snapshot_growth(snap,'2008-09',1),218.813/218.880-1)
  with self.assertRaises(ValueError):snapshot_growth(snap,'2008-09',12)
 def test_no_cross_vintage_fallback(self):
  a=[row('2008-08',218.88),row('2008-09',218.813,'2008-11-01T08:30:00-04:00','later')]
  snap=select_snapshot(a,'CPI','2008-11-02T16:00:00-05:00')
  with self.assertRaises(ValueError):snapshot_growth(snap,'2008-09',1)
 def test_timezone_required(self):
  with self.assertRaises(ValueError):select_snapshot([row('2008-09',1)],'CPI','2008-10-31T16:00:00')
 def test_mixed_basis_rejected(self):
  a=[row('2008-08',1),row('2008-09',2)];a[-1]['units']='NSA'
  with self.assertRaises(ValueError):select_snapshot(a,'CPI','2008-10-31T16:00:00-04:00')
 def test_duplicate_month_rejected(self):
  with self.assertRaises(ValueError):select_snapshot([row('2008-09',1),row('2008-09',2)],'CPI','2008-10-31T16:00:00-04:00')
 def test_exit_carries_old_overnight_loss(self):
  z=next_open_step(np.array([100.,0]),np.array([.9,1]),np.ones(2),np.array([0.,1]),np.zeros(2))
  self.assertAlmostEqual(z['end_wealth'],90)
 def test_new_purchase_does_not_earn_previous_gap(self):
  z=next_open_step(np.array([0.,100]),np.array([.9,1]),np.array([1.1,1]),np.array([1.,0]),np.zeros(2))
  self.assertAlmostEqual(z['end_wealth'],110)
 def test_cost_self_financing(self):
  z=next_open_step(np.array([50.,50]),np.ones(2),np.ones(2),np.array([1.,0]),np.array([.001,.001]))
  self.assertAlmostEqual(z['posttrade_wealth']+z['fees'],100)
  self.assertLess(z['end_wealth'],100)
 def test_no_trade_no_cost(self):
  z=next_open_step(np.array([40.,60]),np.ones(2),np.ones(2),np.array([.4,.6]),np.array([.001,.001]))
  self.assertAlmostEqual(z['fees'],0)
 def test_no_borrow_or_short(self):
  with self.assertRaises(ValueError):next_open_step(np.array([100.,0]),np.ones(2),np.ones(2),np.array([1.2,-.2]),np.zeros(2))
 def test_missing_factor_not_interpolated(self):
  with self.assertRaises(ValueError):next_open_step(np.array([100.,0]),np.array([np.nan,1]),np.ones(2),np.array([1.,0]),np.zeros(2))
 def test_bad_weight_sum(self):
  with self.assertRaises(ValueError):next_open_step(np.array([100.,0]),np.ones(2),np.ones(2),np.array([.4,.4]),np.zeros(2))
 def test_month_end_holiday_calendar(self):
  c=session_calendar()
  self.assertFalse(c.is_session('2018-03-30'))
  self.assertEqual(str(c.next_session('2018-03-29').date()),'2018-04-02')
  self.assertEqual(str(c.next_session('1999-12-31').date()),'2000-01-03')
 def test_special_closures(self):
  c=session_calendar()
  self.assertEqual(str(c.next_session('2001-09-10').date()),'2001-09-17')
  self.assertEqual(str(c.next_session('2012-10-26').date()),'2012-10-31')
 def test_nyse_good_friday_2026(self):
  c=session_calendar()
  self.assertFalse(c.is_session('2026-04-03'))
  self.assertEqual(str(c.next_session('2026-04-02').date()),'2026-04-06')
if __name__=='__main__':unittest.main(verbosity=2)
