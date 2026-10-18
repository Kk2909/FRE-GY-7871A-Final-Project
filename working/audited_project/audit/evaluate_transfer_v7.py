import os
os.environ['ORT_DISABLE_TELEMETRY']='1'
import json,re
import pandas as pd,numpy as np
from sklearn.metrics import classification_report,accuracy_score,f1_score,cohen_kappa_score
from score_corpus_v7 import calibrator,operational,PC
from nlp_measure_v7 import Coder,R
O=R/'outputs_v7'
def run():
 d=pd.read_csv(O/'new_ai_reference_300.csv',keep_default_na=False);cached=pd.read_csv(O/'semantic_features.csv');a=d[['record_id','title']].merge(cached,on='record_id',how='left');missing=a[PC].isna().any(axis=1);c=Coder()
 for start in range(0,int(missing.sum()),16):
  ix=a.index[missing][start:start+16];a.loc[ix,PC]=c.probabilities(a.loc[ix,'title'].tolist());print('Transfer coding',start+16,flush=True)
 a.to_csv(O/'new_reference_semantic_features.csv',index=False);m=calibrator();x=a[PC].astype(float);pr=m.predict_proba(x,d.title);d['hybrid_prediction']=m.classes_[pr.argmax(axis=1)];d['semantic_prediction']=m.rf.predict(x);d['lexical_prediction']=m.text.predict(d.title);d['hybrid_tone_score']=pr[:,2]-pr[:,0];d['dictionary_prediction']=operational(d[['title']].copy()).dictionary_tone
 d.to_csv(O/'transfer_audit_predictions.csv',index=False);reports={};rows=[]
 for model in ['hybrid','semantic','lexical','dictionary']:
  pred=d[model+'_prediction'];reports[model]=classification_report(d.reference_tone,pred,output_dict=True,zero_division=0);reports[model]['kappa']=cohen_kappa_score(d.reference_tone,pred)
  for source,g in d.groupby('source'):
   rows.append(dict(model=model,source=source,n=len(g),accuracy=accuracy_score(g.reference_tone,g[model+'_prediction']),macro_f1=f1_score(g.reference_tone,g[model+'_prediction'],average='macro',labels=[-1,0,1],zero_division=0)))
 pd.DataFrame(rows).to_csv(O/'transfer_source_metrics.csv',index=False);rng=np.random.default_rng(1415);groups=d.title.str.lower().str.replace(r'\W+','',regex=True);unique=groups.unique();draw=[]
 for _ in range(1000):
  selected=rng.choice(unique,len(unique),replace=True);ix=np.concatenate([np.flatnonzero(groups.values==g) for g in selected]);draw.append(f1_score(d.reference_tone.iloc[ix],d.hybrid_prediction.iloc[ix],average='macro',labels=[-1,0,1],zero_division=0))
 reports['hybrid']['macro_f1_cluster_bootstrap95']=[float(np.quantile(draw,.025)),float(np.quantile(draw,.975))];reports['n_reference_relevant']=int(d.reference_relevant.sum());reports['n_reference_total']=len(d);reports['new_labels_used_to_train']=0;reports['interpretation']='AI-reference agreement only. Three-source/era-balanced evaluation, not independent human accuracy.'
 (O/'transfer_validation.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports,indent=2))
 # Re-score saved counterfactual features with the frozen hybrid, without recomputing the language model.
 z=pd.read_csv(O/'measurement_counterfactual_results.csv');prob=m.predict_proba(z[PC],z.title);z['predicted_tone']=m.classes_[prob.argmax(axis=1)];z['tone_score']=prob[:,2]-prob[:,0];z.to_csv(O/'measurement_counterfactual_results.csv',index=False);s={}
 for kind in ['direction_foil','neutral_foil']:
  v=z[z.test==kind];s[kind]=dict(n=len(v),agreement=float((v.expected_tone==v.predicted_tone).mean()))
 for kind in ['name_swap','source_prefix']:
  v=z[z.test==kind];g=v.groupby('pair');s[kind]=dict(n_pairs=g.ngroups,label_flip_pairs=int((g.predicted_tone.nunique()>1).sum()),mean_score_range=float((g.tone_score.max()-g.tone_score.min()).mean()),max_score_range=float((g.tone_score.max()-g.tone_score.min()).max()))
 (O/'measurement_tests_summary.json').write_text(json.dumps(s,indent=2))
if __name__=='__main__':run()
