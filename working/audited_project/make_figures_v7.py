from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;O=R/'outputs';plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#263b4c','text.color':'#263b4c'})
COL=['#008577','#b76335','#334e69','#8095a3']
def save(name):plt.tight_layout();plt.savefig(O/name,dpi=190,bbox_inches='tight');plt.close()
def run():
 s=json.loads((O/'summary.json').read_text());d=pd.read_csv(O/'coded_corpus.csv',keep_default_na=False);sources=s['primary_sources'];rng=np.random.default_rng(2701);rr=[]
 for month in pd.period_range('2019-11','2026-09',freq='M').astype(str):
  row=dict(month=month);a=[]
  for src in sources:
   z=d[(d.month==month)&(d.source==src)];row['n_'+src.replace(' ','_')]=len(z)
   if len(z)>=3:a.append(z.tone_score.to_numpy())
  row['valid_balanced']=len(a)==len(sources)
  if row['valid_balanced']:
   row['tone_score']=float(np.mean([x.mean() for x in a]));draw=np.mean([rng.choice(x,(1000,len(x)),replace=True).mean(axis=1) for x in a],axis=0);row['lower95']=float(np.quantile(draw,.025));row['upper95']=float(np.quantile(draw,.975))
   for field in ['raw_nli_tone','dictionary_tone','prices','labor','housing','growth','debt','policy','level_frame','rate_frame','political_mention','political_blame_proxy','emotion_word']:
    row[field]=float(np.mean([d[(d.month==month)&(d.source==src)][field].mean() for src in sources]))
  rr.append(row)
 media=pd.DataFrame(rr);media.to_csv(O/'monthly_media.csv',index=False)
 g=pd.read_csv(O/'sentiment_gap.csv',parse_dates=['period']);fig,ax=plt.subplots(figsize=(9,3));ax.plot(g.period,g.actual,color=COL[2],label='Observed sentiment');ax.plot(g.period,g.predicted,color=COL[0],label='Earlier-data economic prediction');ax.fill_between(g.period,g.lower90,g.upper90,color=COL[0],alpha=.12,label='Nominal 90% interval');ax.legend(frameon=False,fontsize=8,ncol=3,loc='upper center',bbox_to_anchor=(.5,1.15));ax.set_ylabel('Michigan index points');ax.set_xlim(g.period.min(),g.period.max());save('baseline_gap.png')
 m=pd.read_csv(O/'metrics.csv').set_index('model');names=['M1 Economics','M2 Economics + own AI','Households','Full controls','M3 Controls + own AI','Dynamic controls','Dynamic M3','Last month'];z=m.loc[names];fig,ax=plt.subplots(figsize=(9,3.8));ax.barh(range(len(z)),z.rmse,color=[COL[0] if 'AI' in x or x=='Dynamic M3' else COL[2] for x in names]);ax.set_yticks(range(len(z)),['M1: economics','M2: + own AI','+ household pressures','+ regime/method controls','M3: controls + own AI','Dynamic controls','Dynamic M3','Last month']);ax.invert_yaxis();ax.set_xlim(0,z.rmse.max()*1.18)
 for i,v in enumerate(z.rmse):ax.text(v+.08,i,f'{v:.2f}',va='center',fontsize=9)
 ax.set_xlabel('Chronological RMSE, sentiment points (same target months)');save('accuracy.png')
 cov=pd.read_csv(O/'coverage_final.csv',index_col=0).reindex(columns=sources);fig,ax=plt.subplots(figsize=(9,2.1));a=cov.to_numpy().T;im=ax.imshow(a,aspect='auto',vmin=0,vmax=5,cmap='YlGnBu');ax.set_yticks(range(len(sources)),sources);ticks=np.array([i for i,k in enumerate(cov.index) if k.endswith('-01')]);ax.set_xticks(ticks,[cov.index[i][:4] for i in ticks]);fig.colorbar(im,ax=ax,label='Eligible selected titles',shrink=.8);save('coverage.png')
 media['date']=pd.to_datetime(media.month);fig,ax=plt.subplots(figsize=(9,2.8));ax.plot(media.date,media.tone_score,color=COL[0]);ax.fill_between(media.date,media.lower95,media.upper95,color=COL[0],alpha=.18);ax.axhline(0,color='#b5bec5',lw=.8);ax.set_ylabel('Own AI tone, -1 to +1');save('own_media.png')
 c=pd.read_csv(O/'associations_hac.csv');z=c[(c.term=='media')&(c.model.isin(['M2','M3','Dynamic M3']))];fig,ax=plt.subplots(figsize=(9,3));names=[]
 for i,(_,r) in enumerate(z.iterrows()):ax.errorbar(r.coefficient,i,xerr=1.96*r.hac_se,fmt='o',color=COL[0] if r.transformation=='Levels' else COL[1],capsize=3);names.append(r.transformation+' / '+r.model)
 ax.set_yticks(range(len(z)),names);ax.axvline(0,color='#9daab5',lw=1);ax.set_xlabel('Sentiment points per full tone-score unit, 95% HAC intervals');save('association_challenge.png')
 z=d[d.source.isin(sources)];table=z.groupby('source')[['prices','labor','housing','level_frame','rate_frame','political_mention','emotion_word']].mean()*100;table.to_csv(O/'descriptive_source_measures.csv');fig,ax=plt.subplots(figsize=(9,2.8));a=table[['prices','labor','housing']];x=np.arange(len(a));w=.24
 for j,f in enumerate(a.columns):ax.bar(x+(j-1)*w,a[f],width=w,label=f.title(),color=COL[j])
 ax.set_xticks(x,a.index);ax.set_ylabel('% with explicit vocabulary');ax.legend(frameon=False,ncol=3);save('salience.png')
 b=pd.read_csv(O/'baseline_metrics.csv');bm=b.set_index('model');g['period']=g.period.dt.strftime('%Y-%m-%d');latest=json.loads((O/'summary.json').read_text());latest['index_valid_months']=int(media.valid_balanced.sum());latest['coded_source_counts']=d.source.value_counts().to_dict();latest['balanced_item_total']=int(d[d.source.isin(sources)].shape[0]);latest['base_improvement_households']=float(1-bm.loc['Households','rmse']/bm.loc['M1 Economics','rmse']);(O/'summary.json').write_text(json.dumps(latest,indent=2))
if __name__=='__main__':run()
