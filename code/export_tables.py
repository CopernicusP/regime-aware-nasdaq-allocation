"""Generate all manuscript tables from the audited numeric outputs, never hand-entered values."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1];T=ROOT/'manuscript/tables';T.mkdir(exist_ok=True,parents=True)
def read(name):
 with (ROOT/'outputs'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
MET=read('metrics.csv')
NAMES={'QQQ':'QQQ buy-and-hold','SPY':'SPY buy-and-hold','Static_70_20_10':'Static 70/20/10','Static_50_20_20_10':'Static 50/20/20/10','Vol15':'V: volatility control','RegimeRule':'R: state rule','BoydSimple':'M: simple optimizer','BoydRidge':'MR: ridge optimizer','RegimeRobust':'RM: robust state','ProbabilityRobust':'PM: probability','MacroRidge_Exploratory':'MM: macro (exploratory)'}
def p(x,sign=False):
 v=float(x)*100
 return f'{v:+.2f}' if sign else f'{v:.2f}'
def fmt(x):return f'{float(x):.2f}'
def table(file,headers,rows,align):
 s='\\begin{tabular}{@{}'+align+'@{}}\\toprule\n'+' & '.join(headers)+r'\\\midrule'+'\n'
 s+='\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n\\bottomrule\n\\end{tabular}\n'
 (T/file).write_text(s)
def metrics_table(file,start,end,names):
 rows=[]
 for n in names:
  d=next(d for d in MET if d['strategy']==n and d['start']==start and d['end']==end)
  rows.append([NAMES[n],p(d['cagr']),p(d['vol']),fmt(d['sharpe_arithmetic_excess']),p(d['max_dd']),d['longest_water_months']])
 table(file,['Method',r'CAGR (\%)',r'Vol. (\%)','Sharpe',r'MDD (\%)','Water'],rows,'lrrrrr')
main=['QQQ','SPY','Static_70_20_10','Vol15','RegimeRule','BoydSimple','BoydRidge','RegimeRobust','ProbabilityRobust']
metrics_table('full.tex','2000-01','2026-09',main)
metrics_table('later.tex','2016-01','2025-12',main)
metrics_table('etfera.tex','2012-01','2026-09',['QQQ','SPY','RegimeRule','BoydSimple','BoydRidge','RegimeRobust'])
cr=read('crisis_periods.csv');rows=[]
for n in ['QQQ','RegimeRule','BoydSimple','BoydRidge','RegimeRobust']:
 rows.append([NAMES[n]]+[p(next(x['total_return']for x in cr if x['strategy']==n and x['period']==tag),True)for tag in ['Dotcom_2000_2002','GFC_2008','COVID_full','Tightening_2022']])
table('crisis.tex',['Method','2000--2002','2008','2020','2022'],rows,'lrrrr')
cl=read('classifier_eval.csv');rows=[]
for d in cl:
 rows.append([d['start'][:4]+'--'+d['end'][:4],d['n'],d['events'],f"{float(d['brier']):.5f}",f"{float(d['baseline_brier']):.5f}",f"{float(d['auc']):.3f}"])
table('classifier.tex',['Window','Forecasts','Events','Brier','Base Brier','AUC'],rows,'lrrrrr')
rr=read('real_performance.csv');rows=[]
for n in ['QQQ','RegimeRule','BoydSimple']:
 d=next(x for x in rr if x['strategy']==n);m=next(x for x in MET if x['strategy']==n and x['start']=='2000-01'and x['end']=='2026-09')
 rows.append([NAMES[n],m['longest_water_months'],d['real_water_months'],p(d['real_cagr'])])
table('real.tex',['Method','Nominal months','Real months',r'Real CAGR (\%)'],rows,'lrrr')
table('realall.tex',['Method',r'Real CAGR (\%)',r'Real MDD (\%)','Water'],[[NAMES[d['strategy']],p(d['real_cagr']),p(d['real_max_dd']),d['real_water_months']]for d in rr if d['strategy']in main],'lrrr')
ss=read('sensitivities.csv');cases=[('Base','base'),('Cost: 2.5 bp','cost_2.5bp'),('Cost: 25 bp','cost_25bp'),('Risk budget: 12\\%','risk_12pct'),('Risk budget: 18\\%','risk_18pct'),('One-month extra delay','delay_one_month'),('Zero realized reserve yield','cash_realized_zero'),('No no-trade band','no_trade_band_zero')];rows=[]
for label,case in cases:
 r=next(x for x in ss if x['strategy']=='RegimeRule'and x['case']==case);m=next(x for x in ss if x['strategy']=='BoydSimple'and x['case']==case)
 rows.append([label,p(r['cagr']),p(r['max_dd']),p(m['cagr']),p(m['max_dd'])])
table('sensitivity.tex',['Case',r'R CAGR (\%)',r'R MDD (\%)',r'M CAGR (\%)',r'M MDD (\%)'],rows,'lrrrr')
cost=read('fixed_policy_fee_replay.csv');rows=[]
for c in ['0.0','2.5','10.0','25.0']:
 r=next(x for x in cost if x['strategy']=='RegimeRule'and x['per_side_cost_bps']==c);m=next(x for x in cost if x['strategy']=='BoydSimple'and x['per_side_cost_bps']==c)
 rows.append([f'{float(c):g}',p(r['cagr']),p(m['cagr'])])
table('replay.tex',['Per-side cost (bp)',r'R CAGR (\%)',r'M CAGR (\%)'],rows,'rrr')
bt=read('bootstrap_pipeline_summary.csv');rows=[]
for n in ['RegimeRule','BoydSimple']:
 for tag,label,scale in [('cagr_difference','Growth difference',100),('sharpe_difference','Sharpe difference',1),('dd_reduction','Drawdown reduction',100)]:
  x=next(x for x in bt if x['strategy']==n and x['metric']==tag)
  rows.append(['R'if n=='RegimeRule'else'M',label,f"{float(x['median'])*scale:+.2f}",f"[{float(x['low95'])*scale:+.2f}, {float(x['high95'])*scale:+.2f}]"])
table('boot.tex',['Policy','Paired metric','Median','Central 95\\% range'],rows,'llrr')
tr=read('state_transitions.csv');rows=[]
for mo in ['2000-05','2000-08','2000-09','2000-11','2003-02','2003-05','2007-12','2009-04','2020-03','2022-01','2023-01']:
 found=[r for r in tr if r['signal_month']==mo]
 if found:
  x=found[0];rows.append([mo,x['return_month'],{'0':'Defensive','1':'Transition','2':'Risk-on'}[x['state']],x['score'],p(float(x['QQQ'])+float(x['US']))])
table('transitions.tex',['Signal month','Return month','State','Score',r'Equity (\%)'],rows,'llrrr')
serial=read('serial_sharpe_diagnostic.csv');rows=[]
for n in ['QQQ','RegimeRule','BoydSimple']:
 a=next(x for x in serial if x['strategy']==n and x['start']=='2000-01');b=next(x for x in serial if x['strategy']==n and x['start']=='2016-01')
 rows.append([NAMES[n],fmt(a['iid_scaled_sharpe']),fmt(a['serial_adjusted_12month_arithmetic_sharpe']),fmt(b['iid_scaled_sharpe']),fmt(b['serial_adjusted_12month_arithmetic_sharpe'])])
table('serial.tex',['Method','Full: conventional','Full: adjusted','Later: conv.','Later: adj.'],rows,'lrrrr')
# Data supplied to the concise Chinese document, numbers tied to the same output.
cn={}
for key,n in [('Q','QQQ'),('R','RegimeRule'),('M','BoydSimple')]:
 cn[key]={}
 for window,start,end in [('Full','2000-01','2026-09'),('Later','2016-01','2025-12')]:
  x=next(x for x in MET if x['strategy']==n and x['start']==start and x['end']==end)
  cn[key][window]={k:x[k]for k in ['cagr','vol','max_dd','longest_water_months','terminal_100k']}
tex=[]
for name,periods in cn.items():
 for window,x in periods.items():
  for k,suffix in [('cagr','Cagr'),('max_dd','Drawdown'),('longest_water_months','Water')]:
   value=x[k]if k=='longest_water_months'else p(x[k])
   tex.append('\\newcommand{\\'+name+window+suffix+'}{'+value+'}')
if (ROOT/'chinese').is_dir():
 (ROOT/'chinese/numbers.tex').write_text('\n'.join(tex)+'\n')
print('Generated',len(list(T.glob('*.tex'))),'tables from audited outputs (Chinese macros only if that optional folder exists).' )
