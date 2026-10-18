"""Integrated original-corpus analysis. Run only after frozen measurement/coverage checks.
All models use chronological expanding OLS. Current macro vintages make this a retrospective
availability-buffered evaluation rather than an exact real-time deployment replication.
"""
from pathlib import Path
import json
import numpy as np,pandas as pd
from scipy.stats import norm, t as student_t
from v7_core import OLS,add_constant,multipletests,raw,outcomes
R=Path(__file__).resolve().parent;O=R/'outputs';B=['u3','pce_yoy','gdp'];H=B+['pce36','income_growth'];K=H+['dem_president','web_mode']
SPECS={'M1 Economics':B,'M2 Economics + own AI':B+['media'],'Households':H,'Full controls':K,'M3 Controls + own AI':K+['media'],'Dynamic controls':['s1']+K,'Dynamic M3':['s1']+K+['media'],'SF Fed comparator':B+['news'],'AR1':['s1'],'Last month':['s1']}
PAIRS=[('M1 Economics','M2 Economics + own AI'),('Households','Full controls'),('Full controls','M3 Controls + own AI'),('Dynamic controls','Dynamic M3'),('Last month','Dynamic M3'),('SF Fed comparator','M2 Economics + own AI')]
FIELDS=['tone_score','raw_nli_tone','dictionary_tone','prices','labor','housing','growth','debt','policy','level_frame','rate_frame','political_mention','political_blame_proxy','emotion_word']
def calendar_fit(y,x,periods,maxlags=6):
 """OLS with Bartlett HAC using actual calendar month distances and HC1 scaling."""
 fit=OLS(y,x).fit();a=np.asarray(x,float);v=np.asarray(y,float);e=v-a@fit.params.values;xe=pd.DataFrame(a*e[:,None],index=pd.DatetimeIndex(periods));full=xe.reindex(pd.date_range(xe.index.min(),xe.index.max(),freq='ME')).fillna(0).to_numpy();meat=full.T@full
 for lag in range(1,maxlags+1):
  gamma=full[lag:].T@full[:-lag];meat+=(1-lag/(maxlags+1))*(gamma+gamma.T)
 inv=np.linalg.pinv(a.T@a);rank=np.linalg.matrix_rank(a);cov=inv@meat@inv*len(a)/max(1,len(a)-rank);fit.bse=pd.Series(np.sqrt(np.maximum(0,np.diag(cov))),index=fit.params.index);stat=np.divide(fit.params.values,fit.bse.values,out=np.zeros(len(fit.params)),where=fit.bse.values>1e-12);fit.pvalues=pd.Series(2*norm.sf(abs(stat)),index=fit.params.index);return fit

def calendar_boot_indices(periods,rng,n,block=6):
 periods=pd.DatetimeIndex(periods);cal=pd.date_range(periods.min(),periods.max(),freq='ME');lookup={p:i for i,p in enumerate(periods)};ix=[]
 while len(ix)<n:
  start=int(rng.integers(0,len(cal)))
  ix.extend(lookup[cal[(start+j)%len(cal)]] for j in range(block) if cal[(start+j)%len(cal)] in lookup)
 return np.array(ix[:n])

def economic_panel():
 from build_inputs import build
 p=build();p.period=pd.to_datetime(p.period);p.origin=pd.to_datetime(p.origin);p=p[p.period>='2010-01-01'].copy();s=raw('PCEPI');v=100*(s/s.shift(36)-1)
 for i,r in p.iterrows():
  available=v.dropna()[v.dropna().index+pd.Timedelta(days=45)<=r.origin];p.loc[i,'pce36']=float(available.iloc[-1]);p.loc[i,'pce36_period']=available.index[-1];p.loc[i,'pce36_available']=available.index[-1]+pd.Timedelta(days=45)
 p['dem_president']=p.origin.between('2021-02-01','2025-01-01').astype(int);p['web_mode']=(p.origin>='2024-07-01').astype(int);p['month_sin']=np.sin(2*np.pi*p.origin.dt.month/12);p['month_cos']=np.cos(2*np.pi*p.origin.dt.month/12)
 return p

def monthly(d,local,field='tone_score',sources=None,strict=False):
 sources=sources or ['NPR',local,'Hacker News'];z=d[d.source.isin(sources)].copy()
 if strict:z=z[z.us_relevance=='explicit_US_text']
 agg=z.groupby(['month','source'])[FIELDS].mean();n=z.groupby(['month','source']).size();agg.loc[n<3,FIELDS]=np.nan;out=agg.reset_index();out['n']=n.values;out.to_csv(O/('source_month_'+('strict' if strict else 'main')+'.csv'),index=False) if field=='tone_score' and len(sources)==3 else None
 wide=agg[field].unstack('source').reindex(columns=sources);v=wide.mean(axis=1,skipna=False);v.index=pd.to_datetime(v.index)+pd.offsets.MonthEnd(0);return v

def attach_media(p,s,lag=2):
 q=p.copy();q['media_period']=q.period-pd.offsets.MonthEnd(lag);q['media']=q.media_period.map(s);q['media_available']=q.media_period+pd.Timedelta(days=7);assert (q.media_available<=q.origin).all() if lag>=2 else True
 return q

def fit_predict(tr,te,keys):
 x=tr[keys].to_numpy(float);z=te[keys].to_numpy(float);mu=x.mean(axis=0);sd=x.std(axis=0);sd[sd<1e-12]=1;x=(x-mu)/sd;z=(z-mu)/sd;x=np.c_[np.ones(len(x)),x];z=np.c_[np.ones(len(z)),z];y=tr.y.to_numpy();b=np.linalg.lstsq(x,y,rcond=None)[0];e=y-x@b;dof=max(1,len(x)-np.linalg.matrix_rank(x));sigma=float(e@e/dof);inv=np.linalg.pinv(x.T@x);pred=z@b;half=student_t.ppf(.95,dof)*np.sqrt(sigma*(1+np.einsum('ij,jk,ik->i',z,inv,z)));return pred,half

def rolling(p,specs=SPECS,warmup=36,start=None,scenario='Original balanced index',outcome='Headline'):
 p=p.sort_values('period').reset_index(drop=True);rr=[]
 if start is None:start=p.iloc[warmup].period
 for model,keys in specs.items():
  prev=[]
  for _,r in p[p.period>=start].iterrows():
   tr=p[(p.period<r.period)&(~p.preliminary)];te=pd.DataFrame([r]);assert len(tr)>=warmup and tr.period.max()<r.period
   if model=='Last month':pred=float(r.s1);h=1.645*np.std(tr.y-tr.s1,ddof=1)
   else:a,b=fit_predict(tr,te,keys);pred=float(a[0]);h=float(b[0])
   if len(prev)>=12:h=float(np.quantile(np.abs(prev[-60:]),min(1,np.ceil(.9*(len(prev[-60:])+1))/len(prev[-60:])),method='higher'))
   err=float(r.y-pred);rr.append(dict(model=model,period=r.period,actual=r.y,predicted=pred,error=err,lower90=pred-h,upper90=pred+h,n_train=len(tr),preliminary=bool(r.preliminary),scenario=scenario,outcome=outcome))
   if not r.preliminary:prev.append(err)
 return pd.DataFrame(rr)

def metrics(f):
 rr=[]
 for (sc,out,model),g in f[~f.preliminary].groupby(['scenario','outcome','model']):
  rr.append(dict(scenario=sc,outcome=out,model=model,n=len(g),first=str(g.period.min().date()),last=str(g.period.max().date()),rmse=float(np.sqrt(np.mean(g.error**2))),mae=float(np.mean(abs(g.error))),mean_error=float(g.error.mean()),coverage90=float(g.actual.between(g.lower90,g.upper90).mean())))
 return pd.DataFrame(rr)

def comparisons(f,pairs=PAIRS):
 rr=[];rng=np.random.default_rng(271828)
 for a,b in pairs:
  z=f[(f.model==a)&(~f.preliminary)].sort_values('period');v=f[(f.model==b)&(~f.preliminary)].sort_values('period');assert z.period.tolist()==v.period.tolist();ea=z.error.values;eb=v.error.values;delta=ea**2-eb**2;fit=calendar_fit(delta,np.ones((len(delta),1)),z.period,3);draw=[]
  for _ in range(2000):
   ix=calendar_boot_indices(z.period,rng,len(ea),6);draw.append(np.sqrt(np.mean(ea[ix]**2))-np.sqrt(np.mean(eb[ix]**2)))
  rr.append(dict(baseline=a,augmented=b,n=len(ea),rmse_gain=float(np.sqrt(np.mean(ea**2))-np.sqrt(np.mean(eb**2))),lower95=float(np.quantile(draw,.025)),upper95=float(np.quantile(draw,.975)),p_hac=float(fit.pvalues.iloc[0])))
 z=pd.DataFrame(rr);z['p_holm']=multipletests(z.p_hac)[1];return z

def associations(p):
 rr=[];diag=[];variants=[]
 p=p.set_index('period').reindex(pd.date_range(p.period.min(),p.period.max(),freq='ME')).rename_axis('period').reset_index()
 for tag,base in [('Levels',p),('First differences',p.assign(**{c:p[c].diff() for c in ['y']+K+['media','s1']})),('12-month changes',p.assign(**{c:p[c].diff(12) for c in ['y']+K+['media','s1']}))]:
  for name,keys in [('M2',B+['media']),('M3',K+['media']),('Dynamic M3',['s1']+K+['media'])]:
   q=base.dropna(subset=['y']+keys);x=q[keys];mu=x.mean();sd=x.std(ddof=0).replace(0,1);xx=(x-mu)/sd;fit=calendar_fit(q.y,add_constant(xx),q.period,12 if tag=='12-month changes' else 6);ph=multipletests(fit.pvalues.iloc[1:])[1]
   for j,k in enumerate(keys):
    b=float(fit.params[k]/sd[k]);se=float(fit.bse[k]/sd[k]);rr.append(dict(transformation=tag,model=name,term=k,n=len(q),coefficient=b,hac_se=se,lower95=b-1.96*se,upper95=b+1.96*se,p_hac=float(fit.pvalues[k]),p_holm=float(ph[j]),coefficient_per_sd=float(fit.params[k])))
   rank=np.linalg.matrix_rank(np.c_[np.ones(len(xx)),xx]);diag.append(dict(transformation=tag,model=name,n=len(q),rank=int(rank),n_columns=len(keys)+1,r2=float(fit.rsquared),adjusted_r2=float(1-(1-fit.rsquared)*(len(q)-1)/(len(q)-rank)),residual_calendar_lag1_corr=float(pd.Series(q.y.to_numpy()-np.c_[np.ones(len(xx)),xx]@fit.params.values,index=pd.DatetimeIndex(q.period)).reindex(pd.date_range(q.period.min(),q.period.max(),freq='ME')).autocorr(1)),condition_number=float(np.linalg.cond(np.c_[np.ones(len(xx)),xx]))))
   if tag=='Levels' and name=='M3':
    for k in keys:
     v=xx[k].values;other=np.c_[np.ones(len(xx)),xx.drop(columns=k)];res=v-other@np.linalg.lstsq(other,v,rcond=None)[0];r2=1-float(res@res)/max(float(v@v),1e-12);variants.append(dict(term=k,vif=float(1/max(1-r2,1e-12))))
 pd.DataFrame(rr).to_csv(O/'associations_hac.csv',index=False);pd.DataFrame(diag).to_csv(O/'fit_diagnostics.csv',index=False);pd.DataFrame(variants).to_csv(O/'vif.csv',index=False)
 # Expanding association stability after36 months. This is not a causal rolling effect.
 r=[]
 for end in range(36,len(p)+1):
  q=p.iloc[:end].dropna(subset=['y']+K+['media']);keys=K+['media'];xx=(q[keys]-q[keys].mean())/q[keys].std(ddof=0).replace(0,1);fit=calendar_fit(q.y,add_constant(xx),q.period,6);sd=q.media.std(ddof=0);b=fit.params.media/sd;se=fit.bse.media/sd;r.append(dict(end=str(q.period.max().date()),coefficient=b,lower95=b-1.96*se,upper95=b+1.96*se))
 pd.DataFrame(r).to_csv(O/'coefficient_stability.csv',index=False)

def run():
 d=pd.read_csv(O/'coded_corpus.csv',keep_default_na=False);coverage=pd.crosstab(d.month,d.source).reindex(pd.period_range('2019-11','2026-09',freq='M').astype(str),fill_value=0);coverage.to_csv(O/'coverage_final.csv')
 # Source selection is based only on data coverage, never financial fit.
 available=[x for x in ['CT Mirror','Colorado Sun'] if x in coverage];assert available,'Historical local source is required';local=max(available,key=lambda x:int((coverage[x]>=3).sum()));sources=['NPR',local,'Hacker News'];(O/'source_selection.json').write_text(json.dumps(dict(primary_sources=sources,local_coverage_counts={x:int((coverage[x]>=3).sum()) for x in available},rule='Choose state outlet with most observed months containing at least3 eligible independent titles, before outcome fitting'),indent=2))
 media=monthly(d,local);p=economic_panel();p.to_csv(O/'economic_availability_panel.csv',index=False);final=p[~p.preliminary];long=rolling(p,{'M1 Economics':B,'Households':H,'Dynamic economics':['s1']+B,'Dynamic households':['s1']+H,'Last month':['s1']},120,pd.Timestamp('2020-01-31'),'Long economic baseline');long.to_csv(O/'baseline_forecasts.csv',index=False);metrics(long).to_csv(O/'baseline_metrics.csv',index=False)
 q=attach_media(p,media).dropna(subset=['media']).copy();q=q[q.period<='2026-10-31'];q.to_csv(O/'integrated_panel.csv',index=False);n_final=int((~q.preliminary).sum());assert n_final>=36,'Too few complete months for specified minimum';warmup=36 if n_final>=60 else (30 if n_final>=48 else 24);f=rolling(q,warmup=warmup);f.to_csv(O/'forecasts.csv',index=False);m=metrics(f);m.to_csv(O/'metrics.csv',index=False);comparisons(f).to_csv(O/'comparison_tests.csv',index=False);associations(q[~q.preliminary])
 # Monthly same-period media versus an earlier-data economic prediction gap, descriptive.
 gap=long[(long.model=='M1 Economics')&(~long.preliminary)].copy();gap['same_month_media']=gap.period.map(media);gap['gap']=gap.error;gap.to_csv(O/'sentiment_gap.csv',index=False);g=gap.dropna(subset=['same_month_media']);rows=[]
 for lag in [0,1,2,-1,-2]:
  a=gap.copy();a['text']= (a.period-pd.offsets.MonthEnd(lag)).map(media);a=a.dropna(subset=['text']);rows.append(dict(text_lag_months=lag,n=len(a),pearson=float(a.gap.corr(a.text)),interpretation='Future-text falsification diagnostic' if lag<0 else 'Descriptive, noncausal'))
 pd.DataFrame(rows).to_csv(O/'gap_correlations.csv',index=False)
 # Sensitivities use matched dates within each variant and the primary evaluation start.
 sensitivity=[];start=f.period.min();sm={'Dynamic controls':['s1']+K,'Dynamic M3':['s1']+K+['media'],'M3 Controls + own AI':K+['media'],'Full controls':K,'Last month':['s1']}
 variants=[('Lag3 timing',media,3),('Strict US text',monthly(d,local,strict=True),2),('Raw NLI tone',monthly(d,local,field='raw_nli_tone'),2),('Dictionary tone',monthly(d,local,field='dictionary_tone'),2)]
 for src in sources:variants.append(('Without '+src,monthly(d,local,sources=[x for x in sources if x!=src]),2))
 for label,ss,lag in variants:
  z=attach_media(p,ss,lag).dropna(subset=['media']);z=z[z.period<='2026-09-30'];test_start=max(start,z.iloc[warmup].period) if len(z)>warmup else None
  if test_start is None or len(z[z.period>=test_start])<12:continue
  sensitivity.append(rolling(z,sm,warmup,test_start,label))
 seasonal={k:v+['month_sin','month_cos'] for k,v in sm.items() if k!='Last month'};sensitivity.append(rolling(q,seasonal,warmup,start,'Annual seasonality'))
 sf=pd.concat(sensitivity);sf.to_csv(O/'sensitivity_forecasts.csv',index=False);metrics(sf).to_csv(O/'sensitivity_metrics.csv',index=False)
 comps=[]
 for name,series in outcomes().items():
  if name=='Headline':continue
  z=q.copy();z['y']=z.period.map(series);z['s1']=(z.period-pd.offsets.MonthEnd(1)).map(series);z=z.dropna(subset=['y','s1']);comps.append(rolling(z,sm,warmup,start,'Secondary outcomes',name))
 cc=pd.concat(comps);cc.to_csv(O/'component_forecasts.csv',index=False);metrics(cc).to_csv(O/'component_metrics.csv',index=False)
 sub=[]
 for label,mask in [('Nov-Dec2024',f.period<'2025-01-01'),('2025-Sep2026',f.period>='2025-01-01')]:
  z=metrics(f[mask]);z['subperiod']=label;sub.append(z)
 pd.concat(sub).to_csv(O/'subperiod_metrics.csv',index=False)
 summary=dict(version=8,n_media_items=len(d),primary_sources=sources,eligible_monthly_panel=n_final,panel_start=str(q.period.min().date()),panel_end=str(q.period.max().date()),initial_train=warmup,n_forecasts=int(m.n.iloc[0]),metrics=m.to_dict('records'),baseline_metrics=metrics(long).to_dict('records'),latest_baseline=long[long.preliminary].assign(period=lambda x:x.period.astype(str)).to_dict('records'),mean_gap_2022_on=float(gap[gap.period>='2022-01-01'].gap.mean()),mean_gap_last12=float(gap.tail(12).gap.mean()),corpus='Original public title metadata; no peer corpus, labels or code',status='Exploratory, revised-history, AI-reference measurements; causal exposure unidentified')
 (O/'summary.json').write_text(json.dumps(summary,indent=2));print(m[['model','n','rmse','mae']].to_string(index=False));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
