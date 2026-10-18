"""Usage: python evaluate_human_annotations.py RaterA.csv RaterB.csv Adjudicated.csv
Never inserts inferred/hypothetical human ratings. Run only after actual independent completion.
"""
import sys,json
from pathlib import Path
import pandas as pd
from sklearn.metrics import cohen_kappa_score,classification_report
R=Path(__file__).resolve().parent
if len(sys.argv)!=4:raise SystemExit('Supply two completed independent files and an adjudicated file with item_id and tone.')
a,b,j=[pd.read_csv(x,keep_default_na=False) for x in sys.argv[1:]]
for z in [a,b,j]:
 assert z.item_id.nunique()==len(z)==300,'Exactly 300 unique item IDs required'
 z['tone']=pd.to_numeric(z.tone,errors='raise');assert z.tone.isin([-1,0,1]).all(),'All tone labels must be -1/0/+1'
for z in [a,b]:assert z.rater_id.nunique()==1 and bool(z.rater_id.iloc[0].strip()),'Record a real rater ID'
assert a.rater_id.iloc[0]!=b.rater_id.iloc[0],'Two independent human raters required'
m=pd.read_csv(R/'audit/human_sample_sealed_mapping.csv');z=m.merge(a[['item_id','tone']],on='item_id',validate='one_to_one').rename(columns={'tone':'raterA'}).merge(b[['item_id','tone']],on='item_id',validate='one_to_one').rename(columns={'tone':'raterB'}).merge(j[['item_id','tone']],on='item_id',validate='one_to_one').rename(columns={'tone':'adjudicated'})
report=dict(n=len(z),agreement=float((z.raterA==z.raterB).mean()),kappa=float(cohen_kappa_score(z.raterA,z.raterB)),AI_against_adjudicated=classification_report(z.adjudicated,z.tone_score,output_dict=True,zero_division=0),by_source={src:classification_report(g.adjudicated,g.tone_score,output_dict=True,zero_division=0) for src,g in z.groupby('source')},note='Identity fields cannot prove independence. Document independent labeling and adjudication procedure.')
(R/'validation/human_validation_completed.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
