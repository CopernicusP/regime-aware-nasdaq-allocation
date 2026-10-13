"""Generate publication tables and headline macros from saved computed outputs."""
import export_tables as t
from pathlib import Path
MET=t.MET
def metric(n,a='2000-01',b='2026-09'):
    return next(x for x in MET if x['strategy']==n and x['start']==a and x['end']==b)
names={'QQQ':'QQQ','SPY':'SPY','Static_70_20_10':'Static 70/20/10','Vol15':'Volatility control','RegimeRule':'R','BoydSimple':'M','BoydRidge':'MR','RegimeRobust':'RM','ProbabilityRobust':'PM','MacroRidge_Exploratory':'Legacy macro'}
mc=t.read('matched_control_metrics.csv')
def out_metrics(file,rows):
    t.table(file,['Method',r'CAGR (\%)',r'Vol. (\%)','Sharpe',r'MDD (\%)','Water'],[[name,t.p(x['cagr']),t.p(x['vol']),t.fmt(x['sharpe_arithmetic_excess']),t.p(x['max_dd']),x['longest_water_months']]for name,x in rows],'lrrrrr')
for fn,a,b in [('full.tex','2000-01','2026-09'),('later.tex','2016-01','2025-12')]:
    rows=[(names[n],metric(n,a,b))for n in ['QQQ','SPY','Static_70_20_10','Vol15','RegimeRule','BoydSimple']]
    rows.append(('Trend (10 months)',next(x for x in mc if x['strategy']=='Trend10_QQQ_Reserve'and x['start']==a)))
    out_metrics(fn,rows)
out_metrics('variants.tex',[(names[n],metric(n,'2016-01','2025-12'))for n in names])
rows=[]
for active,label in [('RegimeRule','R'),('BoydSimple','M')]:
    for suffix,text in [('',label),('_MeanWeights',label+' mean holdings'),('_RiskMatchedQQQ',label+' volatility match')]:
        x=next(x for x in mc if x['strategy']==active+suffix and x['design']=='validation_frozen')
        rows.append([text,t.p(x['cagr']),t.p(x['vol']),t.p(x['max_dd']),x['longest_water_months'],t.p(x['mean_equity'])])
t.table('matched.tex',['Policy/control',r'CAGR (\%)',r'Vol. (\%)',r'MDD (\%)','Water',r'Equity (\%)'],rows,'lrrrrr')
rs=t.read('classifier_horizon_audit.csv')
t.table('classifier.tex',['Signal dates','Last outcome','N','Events','Brier','Base Brier','AUC'],[[x['first_signal']+' to '+x['last_signal'],x['last_outcome'],x['n'],x['events'],f"{float(x['brier']):.5f}",f"{float(x['baseline_brier']):.5f}",f"{float(x['auc']):.3f}"]for x in rs],'llrrrrr')
rs=t.read('macro_vintage_metrics.csv');rows=[]
for name,label in [('BoydRidge','Price-only MR'),('MacroRidge_asof','As-of macro (SIC)'),('MacroRidge_latest','Latest macro (SIC)')]:
    a=metric(name)if name=='BoydRidge'else next(x for x in rs if x['strategy']==name and x['start']=='2000-01')
    b=metric(name,'2016-01','2025-12')if name=='BoydRidge'else next(x for x in rs if x['strategy']==name and x['start']=='2016-01')
    rows.append([label,t.p(a['cagr']),t.p(b['cagr']),t.p(b['max_dd']),b['longest_water_months']])
t.table('macro.tex',['Forecast',r'Full CAGR (\%)',r'Later CAGR (\%)',r'Later MDD (\%)','Water'],rows,'lrrrr')
rs=t.read('macro_forecast_metrics.csv')
t.table('macro_forecasts.tex',['Features',r'Price MSE',r'Macro MSE',r'Difference',r'95\% range'],[[x['kind'],f"{float(x['price_mse'])*1e6:.2f}",f"{float(x['macro_mse'])*1e6:.2f}",f"{float(x['difference_macro_minus_price'])*1e6:+.2f}",f"[{float(x['conditional_low95'])*1e6:+.2f}, {float(x['conditional_high95'])*1e6:+.2f}]"]for x in rs],'lrrrr')
rs=t.read('official_cpi_real_metrics.csv')
t.table('realall.tex',['Method',r'Real CAGR (\%)',r'Real MDD (\%)','Water (months)'],[[names[x['strategy']],t.p(x['real_cagr']),t.p(x['real_max_dd']),x['real_water_months']]for x in rs],'lrrr')
rs=t.read('rolling_start_summary.csv')
t.table('rolling.tex',['Policy','Years','Windows','Growth wins','MDD wins','Median growth gap'],[[names[x['strategy']],x['years'],x['windows'],x['growth_wins'],x['drawdown_wins'],t.p(x['median_growth_difference'],True)]for x in rs],'lrrrrr')
rs=t.read('issuer_checkpoint_summary.csv')
t.table('external_issuer.tex',['Series/basis','Windows','Max. absolute gap (bp)'],[[x['ticker']+' '+{'modern_market':'modern market','early_market':'early market','early_NAV_comparison':'early NAV'}[x['group']],x['comparisons'],t.fmt(x['max_absolute_difference_bp'])]for x in rs],'lrr')
rs=t.read('v4_rule_ablation.csv');print('ablation fields',list(rs[0]))
rs=t.read('downside_turnover_metrics.csv')
t.table('downside.tex',['Method','Sortino',r'Monthly ES (\%)','Two-way turnover','Orders/year'],[[names[x['strategy']],t.fmt(x['sortino_reserve_threshold']),t.p(x['cvar95_month']),t.fmt(x['turnover_two_way_annual']),t.fmt(x['orders_per_year'])]for x in rs if x['start']=='2000-01'],'lrrrr')
rs=t.read('bootstrap_conditional.csv');rows=[]
for x in rs:
    if x['strategy']not in ['RegimeRule','BoydSimple']:continue
    rows.append([names[x['strategy']],x['start'][:4]+'--'+x['end'][:4],t.p(x['annual_log_growth_difference'],True),'['+t.p(x['paired_CI95_low'],True)+', '+t.p(x['paired_CI95_high'],True)+']',t.fmt(x['bonferroni_p'])])
t.table('conditional.tex',['Policy','Window','Log-growth gap','95\\% interval','Adjusted $p$'],rows,'llrrr')
rs=t.read('matched_control_tests.csv')
t.table('matched_tests.tex',['Policy','Comparator','Log-growth gap','95\\% interval','Adjusted $p$'],[[names[x['active']],('Trend'if x['comparator'].startswith('Trend')else'Mean holdings'if x['comparator'].endswith('MeanWeights')else'Volatility match'),t.p(x['annual_log_growth_difference'],True),'['+t.p(x['low95'],True)+', '+t.p(x['high95'],True)+']',t.fmt(x['bonferroni_six_p'])]for x in rs],'llrrr')
mac=[]
for short,name in [('Q','QQQ'),('R','RegimeRule'),('M','BoydSimple')]:
    for period,a,b in [('Full','2000-01','2026-09'),('Later','2016-01','2025-12')]:
        x=metric(name,a,b)
        for field,suffix in [('cagr','Growth'),('max_dd','Drawdown'),('longest_water_months','Water')]:
            value=x[field]if field=='longest_water_months'else t.p(x[field])
            mac.append('\\newcommand{\\'+short+period+suffix+'}{'+value+'}')
(t.ROOT/'manuscript/numbers.tex').write_text('\n'.join(mac)+'\n')
print('Publication tables and numerical macros generated')
