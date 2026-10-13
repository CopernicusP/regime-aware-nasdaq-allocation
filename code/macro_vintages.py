"""Parse unmodified official XLSX vintage matrices using standard-library XML.

Avoids an openpyxl failure on the source IPM document's date-only core metadata.
No observations or metadata in the source workbook are modified.
"""
from pathlib import Path
import zipfile, xml.etree.ElementTree as ET, re, json
import numpy as np
import engine as e
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
ROOT=Path(__file__).resolve().parents[1]

def workbook_cells(path):
    with zipfile.ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared=[''.join(el.itertext()) for el in root.findall('s:si',NS)]
        sheets=[n for n in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n)]
        assert len(sheets)==1,(path,sheets)
        root=ET.fromstring(z.read(sheets[0]));rows=[]
        for rr in root.findall('.//s:sheetData/s:row',NS):
            row={}
            for c in rr.findall('s:c',NS):
                v=c.find('s:v',NS);t=c.get('t');val=None
                if t=='inlineStr':val=''.join(c.find('s:is',NS).itertext())
                elif v is not None:
                    val=v.text
                    if t=='s':val=shared[int(val)]
                    elif t=='e':val=None
                    else:
                        try:val=float(val)
                        except (TypeError,ValueError):pass
                row[re.sub(r'\d','',c.get('r'))]=val
            rows.append(row)
        return rows

def load_panel(name):
    rows=workbook_cells(ROOT/'audit/external'/f'{name}.xlsx');header=rows[0];panel={}
    for col,label in header.items():
        m=re.search(r'(\d{2})M(\d{1,2})$',str(label))
        if m:
            yy,mm=map(int,m.groups());year=2000+yy if yy<=26 else 1900+yy
            panel[e.mn(f'{year}-{mm:02d}')]=(col,{})
    for row in rows[1:]:
        label=row.get('A');m=re.fullmatch(r'(\d{4}):(\d{2})',str(label))
        if not m:continue
        date=e.mn('-'.join(m.groups()))
        for vintage,(col,values) in panel.items():
            val=row.get(col)
            if isinstance(val,(float,int)) and np.isfinite(val):values[date]=float(val)
    return {k:v[1] for k,v in panel.items()}

def feature_row(signal,panels,latest=False):
    ref=signal-2;fields=[];meta={};vs=[]
    for name in ['pcpi','ipm']:
        panel=panels[name]
        candidates=[v for v in panel if v<=signal-1]
        if not candidates:raise ValueError('No sufficiently early vintage')
        vintage=max(panel) if latest else max(candidates);values=panel[vintage];vs.append(vintage)
        lags=[0,6,12,18] if name=='pcpi' else [0,12]
        vals=[values.get(ref-l,np.nan) for l in lags]
        if not np.isfinite(vals).all():raise ValueError(f'Missing exact lag: {name} vintage {e.label(vintage)} reference {e.label(ref)}')
        if name=='pcpi':fields.extend([vals[0]/vals[2]-1,(vals[0]/vals[2]-1)-(vals[1]/vals[3]-1)])
        else:fields.append(vals[0]/vals[1]-1)
        meta[name+'_vintage']=e.label(vintage)
    return np.array(fields),meta

def run():
    panels={n:load_panel(n) for n in ['pcpi','ipm']};rows=[];features={k:{} for k in ['asof','latest']};failures=[]
    for i in range(9,len(e.D)+1):
        signal=int((e.D[i] if i<len(e.D) else e.D[-1]+1)-1)
        for kind in features:
            try:
                x,meta=feature_row(signal,panels,kind=='latest');features[kind][i]=x
                rows.append({'signal_month':e.label(signal),'kind':kind,'reference_month':e.label(signal-2),**meta,'cpi_yoy':x[0],'cpi_yoy_change6':x[1],'ipm_yoy':x[2]})
            except ValueError as exc:failures.append({'signal_month':e.label(signal),'kind':kind,'error':str(exc)})
    # Eligibility is determined solely by historically available information.
    # The latest-vintage comparator must cover that set; it cannot determine it.
    common=set(features['asof'])
    assert common <= set(features['latest']), 'Latest comparator lacks an as-of eligible origin'
    original_features=e.features;original_est=e.ESTM;metrics=[];paths=[];fallbacks={};predictions=[]
    for kind in ['asof','latest']:
        def f(i,macro=False):
            base=original_features(i,False)
            return np.r_[base,features[kind].get(i,np.full(3,np.nan)) if i in common else np.full(3,np.nan)] if macro else base
        e.features=f
        class VintageEstimator(e.Estimator):
            def get(self,i,kind='ridge',covwindow=36):
                if i not in common:
                    return e.EST.get(i,kind,covwindow)
                return super().get(i,kind,covwindow)
        e.ESTM=VintageEstimator(True)
        # Outcome-bounded diagnostic, added after the portfolio extension was
        # specified; no forecast, parameter or policy is selected with it.
        for i in range(9,len(e.D)-2):
            if e.D[i]<e.mn('2016-01') or e.D[i+2]>e.mn('2025-12'):continue
            target=(np.prod(1+e.R[i:i+3,:4],axis=0)-np.prod(1+e.R[i:i+3,4]))/3
            price=e.EST.get(i);macro_est=e.ESTM.get(i)
            for j,a in enumerate(e.ASSETS[:4]):
                predictions.append({'kind':kind,'signal_month':e.label(int(e.D[i]-1)),
                    'outcome_end':e.label(int(e.D[i+2])),'asset':a,'target':float(target[j]),
                    'price_prediction':float(price.mu[j]),'macro_prediction':float(macro_est.mu[j]),
                    'price_squared_error':float((price.mu[j]-target[j])**2),
                    'macro_squared_error':float((macro_est.mu[j]-target[j])**2),
                    'asof_eligible':i in common})
        for a,b in [('2000-01','2026-09'),('2016-01','2025-12')]:
            s=e.simulate('MacroRidge_Exploratory',a,b);s['name']='MacroRidge_'+kind
            metrics.append(e.metrics(s,e.simulate('QQQ',a,b)))
            paths += [{'kind':kind,'start':a,'month':e.label(int(d)),'net_return':float(r),**dict(zip(e.ASSETS,map(float,w)))} for d,r,w in zip(s['dates'],s['r'],s['W'])]
        fallbacks[kind]=[e.label(int(e.D[i]-1)) for i in range(9,len(e.D)) if i not in common]
    e.features=original_features;e.ESTM=original_est
    e.write(e.OUT/'macro_vintage_features.csv',rows);e.write(e.OUT/'macro_vintage_missing.csv',failures)
    e.write(e.OUT/'macro_vintage_metrics.csv',metrics);e.write(e.OUT/'macro_vintage_paths.csv',paths)
    e.write(e.OUT/'macro_forecast_predictions.csv',predictions)
    forecast=[]
    for kind in ['asof','latest']:
        rs=[x for x in predictions if x['kind']==kind]
        months=sorted(set(x['signal_month'] for x in rs))
        delta=np.array([np.mean([x['macro_squared_error']-x['price_squared_error'] for x in rs if x['signal_month']==m])for m in months])
        rng=np.random.default_rng(13102027);n=len(months);B=9999;L=12
        ix=((rng.integers(0,n,size=(B,int(np.ceil(n/L))))[:,:,None]+np.arange(L))%n).reshape(B,-1)[:,:n]
        lo,hi=np.quantile(delta[ix].mean(1),[.025,.975])
        forecast.append({'kind':kind,'origins':n,'asset_predictions':len(rs),'price_mse':np.mean([x['price_squared_error']for x in rs]),'macro_mse':np.mean([x['macro_squared_error']for x in rs]),'difference_macro_minus_price':delta.mean(),'conditional_low95':lo,'conditional_high95':hi,'block_months':L,'B':B,'scope':'Exploratory conditional paired forecast-loss diagnostic; monthly vectors resampled together; overlapping three-month labels; no selection'})
    e.write(e.OUT/'macro_forecast_metrics.csv',forecast)
    # Latest official CPI is for ex-post purchasing-power evaluation only.
    frozen=e.MAC;latest_pcpi=panels['pcpi'][max(panels['pcpi'])];latest_ipm=panels['ipm'][max(panels['ipm'])]
    comparison=[]
    for date,v in frozen.items():
        for j,name,source in [(0,'CPIAUCSL',latest_pcpi),(1,'IPMAN',latest_ipm)]:
            if date in source and np.isfinite(v[j]):comparison.append({'month':e.label(date),'series':name,'frozen':float(v[j]),'official_latest':source[date],'difference':float(v[j]-source[date])})
    e.write(e.OUT/'macro_level_reconciliation.csv',comparison)
    e.MAC={d:np.array([v,latest_ipm.get(d,np.nan)]) for d,v in latest_pcpi.items()}
    real=[]
    for name in ['QQQ','SPY','RegimeRule','BoydSimple','Vol15']:
        s=e.simulate(name);row=e.real_metrics(s);row['missing_cpi_observation_skipped']=';'.join(e.label(int(d)) for d in s['dates'] if d<=e.mn('2025-12') and d not in latest_pcpi);real.append(row)
    e.MAC=frozen
    e.write(e.OUT/'official_cpi_real_metrics.csv',real)
    summary={'panels':{n:{'vintages':len(p),'first_vintage':e.label(min(p)),'last_vintage':e.label(max(p))}for n,p in panels.items()},'origins_including_next':len(e.D)-8,'common_complete_origins':len(common),'missing':failures,'price_only_fallbacks':fallbacks,'availability_rule':'Vintage month <= signal month minus one; exact publication clock not asserted. Same-vintage exact observation lags.','max_abs_cpi_difference':max(abs(x['difference']) for x in comparison if x['series']=='CPIAUCSL'),'max_abs_ipm_level_difference_not_growth':max(abs(x['difference']) for x in comparison if x['series']=='IPMAN')}
    (ROOT/'audit/macro_vintage_audit.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2));print(metrics);print(real)
if __name__=='__main__':run()
