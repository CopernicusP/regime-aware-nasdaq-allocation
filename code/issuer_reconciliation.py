"""Reconcile independently retrieved aggregate issuer/SEC checkpoints.

Inputs are short numeric transcriptions checked against rendered issuer PDFs
and the SEC-hosted bar chart. NAV and market-price comparisons remain distinct.
This is not validation of individual daily prices or corporate actions.
"""
import hashlib,json
import numpy as np
import engine as e
ROOT=e.ROOT

def run():
    old=e.read(ROOT/'checks/data/issuer_return_checkpoints.csv')
    rows=[]
    for x in old:
        if x['source_date_status']!='CONSISTENT_DATE':continue
        rows.append(dict(ticker=x['ticker'],end=x['end_month'],months=int(x['horizon_months']),issuer_percent=float(x['issuer_return_percent']),basis=x['return_basis'],source=x['source_url'],source_location='issuer fact sheet, p. 1',group='modern_market'))
    qurl='https://www.invesco.com/us-rest/contentdetail?contentId=841e411c-a1eb-4541-8cb8-0fa603abea81&dnsName=us'
    surl='https://www.ssga.com/library-content/products/factsheets/etfs/us/factsheet-us-en-spy.pdf'
    for ticker,vals,url,pg in [('QQQ',{6:20.09,12:34.00,36:26.53,60:16.43,120:22.08},qurl,2),('SPY',{3:15.08,6:10.02,12:22.08,36:20.44,60:13.25,120:15.34},surl,1)]:
        for n,v in vals.items():rows.append(dict(ticker=ticker,end='2026-06',months=n,issuer_percent=v,basis='market_price'if ticker=='QQQ'else'midpoint_at_NAV_time',source=url,source_location=f'issuer fact sheet, p. {pg}',group='modern_market'))
    sec07='https://www.sec.gov/Archives/edgar/data/1067839/000120677407000279/nasdaq_485bpos.htm'
    for year,v in zip(range(2000,2007),[-36.93,-32.78,-37.66,49.17,10.47,1.66,7.02]):
        rows.append(dict(ticker='QQQ',end=f'{year}-12',months=12,issuer_percent=v,basis='NAV_total_return',source=sec07,source_location='p. 6, Annual Total Returns chart',group='early_NAV_comparison'))
    sec09='https://www.sec.gov/Archives/edgar/data/1067839/000110465910001821/a09-31668_2n30b2.htm'
    for end,n,v,basis,loc in [('2009-09',12,8.41,'market_close_total_return','p. 16'),('2009-09',60,4.12,'market_close_total_return','p. 16'),('2008-09',12,-23.50,'NAV_total_return','p. 9')]:
        rows.append(dict(ticker='QQQ',end=end,months=n,issuer_percent=v,basis=basis,source=sec09,source_location=loc,group='early_NAV_comparison'if basis.startswith('NAV')else'early_market'))
    mapping={'QQQ':0,'VTI':1,'BND':2,'GLD':3}
    for x in rows:
        n=x['months'];end=e.mn(x['end']);start=end-n+1;take=(e.D>=start)&(e.D<=end)
        r=e.SPY[take]if x['ticker']=='SPY'else e.R[take,mapping[x['ticker']]]
        assert len(r)==n and np.isfinite(r).all()
        gross=float(np.prod(1+r));value=100*(gross**(12/n)-1)if n>12 else 100*(gross-1)
        x.update(start=e.label(start),computed_percent=value,difference_bp=(value-x['issuer_percent'])*100,retrieved='2026-10-13',status='AGGREGATE_COHERENCE_ONLY',annualized=n>12)
    e.write(ROOT/'outputs/issuer_checkpoint_comparison.csv',rows)
    summary=[]
    for group in sorted(set(x['group']for x in rows)):
        for ticker in sorted(set(x['ticker']for x in rows if x['group']==group)):
            rs=[x for x in rows if x['group']==group and x['ticker']==ticker]
            summary.append(dict(group=group,ticker=ticker,comparisons=len(rs),max_absolute_difference_bp=max(abs(x['difference_bp'])for x in rs),mean_absolute_difference_bp=float(np.mean([abs(x['difference_bp'])for x in rs]))))
    e.write(ROOT/'outputs/issuer_checkpoint_summary.csv',summary)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'audit/external').glob('*_issuer.pdf')}
    (ROOT/'audit/issuer_reconciliation.json').write_text(json.dumps(dict(rows=len(rows),summary=summary,document_sha256=hashes,scope='Overlapping aggregate checks. Early NAV/market differences are retained; no threshold fitted. No complete corporate-action or daily-price audit.'),indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':run()
