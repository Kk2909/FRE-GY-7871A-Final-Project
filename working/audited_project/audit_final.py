"""Independent raw-unit checks. Fails if persisted outputs disagree with raw sources."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from scipy.linalg import lstsq
from scipy.stats import norm
from sklearn.metrics import classification_report,cohen_kappa_score
from v7_core import raw,outcomes
R=Path(__file__).resolve().parent;O=R/'outputs';V=R/'validation'
p=pd.read_csv(O/'economic_availability_panel.csv',parse_dates=['period','origin']);d=pd.read_csv(O/'coded_corpus.csv');q=pd.read_csv(O/'integrated_panel.csv',parse_dates=['period']);q=q[~q.preliminary]
checks={};max_input=0
# Recompute all required transforms using the raw calendar grids.
values={'u3':raw('UNRATE'),'pce_yoy':100*(raw('PCEPI')/raw('PCEPI').shift(12)-1),'gdp':raw('A191RL1Q225SBEA',True),'income_growth':100*(raw('DSPIC96')/raw('DSPIC96').shift(12)-1),'pce36':100*(raw('PCEPI')/raw('PCEPI').shift(36)-1)}
for k,s in values.items():
 expected=pd.to_datetime(p[k+'_period']).map(s);err=float(np.max(abs(expected-p[k])));assert err<1e-10,(k,err);max_input=max(max_input,err)
 assert (pd.to_datetime(p[k+'_available'])<=p.origin).all()
checks['raw_formula_max_absolute_error']=max_input
for k in ['s1','y']:
 expect=(p.period-pd.offsets.MonthEnd(1) if k=='s1' else p.period).map(outcomes()['Headline']);assert np.allclose(expect,p[k])
checks['workbook_outcome_and_calendar_lag']='pass'
# Match coded titles to retrieved public metadata, and recompute source-balanced index.
cand=pd.read_csv(O/'candidate_corpus.csv').set_index('record_id');assert set(d.record_id)<=set(cand.index)
assert d.title.equals(d.record_id.map(cand.title).rename('title'))
assert d.record_id.nunique()==len(d)==670
assert d.tone_score.isin([-1,0,1]).all()
w=d.groupby(['month','source']).tone_score.mean().unstack();n=d.groupby(['month','source']).size().unstack();assert (n>=3).all().all();s=w[['NPR','Colorado Sun','Hacker News']].mean(axis=1);s.index=pd.to_datetime(s.index)+pd.offsets.MonthEnd(0)
expected=(q.period-pd.offsets.MonthEnd(2)).map(s);assert np.allclose(expected,q.media)
checks['titles_traceable_to_metadata']=len(d);checks['balanced_media_months']=len(s);checks['complete_media_targets']=len(q)
# Reproduce every rolling prediction using a separate raw-unit LAPACK solver.
from analyze_integrated_v7 import SPECS,K,B
worst=0
for filename,panel in [('forecasts.csv',q),('baseline_forecasts.csv',p[~p.preliminary])]:
 f=pd.read_csv(O/filename,parse_dates=['period']);f=f[~f.preliminary]
 for _,row in f.iterrows():
  keys=SPECS.get(row.model)
  if row.model=='Dynamic economics':keys=['s1']+B
  if row.model=='Dynamic households':keys=['s1']+B+['pce36','income_growth']
  tr=panel[panel.period<row.period];te=panel[panel.period==row.period];assert len(te)==1
  if row.model=='Last month':pred=float(te.s1.iloc[0])
  else:
   x=np.c_[np.ones(len(tr)),tr[keys].values];b=lstsq(x,tr.y.values,lapack_driver='gelsy')[0];pred=float(np.r_[1.,te[keys].values[0]]@b)
  err=abs(pred-row.predicted);worst=max(worst,err);assert err<1e-7,(filename,row.model,row.period,err)
 for name,g in f.groupby('model'):
  scored=pd.read_csv(O/('metrics.csv' if filename=='forecasts.csv' else 'baseline_metrics.csv'));m=scored[scored.model==name].iloc[0];assert abs(np.sqrt(np.mean((g.actual-g.predicted)**2))-m.rmse)<1e-10
checks['all_predictions_max_absolute_error']=worst
# Independent raw-unit calendar HAC using pairwise date distances, not compressed rows.
a=pd.read_csv(O/'associations_hac.csv');errors=[]
calendar=q.set_index('period').reindex(pd.date_range(q.period.min(),q.period.max(),freq='ME')).rename_axis('period').reset_index()
for tag,base in [('Levels',calendar),('First differences',calendar.assign(**{k:calendar[k].diff() for k in ['y']+K+['media','s1']})),('12-month changes',calendar.assign(**{k:calendar[k].diff(12) for k in ['y']+K+['media','s1']}))]:
 for name,keys in [('M2',B+['media']),('M3',K+['media']),('Dynamic M3',['s1']+K+['media'])]:
  z=base.dropna(subset=['y']+keys);x=np.c_[np.ones(len(z)),z[keys].values];y=z.y.values;b=lstsq(x,y,lapack_driver='gelsy')[0];res=y-x@b;bread=np.linalg.pinv(x);inv=bread@bread.T;meat=np.zeros((x.shape[1],x.shape[1]));dates=z.period.dt.year*12+z.period.dt.month;band=12 if tag=='12-month changes' else 6
  for i in range(len(z)):
   for j in range(len(z)):
    lag=abs(int(dates.iloc[i]-dates.iloc[j]));weight=1-lag/(band+1) if lag<=band else 0
    if weight:meat+=weight*res[i]*res[j]*np.outer(x[i],x[j])
  cov=inv@meat@inv*len(z)/(len(z)-np.linalg.matrix_rank(x));se=np.sqrt(np.maximum(0,np.diag(cov)))
  for i,k in enumerate(keys,1):
   row=a[(a.transformation==tag)&(a.model==name)&(a.term==k)].iloc[0];assert abs(row.coefficient-b[i])<1e-7;assert abs(row.hac_se-se[i])<1e-6;errors.append(abs(row.hac_se-se[i]))
checks['independent_HAC_coefficient_checks']=len(errors);checks['HAC_max_absolute_se_error']=max(errors)
# Additional model diagnostics. Full levels, direct raw units.
rows=[];influence=[]
for name,keys in [('M1',B),('M2',B+['media']),('Controls',K),('M3',K+['media']),('Dynamic M3',['s1']+K+['media'])]:
 x=np.c_[np.ones(len(q)),q[keys].values];y=q.y.values;pinv=np.linalg.pinv(x);b=pinv@y;e=y-x@b;h=np.sum(x*pinv.T,axis=1);rank=np.linalg.matrix_rank(x);mse=e@e/(len(q)-rank);cook=e**2/(rank*mse)*h/np.maximum((1-h)**2,1e-12)
 rows.append(dict(model=name,n=len(q),predictors=len(keys),parameters=len(keys)+1,rank=rank,r2=1-e@e/np.sum((y-y.mean())**2),adjusted_r2=1-(e@e/(len(q)-rank))/np.var(y,ddof=1),max_leverage=max(h),max_cooks_distance=max(cook)))
 if name=='M3':
  for i in range(len(q)):
   keep=np.arange(len(q))!=i;bb=lstsq(x[keep],y[keep],lapack_driver='gelsy')[0];influence.append(dict(period=str(q.period.iloc[i].date()),cook=float(cook[i]),leverage=float(h[i]),media_coefficient_without_month=float(bb[-1])))
pd.DataFrame(rows).to_csv(O/'model_parameter_audit.csv',index=False);pd.DataFrame(influence).to_csv(O/'influence_audit.csv',index=False)
# Confirm same evaluation dates, explicit gaps, preliminary exclusion.
f=pd.read_csv(O/'forecasts.csv',parse_dates=['period']);ff=f[~f.preliminary];g=ff.groupby('model');assert g.period.apply(list).apply(tuple).nunique()==1
checks['forecast_dates']=sorted(ff.period.dt.strftime('%Y-%m').unique().tolist());checks['forecast_n']=int(g.size().iloc[0]);checks['preliminary_scored']=0
# Label diagnostics are AI-reference only.
audit=pd.read_csv(O/'Direct_AI_Coding_Audit.csv');v=audit.dropna(subset=['pass_B_tone']);checks['same_session_AI_agreement']=float(np.mean(v.pass_A_tone==v.pass_B_tone));checks['same_session_AI_kappa']=float(cohen_kappa_score(v.pass_A_tone,v.pass_B_tone))
checks['missing_UNRATE_months']=raw('UNRATE')[raw('UNRATE').isna()].index.strftime('%Y-%m').tolist()
checks['status']='PASS numerical audit. Human validation and exact vintage reconstruction remain incomplete.'
(V/'numerical_audit.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
# Content hashes make raw snapshots, labels and outputs auditable.
files=[]
for folder in ['data','outputs','audit']:
 for file in sorted((R/folder).rglob('*')):
  if file.is_file():files.append(dict(path=str(file.relative_to(R)),bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
pd.DataFrame(files).to_csv(V/'manifest.csv',index=False)
