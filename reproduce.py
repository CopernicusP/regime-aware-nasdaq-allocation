#!/usr/bin/env python3
"""Explicit offline modes. A successful command means its stages actually ran."""
from pathlib import Path
import argparse,os,sys,subprocess,json,time
ROOT=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['verify','core','full','figures','build','demo','followup']);ap.add_argument('--dry-run',action='store_true');args=ap.parse_args()
    py=sys.executable
    numerical=['prepare_data.py','engine.py','robustness.py','statistics.py','end_to_end_check.py','v4_solver_certificate.py','v4_rule_ablation.py','additional_experiments.py','macro_vintages.py','publication_analysis.py','issuer_reconciliation.py','recovery_audit.py','followup_research.py','followup_tables.py']
    stages=[]
    if args.mode=='demo':stages=[[py,'code/synthetic_demo.py']]
    if args.mode=='followup':stages=[[py,'code/followup_research.py'],[py,'code/followup_tables.py'],[py,'-m','unittest','discover','-s','tests','-p','test_followup.py','-v']]
    if args.mode=='core':stages=[[py,'code/'+x]for x in ['prepare_data.py','engine.py','publication_analysis.py']]
    if args.mode=='full':stages=[[py,'code/'+x]+(['--fresh']if x=='end_to_end_check.py'else[])for x in numerical]
    if args.mode in ['full','figures']:stages += [[py,'code/publication_tables.py'],[py,'code/export_figures.py']]
    if args.mode in ['full','verify']:stages += [[py,'-m','unittest','discover','-s','tests','-v'],[py,'-m','unittest','discover','-s','checks','-v'],[py,'code/validate_artifacts.py']]
    if args.mode in ['full','build']:stages += [['latexmk','-cd','-xelatex','-bibtex','-interaction=nonstopmode','-halt-on-error','-outdir=build','manuscript/paper.tex']]
    if args.dry_run:
        print(json.dumps({'mode':args.mode,'commands':stages,'executes':False},indent=2));return
    audit=ROOT/'audit';audit.mkdir(exist_ok=True)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONHASHSEED='0')
    results=[]
    for i,cmd in enumerate(stages):
        log=audit/f'runner_{args.mode}_{i:02d}.log';t=time.monotonic();print('RUN',' '.join(cmd),flush=True)
        with log.open('w')as f:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
        results.append(dict(command=cmd,exit_code=r.returncode,seconds=round(time.monotonic()-t,3),log=str(log.relative_to(ROOT))))
        (audit/f'runner_{args.mode}.json').write_text(json.dumps(results,indent=2))
        if r.returncode:raise SystemExit(f'FAILED: see {log}')
    print(f'PASS: {len(results)} stages executed for {args.mode}.')
if __name__=='__main__':main()
