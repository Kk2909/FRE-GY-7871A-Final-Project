from pathlib import Path
import json
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'outputs';E=R/'company/exhibits';E.mkdir(exist_ok=True)
N='#142B42';T='#007F78';A='#B96E45';G='#64768A';L='#DCE6EB';BG='#FFFFFF'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':N,'axes.labelcolor':N,'xtick.color':G,'ytick.color':N,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':L,'axes.axisbelow':True})
def save(name):plt.tight_layout(pad=.6);plt.savefig(E/name,dpi=210,bbox_inches='tight',facecolor=BG);plt.close()
def bar(name,keys,labels):
 m=pd.read_csv(O/'metrics.csv').set_index('model');v=m.loc[keys].rmse
 fig,ax=plt.subplots(figsize=(8,2.45));ax.barh(range(len(v)),v,color=[T if 'AI' in k or k=='Dynamic M3' else N for k in keys],height=.58);ax.set_yticks(range(len(v)),labels);ax.invert_yaxis();ax.set_xlim(0,max(v)*1.23);ax.grid(axis='x',color=L,lw=.6)
 for i,x in enumerate(v):ax.text(x+max(v)*.025,i,f'{x:.2f}',va='center',fontweight='bold',fontsize=12)
 ax.set_xlabel('Forecast RMSE / sentiment index points / lower is better');save(name)
bar('required_models.png',['M1 Economics','M2 Economics + own AI','Full controls','M3 Controls + own AI'],['M1  Economic indicators','M2  Economics + AI tone','C  Full controls, no tone','M3  Full controls + AI tone'])
bar('dynamic_models.png',['Last month','Dynamic controls','Dynamic M3'],['Last month unchanged','Dynamic controls','Dynamic controls + AI tone'])
c=pd.read_csv(O/'associations_hac.csv');z=c[(c.transformation=='Levels')&(c.term=='media')].set_index('model').loc[['M2','M3','Dynamic M3']];fig,ax=plt.subplots(figsize=(8,2.3));ax.axvline(0,color=G,lw=.8);ax.errorbar(z.coefficient*.1,range(3),xerr=np.array([z.coefficient-z.lower95,z.upper95-z.coefficient])*.1,fmt='o',color=T,ecolor=T,elinewidth=2,capsize=5,markersize=7);ax.set_yticks(range(3),['M2  Economic indicators','M3  Broader controls','Dynamic M3  Prior sentiment']);ax.invert_yaxis();ax.grid(axis='x',color=L,lw=.6);ax.set_xlabel('Sentiment points per 0.1 tone increase / 95% calendar-HAC interval');save('media_coefficients.png')
g=pd.read_csv(O/'baseline_forecasts.csv',parse_dates=['period']);g=g[(g.model=='M1 Economics')&(~g.preliminary)];fig,ax=plt.subplots(figsize=(8,2.6));ax.fill_between(g.period,g.lower90,g.upper90,color=T,alpha=.09,label='Nominal 90% interval');ax.plot(g.period,g.predicted,color=T,lw=1.9,label='Economic prediction');ax.plot(g.period,g.actual,color=N,lw=1.9,label='Observed sentiment');ax.legend(frameon=False,ncol=3,fontsize=8,loc='upper center',bbox_to_anchor=(.5,1.17));ax.set_xlim(g.period.min(),g.period.max());ax.set_ylabel('Michigan index points');ax.grid(axis='y',color=L,lw=.6);save('baseline_gap.png')
m=pd.read_csv(O/'monthly_media.csv');cols=['n_NPR','n_Colorado_Sun','n_Hacker_News'];fig,ax=plt.subplots(figsize=(8,1.8));a=m[cols].to_numpy().T;im=ax.imshow(a,aspect='auto',vmin=0,vmax=5,cmap='Blues',interpolation='nearest');ax.set_yticks(range(3),['NPR','Colorado Sun','Hacker News']);ix=np.array([i for i,v in enumerate(m.month) if v.endswith('-01')]);ax.set_xticks(ix,m.month.iloc[ix].str[:4]);ax.tick_params(axis='both',length=0);fig.colorbar(im,ax=ax,label='Titles',ticks=[0,3,5],shrink=.8,pad=.02);save('source_coverage.png')
# One source of truth for the editable deck and redesigned report.
metrics=pd.read_csv(O/'metrics.csv');assoc=c[(c.transformation=='Levels')&(c.term=='media')];p=pd.read_csv(O/'model_parameter_audit.csv');co=c[(c.transformation=='Levels')&(c.model=='M3')];s=json.load(open(O/'summary.json'))
data={'metrics':metrics.to_dict('records'),'media_slopes':assoc.to_dict('records'),'parameters':p.to_dict('records'),'M3_coefficients':co.to_dict('records'),'baseline':json.loads(g.to_json(orient='records',date_format='iso')),'summary':s,'paired_tests':pd.read_csv(O/'comparison_tests.csv').to_dict('records'),'source_counts':{'NPR':220,'Colorado Sun':223,'Hacker News':227}}
(R/'company/evidence.json').write_text(json.dumps(data,indent=2));print('Company exhibits use frozen verified outputs. No new model fitted.')
