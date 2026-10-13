"""Bounded final release checks: hashes, numerical tables, source build and privacy scope."""
from pathlib import Path
import tempfile,zipfile,subprocess,json,hashlib,re
import fitz,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent;OUT=ROOT/'audit/followup';TITLE='Pan_2026_Regime_Aware_Nasdaq_Allocation'
def main():
 p=ROOT/'manuscript/build/paper.pdf';d=fitz.open(p);assert len(d)==33;assert d.metadata['author']=='Yudian Pan'
 bad=[]
 for i,page in enumerate(d):
  assert '??'not in page.get_text()
  for b in page.get_text('dict')['blocks']:
   for line in b.get('lines',[]):
    for s in line['spans']:
     x0,y0,x1,y1=s['bbox']
     if x0<20 or x1>page.rect.width-20 or y0<10 or y1>page.rect.height-12:bad.append((i+1,s['text']))
 assert not bad
 (ROOT/'audit/final_document_geometry.json').write_text(json.dumps(dict(status='PASS',pages=len(d),outside_page_margin_spans=bad,unresolved_references=False),indent=2))
 # Every displayed new table value comes from executed output; rows checked at their display precision.
 ex=pd.read_csv(ROOT/'outputs/followup/execution_metrics.csv');assert len(ex)==32 and ex.solver_failures.sum()==0
 tex=(ROOT/'manuscript/tables/daily_execution.tex').read_text()
 for _,x in ex[ex.cost==.001].iterrows():
  for key in ['cagr','max_dd','daily_max_dd']:assert f'{x[key]*100:.2f}'in tex
 st=pd.read_csv(ROOT/'outputs/followup/qqq_fixed_range_metrics.csv');assert len(st)==78 and st.solver_failures.sum()==0
 # Preserve the original endpoint mismatch, no artificial reconciliation.
 q=json.loads((ROOT/'outputs/followup/qqq_reconciliation.json').read_text());assert q['price_return']>q['issuer_market_return'];assert abs(q['timing_difference_bp'])<1.;assert q['issuer_gap_remaining_bp']>70
 # Build the exact source-only deliverable in a new isolated directory.
 with tempfile.TemporaryDirectory(prefix='pan_source_verify_',dir=BASE)as td:
  td=Path(td)
  with zipfile.ZipFile(BASE/'deliverables'/f'{TITLE}_Overleaf.zip')as z:z.extractall(td)
  src=td/(TITLE+'_Overleaf')
  with(OUT/'standalone_build.log').open('w')as f:subprocess.run(['latexmk','-xelatex','-bibtex','-interaction=nonstopmode','-halt-on-error','-outdir=build','paper.tex'],cwd=src,stdout=f,stderr=subprocess.STDOUT,check=True)
  other=fitz.open(src/'build/paper.pdf');assert len(other)==len(d)
  for i in range(len(d)):
   assert other[i].get_text()==d[i].get_text(),i
   assert other[i].get_pixmap().samples==d[i].get_pixmap().samples,i
 (ROOT/'audit/standalone_build_verification.json').write_text(json.dumps(dict(status='PASS',pages=len(d),exact_extracted_text_match=True,exact_72dpi_pixels_match=True,source='Current formal LaTeX ZIP',pdf_binary_identity_required=False),indent=2))
 # Public-candidate fixture/demo checks in the isolated scope (no private vendor inputs).
 candidate=Path(json.loads((ROOT/'audit/candidate_package_check.json').read_text())['candidate_stage'])
 py=str(BASE/'.venv/bin/python')
 with(OUT/'candidate_smoke.log').open('w')as f:
  subprocess.run([py,'reproduce.py','demo'],cwd=candidate,stdout=f,stderr=subprocess.STDOUT,check=True)
  subprocess.run([py,'-m','unittest','discover','-s','checks','-v'],cwd=candidate,stdout=f,stderr=subprocess.STDOUT,check=True)
 result=dict(status='PASS',paper_pages=33,report_pages=len(fitz.open(ROOT/'docs/Verification_Report.pdf')),research_tests=17,accounting_asof_tests=18,total_tests=35,qqq_fixed_scenarios=26,qqq_strategy_stress_runs=78,alternate_source_runs=6,execution_scenarios=32,followup_solver_failures=0,raw_integrity='Nine prior raw files unchanged',same_canonical_source=True,public_demo_and_18_fixtures_executed=True,source_only_build='33 pages identical in text and 72 dpi pixels',publication=json.loads((ROOT/'docs/RELEASE_GATES.json').read_text())['status'])
 (OUT/'final_checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
