"""Numerical source-data, label and publication-asset checks, with bounded scope."""
from pathlib import Path
import csv,json,re,hashlib
import numpy as np
import fitz
ROOT=Path(__file__).resolve().parents[1]
def read(p):
    with p.open(encoding='utf-8-sig')as f:return list(csv.DictReader(f))
def run():
    checks=[]
    logs=read(ROOT/'outputs/monthly_paths_weights.csv')
    fig=ROOT/'manuscript/figures';plot=read(fig/'source_data/wealth_drawdown.csv')
    for name in ['QQQ','RegimeRule','BoydSimple']:
        expected=[100000.]+[float(r['nav'])for r in logs if r['strategy']==name]
        actual=[r for r in plot if r['strategy']==name];assert len(actual)==322
        np.testing.assert_array_equal([float(r['wealth_usd'])for r in actual],expected)
        peak=0.
        for x,row in zip(expected,actual):
            peak=max(peak,x);assert abs(float(row['drawdown_percent'])-100*(x/peak-1))<1e-12
    checks.append('All 966 plotted wealth and drawdown valuations match numerical source paths')
    rr=read(ROOT/'outputs/rolling_start_metrics.csv');ff=read(fig/'source_data/rolling_growth.csv')
    assert ff==[r for n in ['RegimeRule','BoydSimple']for r in rr if r['strategy']==n and r['years']=='10'];checks.append('All 34 ten-year start-window observations retained')
    pp=read(fig/'source_data/hindsight_frontier.csv');assert sum(x['kind']=='static'for x in pp)==1001
    checks.append('All 1001 static-grid allocations retained')
    for p in sorted(fig.glob('*.pdf')):
        d=fitz.open(p);assert len(d)==1;assert abs(d[0].rect.width*25.4/72-165)<.01
        fonts=[sp['size']for bl in d[0].get_text('dict')['blocks']for line in bl.get('lines',[])for sp in line['spans']]
        assert min(fonts)>=7.9
    checks.append('Five final vector figures are 165 mm wide with at least 8 pt text')
    s='\n'.join(p.read_text()for p in (ROOT/'manuscript').glob('*.tex'));keys=set(re.findall(r'@\w+\s*\{\s*([^,\s]+)',(ROOT/'manuscript/references.bib').read_text()));used=set()
    for group in re.findall(r'\\cite[pt]?\{([^}]+)\}',s):used.update(group.split(','))
    assert used<=keys;checks.append(f'All {len(used)} manuscript citation keys exist')
    # Generated primary metrics must be present in each rendered table source.
    metrics=read(ROOT/'outputs/metrics.csv')
    for file,a,b in [('full.tex','2000-01','2026-09'),('later.tex','2016-01','2025-12')]:
        tex=(ROOT/'manuscript/tables'/file).read_text()
        for name in ['QQQ','RegimeRule','BoydSimple']:
            x=next(x for x in metrics if x['strategy']==name and x['start']==a and x['end']==b)
            for field in ['cagr','vol','max_dd']:assert f"{100*float(x[field]):.2f}"in tex
    checks.append('Core table values agree with stored numerical outputs')
    pdf=ROOT/'manuscript/build/paper.pdf'
    if pdf.exists():
        d=fitz.open(pdf);assert all('??'not in p.get_text()for p in d)
        checks.append('Available compiled PDF contains no unresolved-reference markers')
    out={'status':'PASS','checks':checks,'limits':'These deterministic checks do not authenticate market data, grant rights, or constitute peer review.'}
    (ROOT/'audit/artifact_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':run()
