"""Rebuild every analysis input from frozen raw snapshots, never an intermediate panel."""
from pathlib import Path
import pandas as pd,numpy as np
from v7_core import raw,outcomes
R=Path(__file__).resolve().parent

def build():
 pce=raw('PCEPI');inc=raw('DSPIC96')
 values={'u3':(raw('UNRATE'),45),'pce_yoy':(100*(pce/pce.shift(12)-1),45),'gdp':(raw('A191RL1Q225SBEA',True),35),'income_growth':(100*(inc/inc.shift(12)-1),45)}
 news=pd.read_excel(R/'data/FRBSF_News_Sentiment.xlsx',sheet_name='Data');news.columns=['date','news'];news.date=pd.to_datetime(news.date);news=news.set_index('date').news.dropna()
 y=outcomes()['Headline'];rows=[]
 for t in pd.date_range('2010-01-31','2026-10-31',freq='ME'):
  origin=t.replace(day=1);row=dict(period=t,origin=origin,preliminary=t==pd.Timestamp('2026-10-31'),y=y.get(t,np.nan))
  for k in [1,2,3]:row['s'+str(k)]=y.get(t-pd.offsets.MonthEnd(k),np.nan)
  for key,(s,days) in values.items():
   s=s.dropna();a=s[s.index+pd.Timedelta(days=days)<=origin];assert len(a)>0
   row[key]=float(a.iloc[-1]);row[key+'_period']=a.index[-1];row[key+'_available']=a.index[-1]+pd.Timedelta(days=days)
  end=origin-pd.Timedelta(days=7);start=end-pd.Timedelta(days=30);v=news.loc[start:end];assert len(v)>=25
  row.update(news=float(v.mean()),news_start=start,news_end=end,news_available=end+pd.Timedelta(days=7),news_n=len(v));rows.append(row)
 p=pd.DataFrame(rows);assert not p.isna().any().any();p.to_csv(R/'outputs/rebuilt_economic_inputs.csv',index=False);return p
if __name__=='__main__':print(build().shape)
