from pathlib import Path
import pandas as pd,hashlib,re
R=Path(__file__).resolve().parent;O=R/'outputs_v7'
d=pd.read_csv(O/'corpus.csv',keep_default_na=False);old=pd.read_csv(R/'outputs_v3/AI_Validation_300_Items.csv',keep_default_na=False);norm=lambda t:re.sub(r'\W+','',t.lower());exclude=set(old.text.map(norm));d=d[~d.title.map(norm).isin(exclude)].copy();d['era']=pd.cut(d.month.str[:4].astype(int),[2018,2021,2024,2026],labels=['early','middle','recent']);d['audit_hash']=d.record_id.map(lambda t:hashlib.sha256(('new-reference-v7-'+t).encode()).hexdigest());parts=[]
for source in ['NPR','Colorado Sun','Hacker News']:
 for era,n in [('early',34),('middle',33),('recent',33)]:
  z=d[(d.source==source)&(d.era==era)].sort_values('audit_hash').head(n).copy();assert len(z)==n,(source,era,len(z));parts.append(z)
z=pd.concat(parts).sort_values('audit_hash').reset_index(drop=True);z['audit_id']=['N'+str(i+1).zfill(3) for i in range(len(z))];z['split']=None
for (s,e),ix in z.groupby(['source','era'],observed=True).groups.items():
 for j,i in enumerate(ix):z.loc[i,'split']='training_extension' if j%2==0 else 'heldout_transfer'
z.to_csv(O/'new_reference_mapping.csv',index=False);z[['audit_id','title']].to_csv(O/'new_reference_blind.csv',index=False)
for start in [0,100,200]:
 print('\nBATCH',start+1)
 for _,r in z.iloc[start:start+100].iterrows():print(r.audit_id+' '+r.title)
