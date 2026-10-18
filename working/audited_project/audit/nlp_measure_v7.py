"""Frozen semantic entailment coding. Model scores are measurements, not factual truth."""
from pathlib import Path
import sys,json,time,hashlib,os
os.environ["ORT_DISABLE_TELEMETRY"]="1"
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'work/v7_deps'))
import onnxruntime as ort
ort.disable_telemetry_events()
import numpy as np,pandas as pd
from tokenizers import Tokenizer
HYP=json.loads((R/'CODING_HYPOTHESES_V7.json').read_text());KEYS=list(HYP)
class Coder:
 def __init__(self):
  d=R.parent/'work/models/nli';self.tokenizer=Tokenizer.from_file(str(d/'tokenizer.json'));self.tokenizer.enable_truncation(max_length=128);self.tokenizer.enable_padding(pad_id=0,pad_token='[PAD]');opt=ort.SessionOptions();opt.intra_op_num_threads=2;opt.inter_op_num_threads=1;self.session=ort.InferenceSession(str(d/'model_quantized.onnx'),sess_options=opt,providers=['CPUExecutionProvider']);self.inputs=[v.name for v in self.session.get_inputs()]
 def probabilities(self,texts,keys=KEYS):
  pairs=[(t,HYP[k]) for t in texts for k in keys];out=[]
  for st in range(0,len(pairs),48):
   z=self.tokenizer.encode_batch(pairs[st:st+48]);x={'input_ids':np.array([a.ids for a in z],np.int64),'attention_mask':np.array([a.attention_mask for a in z],np.int64),'token_type_ids':np.array([a.type_ids for a in z],np.int64)};v=self.session.run(None,{k:x[k] for k in self.inputs})[0];pr=np.exp(v-v.max(axis=1,keepdims=True));pr/=pr.sum(axis=1,keepdims=True);out.extend(pr[:,1].tolist())
  return np.array(out).reshape(len(texts),len(keys))
 def labels(self,prob,keys=KEYS):
  d=pd.DataFrame(prob,columns=['p_'+k for k in keys]);p=d.p_tone_positive;n=d.p_tone_negative;d['tone_score']=p-n;d['tone_label']=np.where((p>=.5)&(n<.5),1,np.where((n>=.5)&(p<.5),-1,0));d['tone_conflict']=(p>=.5)&(n>=.5)
  if 'topic_prices' in keys:
   kk=['prices','labor','housing','growth','debt','policy'];a=d[['p_topic_'+k for k in kk]].to_numpy();d['topic_label']=np.where(a.max(axis=1)>=.5,np.array(['P','L','H','G','D','M'])[a.argmax(axis=1)],'O')
   kk=['level','rate','household','national','forecast'];a=d[['p_frame_'+k for k in kk]].to_numpy();d['frame_label']=np.where(a.max(axis=1)>=.5,np.array(['V','R','E','A','F'])[a.argmax(axis=1)],'O');d.loc[(d.p_frame_level>=.5)&(d.p_frame_rate>=.5),'frame_label']='B'
   d['political_label']=np.where(d.p_political_blame>=.5,'BL',np.where(d.p_political_credit>=.5,'CR','N'));d['emotion_label']=(d.p_emotional>=.5).astype(int)
  return d
if __name__=='__main__':
 from sklearn.metrics import classification_report,cohen_kappa_score,f1_score
 p=pd.read_csv(R/'outputs_v3/AI_Validation_300_Items.csv',keep_default_na=False);coder=Coder();all=[]
 for st in range(0,len(p),24):
  all.append(coder.labels(coder.probabilities(p.text.iloc[st:st+24].tolist())));print('Legacy audit',st+24,flush=True)
 z=pd.concat(all,ignore_index=True);d=pd.concat([p.reset_index(drop=True),z],axis=1);d.to_csv(R/'outputs_v7/legacy_nli_audit.csv',index=False)
 for field,a,b in [('tone','reviewed_tone','tone_label'),('topic','reviewed_topic','topic_label'),('frame','reviewed_frame','frame_label'),('emotion','reviewed_emotion','emotion_label')]:
  y=d[a].astype(int) if field in ['tone','emotion'] else d[a];pred=d[b];print(field,classification_report(y,pred,zero_division=0,digits=3),flush=True)
