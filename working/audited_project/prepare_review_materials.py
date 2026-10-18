from pathlib import Path
import json,hashlib,re
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent;O=R/'outputs';A=R/'audit';V=R/'validation'
d=pd.read_csv(O/'coded_corpus.csv',keep_default_na=False)
# Stratify by source and broad date era. No outcome or AI score selects rows.
d['era']=pd.cut(d.month.str[:4].astype(int),[2018,2021,2024,2026],labels=['2019-2021','2022-2024','2025-2026'])
d['human_hash']=d.record_id.map(lambda x:hashlib.sha256(('human-independent-v8-'+x).encode()).hexdigest());selected=[]
for src,g in d.groupby('source'):
 parts=[]
 for era,z in g.groupby('era',observed=True):parts.append(z.sort_values('human_hash').head(34 if era=='2019-2021' else 33))
 a=pd.concat(parts);unused=g[~g.record_id.isin(a.record_id)].sort_values('human_hash');a=pd.concat([a,unused.head(100-len(a))]).head(100);assert len(a)==100;selected.append(a)
s=pd.concat(selected).sort_values('human_hash').reset_index(drop=True);s['item_id']=['H'+str(i+1).zfill(3) for i in range(300)]
s[['item_id','record_id','source','month','era','tone_score']].to_csv(A/'human_sample_sealed_mapping.csv',index=False)
blank=s[['item_id','title']].copy()
for col in ['relevant_US','tone','emotional_wording','topics','price_frame','time_frame','political_actor','attribution','numeric_claim','factual_status','evidence','rater_id']:blank[col]=''
for r in ['A','B']:blank.to_csv(R/f'Human_Annotation_Rater_{r}.csv',index=False)
# Paired factual cases with fixed archived releases, no unverifiable prevalence denominator.
c=pd.read_csv(O/'candidate_corpus.csv').drop_duplicates('record_id').set_index('record_id');cases=[]
for rid,event,unit,status,value,release in [
('I3e37aa815902c9','2020 Q2 GDP, advance','annualized vs actual quarter','Magnitude matches annualized release; title omits annualization','-32.9% annualized = -9.4934% quarterly','https://www.bea.gov/news/2020/gross-domestic-product-2nd-quarter-2020-advance-estimate-and-annual-update'),
('I82903766570ef0','2020 Q2 GDP, advance','actual quarter','Consistent after rate conversion, rounded','-9.5% actual quarter','https://www.bea.gov/news/2020/gross-domestic-product-2nd-quarter-2020-advance-estimate-and-annual-update'),
('Ic110fc47fc9ea8','October 2023 CPI, release 2023-11-14','12-month NSA vs monthly SA','3.2% matches annual CPI; monthly SA was 0.0%','3.2% year over year','https://www.bls.gov/news.release/archives/cpi_11142023.htm'),
('Id293496dc73bcc','May 2020 jobs, release 2020-06-05','payroll change and unemployment rate','Two numeric clauses match original release','+2.5 million payrolls; 13.3% U3','https://www.bls.gov/news.release/archives/empsit_06052020.htm')]:
 row=c.loc[rid];cases.append(dict(record_id=rid,title=row.title,source=row.source,url=row.url,date=row.date,event=event,unit=unit,assessment=status,official_value=value,official_release=release,scope='Purposive title-only case; body/exposure/whole-corpus accuracy not established'))
pd.DataFrame(cases).to_csv(O/'matched_release_cases.csv',index=False)
# Same-assistant illustrative counterfactual review: not blinded and not an accuracy estimate.
z=d[d.title.str.contains(r'\b(?:Trump|Biden)\b',regex=True)].sort_values('record_id').head(8)
labels=[-1,0,1,0,0,0,0,0];rows=[]
for (_,r),label in zip(z.iterrows(),labels):
 swapped=re.sub(r'\bTrump\b','ZZZ',r.title);swapped=re.sub(r'\bBiden\b','Trump',swapped).replace('ZZZ','Biden')
 for variant,t in [('original',r.title),('name_swap',swapped),('source_NPR','NPR: '+r.title),('source_Fox','Fox News: '+r.title),('source_MSNBC','MSNBC: '+r.title)]:rows.append(dict(record_id=r.record_id,variant=variant,title=t,assistant_review_label=label,scope='Illustrative same-assistant audit with original labels visible; no independence, blinding, accuracy or invariance guarantee'))
pd.DataFrame(rows).to_csv(O/'primary_counterfactual_review.csv',index=False)
# Small-sample influence and long-baseline explanatory fit, explicitly descriptive.
p=pd.read_csv(O/'economic_availability_panel.csv');p=p[~p.preliminary];x=np.c_[np.ones(len(p)),p[['u3','pce_yoy','gdp']]];y=p.y.values;e=y-x@np.linalg.lstsq(x,y,rcond=None)[0];r2=1-e@e/np.sum((y-y.mean())**2)
infl=pd.read_csv(O/'influence_audit.csv');summary=dict(long_n=len(p),long_r2=r2,long_adjusted_r2=1-(1-r2)*(len(p)-1)/(len(p)-4),leave_one_month_out_media_coefficient_range=[float(infl.media_coefficient_without_month.min()),float(infl.media_coefficient_without_month.max())],max_cook_month=infl.sort_values('cook').iloc[-1].period,matched_release_cases=len(cases),human_ratings_completed=0)
(V/'additional_audit.json').write_text(json.dumps(summary,indent=2));print(summary)
