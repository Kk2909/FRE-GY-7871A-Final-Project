"""Freeze direct assistant tone coding and documented second-pass adjudication before regressions."""
import os
os.environ['ORT_DISABLE_TELEMETRY']='1'
from pathlib import Path
import json,re
import pandas as pd,numpy as np
from sklearn.metrics import cohen_kappa_score
from score_corpus_v7 import operational
R=Path(__file__).resolve().parent;O=R/'outputs_v7'
B=[[-1,-1,-1,-1,0,1,0,0,0,1],[1,1,1,-1,-1,-1,0,1,-1,0],[0,0,0,-1,0,-1,0,-1,-1,0],[1,0,0,0,0,0,0,-1,-1,-1],[0,-1,-1,0,-1,0,-1,0,-1,0],[-1,1,-1,-1,-1,0,-1,1,0,-1],[-1,0,-1,-1,0,-1,-1,0,-1,-1],[-1,-1,0,1,-1,1,1,0,1,0],[0,0,-1,0,0,-1,0,1,-1,1],[0,1,-1,0,1,0,1,-1,-1,1],[0,-1,1,-1,-1,0,1,0,-1,0],[0,1,1,0,0,-1,0,-1,-1,-1],[0,0,-1,0,-1,-1,-1,0,0,0],[1,0,-1,-1,-1,-1,-1,-1,0,0],[-1,1,0,-1,0,0,1,0,0,0]]
def run():
 d=pd.read_csv(O/'direct_ai_pass_A.csv',keep_default_na=False);d.reference_relevant=d.reference_relevant.astype(str).str.lower().eq('true');b=pd.read_csv(O/'primary_second_mapping.csv',keep_default_na=False);y=sum(B,[]);assert len(y)==len(b)==150;b['pass_B_tone']=y;b.to_csv(O/'primary_second_pass.csv',index=False);d=d.merge(b[['record_id','review_id','pass_B_tone']],on='record_id',how='left',validate='one_to_one');d['adjudication']='First pass retained; not in second-pass sample.'
 for i,r in d[d.pass_B_tone.notna()].iterrows():
  same=int(r.pass_A_tone)==int(r.pass_B_tone);d.loc[i,'adjudication']='Both passes agree.' if same else 'Pre-fit review adopts second pass: a policy-only statement, unspecified distributional effects or a transparency tool does not itself assert improving/worsening household conditions.'
  d.loc[i,'reviewed_tone']=int(r.pass_B_tone)
 changes=json.load(open(R/'data/direct_ai_primary_labels_v7.json'))['pre_fit_policy_review']
 for k,v in changes.items():d.loc[d.coding_id=='A'+str(k).zfill(3),['reviewed_tone','adjudication']]=[v,'Pre-fit uniform policy review: bare changes/proposals without stated economic effects are neutral.']
 d['tone_score']=d.reviewed_tone.astype(int);d['tone_label']=d.tone_score;d['measurement']='Direct assistant title coding; exact model snapshot/temperature unavailable; frozen labels are authoritative';d=operational(d)
 cache=pd.read_csv(O/'semantic_features.csv');d=d.merge(cache[['record_id','p_tone_positive','p_tone_negative']],on='record_id',how='left',validate='one_to_one');d['raw_nli_tone']=d.p_tone_positive-d.p_tone_negative
 # The direct AI source and sampling frame are now frozen. Ineligible records remain in the audit file.
 d.to_csv(O/'Direct_AI_Coding_Audit.csv',index=False);d[d.reference_relevant].to_csv(O/'coded_corpus.csv',index=False)
 v=d[d.pass_B_tone.notna()];agreement=float((v.pass_A_tone==v.pass_B_tone).mean());kappa=float(cohen_kappa_score(v.pass_A_tone,v.pass_B_tone));rng=np.random.default_rng(20261017);groups=v.normalized_title.unique();draw=[]
 for _ in range(1000):
  selected=rng.choice(groups,len(groups),replace=True);ix=np.concatenate([np.flatnonzero(v.normalized_title.values==g) for g in selected]);draw.append(cohen_kappa_score(v.pass_A_tone.iloc[ix],v.pass_B_tone.iloc[ix]))
 summary=dict(n_primary_selected=len(d),n_relevant=int(d.reference_relevant.sum()),n_excluded=int((~d.reference_relevant).sum()),by_source=d[d.reference_relevant].source.value_counts().to_dict(),n_second_pass=len(v),agreement=agreement,kappa=kappa,kappa_cluster_ci95=[float(np.quantile(draw,.025)),float(np.quantile(draw,.975))],n_disagreements=int((v.pass_A_tone!=v.pass_B_tone).sum()),n_uniform_policy_reviews=len(changes),n_missing_raw_nli=int(d[d.reference_relevant].raw_nli_tone.isna().sum()),interpretation='Same-session AI consistency, not independent human accuracy. Review carryover and common model errors can inflate agreement. No financial outcome inspected before finalization.')
 (O/'direct_ai_review_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(v[v.pass_A_tone!=v.pass_B_tone][['coding_id','title','pass_A_tone','pass_B_tone']].to_string(index=False))
if __name__=='__main__':run()
