"""Validate a legally obtained normalized daily export, without network/credentials.
Usage: --input export.csv --provider CRSP_CIZ --output authorized_daily.csv
Required normalized columns: ticker,date,open,high,low,close,adjclose.
Obtain/document provider column mapping and adjustment convention before export.
Negative CRSP price flags or missing opens are rejected, never converted to fills.
"""
import argparse,json,hashlib
from pathlib import Path
import pandas as pd

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--provider',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--adjustment-description',required=True);a=p.parse_args()
 d=pd.read_csv(a.input);fields=['ticker','date','open','high','low','close','adjclose'];assert set(fields)<=set(d.columns),'Map documented provider fields into required schema first'
 assert not d.duplicated(['ticker','date']).any();pd.to_datetime(d.date,format='%Y-%m-%d',errors='raise')
 assert d[fields].notna().all().all(),'Missing observations are not executable fills'
 assert (d[fields[2:]]>0).all().all(),'Nonpositive prices/CRSP quote flags require source review'
 assert (d.high+1e-5>=d[['open','close']].max(axis=1)).all()and(d.low-1e-5<=d[['open','close']].min(axis=1)).all()
 assert a.output.resolve()!=a.input.resolve(),'Preserve original export'
 a.output.parent.mkdir(parents=True,exist_ok=True);d.sort_values(['ticker','date']).to_csv(a.output,index=False)
 a.output.with_suffix('.provenance.json').write_text(json.dumps(dict(provider=a.provider,input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),rows=len(d),adjustment_description=a.adjustment_description,authorization='Supplied by operator; this adapter does not grant access or redistribution rights',quote_time='Must be supplied in acquisition documentation; OHLC open does not prove auction execution'),indent=2))
if __name__=='__main__':main()
