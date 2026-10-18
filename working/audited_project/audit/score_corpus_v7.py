"""Original text measurements. Outcome-free semantic calibration and explicit keyword proxies."""
import os
os.environ['ORT_DISABLE_TELEMETRY']='1'
from pathlib import Path
import json,time,re,hashlib
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold,cross_val_predict
from sklearn.metrics import classification_report,cohen_kappa_score
from nlp_measure_v7 import Coder,KEYS,R
from collect_integrated_v7 import assemble
O=R/'outputs_v7';CACHE=O/'semantic_features.csv';PC=['p_'+k for k in KEYS]
class HybridToneModel:
 def __init__(self):
  from sklearn.pipeline import make_pipeline,FeatureUnion
  from sklearn.feature_extraction.text import TfidfVectorizer
  from sklearn.linear_model import LogisticRegression
  self.rf=RandomForestClassifier(n_estimators=200,max_depth=3,min_samples_leaf=10,class_weight='balanced',random_state=7)
  self.text=make_pipeline(FeatureUnion([('word',TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True)),('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,sublinear_tf=True))]),LogisticRegression(C=1,class_weight='balanced',max_iter=1500));self.classes_=np.array([-1,0,1])
 def fit(self,x,text,y):self.rf.fit(x,y);self.text.fit(text,y);return self
 def predict_proba(self,x,text):return .5*self.rf.predict_proba(x)+.5*self.text.predict_proba(text)
def calibrator():
 d=pd.read_csv(O/'legacy_nli_audit.csv',keep_default_na=False);x=d[PC].astype(float);y=d.reviewed_tone.astype(int);g=d.content_cluster.astype(str)
 cv=StratifiedGroupKFold(5,shuffle=True,random_state=2718);pr=np.zeros((len(d),3))
 for a,b in cv.split(d,y,g):
  m=HybridToneModel().fit(x.iloc[a],d.text.iloc[a],y.iloc[a]);pr[b]=m.predict_proba(x.iloc[b],d.text.iloc[b])
 pred=np.array([-1,0,1])[pr.argmax(axis=1)];z=pd.DataFrame(dict(record_id=d.record_id,content_cluster=g,reference=y,prediction=pred,p_negative=pr[:,0],p_neutral=pr[:,1],p_positive=pr[:,2]));z.to_csv(O/'calibration_oof.csv',index=False)
 diag=classification_report(y,pred,output_dict=True,zero_division=0);diag['kappa']=cohen_kappa_score(y,pred);diag['method']='Equal-weight semantic RF and word/character TF-IDF logistic regression; grouped folds by277 content clusters; trained only on original300 AI references';(O/'calibration_diagnostics.json').write_text(json.dumps(diag,indent=2));return HybridToneModel().fit(x,d.text,y)

PATTERNS={
 'prices':r'\b(inflation|prices?|cost of living|grocer\w*|gasoline|food costs?)\b',
 'labor':r'\b(jobs?|wages?|employment|unemployment|jobless|hiring|layoffs?|laid off|payrolls?|labor|labour)\b',
 'housing':r'\b(hous\w*|homes?|rents?|mortgages?|evictions?)\b',
 'growth':r'\b(gdp|econom\w*|recession|growth|consumer spending|retail sales)\b',
 'debt':r'\b(debt|credit cards?|loan payments?|delinquen\w*)\b',
 'policy':r'\b(tariffs?|tax\w*|federal reserve|interest rates?|(?-i:Fed)|government spending)\b',
 'level_frame':r'\b(high prices?|higher prices?|high costs?|higher costs?|cost of living|afford\w*|expensive|price levels?|record prices?|still high|remain\w* high|elevated prices?)\b',
 'rate_frame':r'\b(inflation|disinflation|deflation|prices? (?:rise|rose|rising|fall|fell|falling|increase|decrease|drop|climb)|price (?:growth|increases?|declines?))\b',
 'political_mention':r'\b(Trump|Biden|Democrat\w*|Republican\w*|White House|president\w*|Congress)\b',
 'blame_word':r'\b(blam\w*|fault|caus\w*|responsib\w*|hurt\w*|fail\w*|damage\w*)\b',
 'emotion_word':r'\b(crisis|panic|fear\w*|terrify\w*|disaster\w*|nightmare|pain\w*|anger|angry|outrag\w*|soar\w*|skyrocket\w*|plung\w*|crash\w*|suffer\w*|struggl\w*)\b'}
def operational(d):
 for k,v in PATTERNS.items():d[k]=d.title.str.contains(v,case=False,regex=True).astype(int)
 d['political_blame_proxy']=d.political_mention*d.blame_word
 d['dictionary_tone']=d.title.str.count(r'(?i)\b(improv\w*|recover\w*|rebound\w*|booming|gains?|strong|cool\w*|eas\w*)\b')-d.title.str.count(r'(?i)\b(recession|layoffs?|crisis|struggl\w*|surge\w*|soar\w*|skyrocket\w*|slump\w*|plung\w*|weak\w*|declin\w*)\b')
 d['dictionary_tone']=np.sign(d.dictionary_tone);return d
if __name__=='__main__':
 model=calibrator();coder=Coder();seen=pd.read_csv(CACHE) if CACHE.exists() else pd.DataFrame(columns=['record_id']+PC)
 while True:
  assemble();d=pd.read_csv(O/'corpus.csv',keep_default_na=False);d=d[d.source.isin(['NPR','Colorado Sun','CT Mirror','Hacker News'])].copy();todo=d[~d.record_id.isin(seen.record_id)]
  for st in range(0,len(todo),16):
   part=todo.iloc[st:st+16];a=coder.probabilities(part.title.tolist());z=pd.DataFrame(a,columns=PC);z.insert(0,'record_id',part.record_id.values);seen=pd.concat([seen,z],ignore_index=True);seen.to_csv(CACHE.with_suffix('.tmp'),index=False);CACHE.with_suffix('.tmp').replace(CACHE);print('Scored',len(seen),'titles',flush=True)
  z=d.merge(seen,on='record_id',validate='one_to_one');pr=model.predict_proba(z[PC].astype(float),z.title);z['tone_score']=pr[:,2]-pr[:,0];z['tone_label']=model.classes_[pr.argmax(axis=1)];z['p_negative']=pr[:,0];z['p_neutral']=pr[:,1];z['p_positive']=pr[:,2];z['raw_nli_tone']=z.p_tone_positive-z.p_tone_negative;z=operational(z);z.to_csv(O/'automated_coded_corpus.csv',index=False)
  if (O/'collection_complete.flag').exists():break
  print('Waiting for additional archive windows',flush=True);time.sleep(20)
 print('All available original records coded.',flush=True)
