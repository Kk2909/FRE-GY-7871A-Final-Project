from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import norm,t as tdist
R=Path(__file__).resolve().parent


def add_constant(x,has_constant=None):
    out=x.copy();out.insert(0,'const',1.0);return out

class OLS:
    """Least squares with Moore-Penrose inverse and Bartlett Newey-West covariance."""
    def __init__(self,y,x):self.y=np.asarray(y,float);self.x=np.asarray(x,float);self.names=list(x.columns) if hasattr(x,'columns') else ['const']
    def fit(self,cov_type=None,cov_kwds=None):
        x,y=self.x,self.y;n,k=x.shape;inv=np.linalg.pinv(x.T@x);b=np.linalg.lstsq(x,y,rcond=None)[0];e=y-x@b
        self.sigma2=float(e@e/(n-np.linalg.matrix_rank(x)));self.inv=inv;self.df=n-np.linalg.matrix_rank(x)
        cov=self.sigma2*inv
        if cov_type=='HAC':
            xe=x*e[:,None];meat=xe.T@xe;L=cov_kwds['maxlags']
            for lag in range(1,L+1):
                gamma=xe[lag:].T@xe[:-lag];meat+=(1-lag/(L+1))*(gamma+gamma.T)
            cov=inv@meat@inv
        self.params=pd.Series(b,index=self.names);self.bse=pd.Series(np.sqrt(np.maximum(0,np.diag(cov))),index=self.names)
        z=np.divide(b,self.bse.to_numpy(),out=np.zeros_like(b),where=self.bse.to_numpy()>1e-14)
        self.pvalues=pd.Series(2*norm.sf(abs(z)),index=self.names);self.rsquared=1-float(e@e)/float(((y-y.mean())**2).sum()) if np.var(y)>0 else np.nan
        return self
    def predict(self,x):return pd.Series(np.asarray(x,float)@self.params.to_numpy())
    def get_prediction(self,x):self.xp=np.asarray(x,float);return self
    def summary_frame(self,alpha=.1):
        p=self.xp@self.params.to_numpy();h=tdist.ppf(1-alpha/2,self.df)*np.sqrt(self.sigma2*(1+np.einsum('ij,jk,ik->i',self.xp,self.inv,self.xp)))
        return pd.DataFrame({'obs_ci_lower':p-h,'obs_ci_upper':p+h})

def multipletests(p,method='holm'):
    p=np.asarray(p);order=np.argsort(p);out=np.empty_like(p);out[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    return out<.05,out,None,None

def raw(s,quarter=False,weekly=False):
 p=R/'data/multifactor'/f'FRED_{s}.csv'
 if not p.exists():p=R/'data'/f'FRED_{s}.csv'
 d=pd.read_csv(p);d.columns=['date','value'];d.date=pd.to_datetime(d.date);d.value=pd.to_numeric(d.value,errors='coerce');d=d.dropna().sort_values('date')
 if not weekly:d.date=d.date+(pd.offsets.QuarterEnd(0) if quarter else pd.offsets.MonthEnd(0))
 assert not d.date.duplicated().any();s=d.set_index('date').value
 if not weekly and not quarter:s=s.reindex(pd.date_range(s.index.min(),s.index.max(),freq='ME'))
 return s

def outcomes():
 d=pd.read_excel(R/'data/Perceptual_Bias_Data.xlsx').iloc[:,[3,4]].dropna();d.columns=['period','sentiment'];d.period=pd.to_datetime(d.period);s=d.set_index('period').sentiment.sort_index()
 c=pd.read_csv(R/'data/Michigan_Components.csv');c['period']=pd.to_datetime(c['Month']+' '+c.YYYY.astype(str))+pd.offsets.MonthEnd(0);c=c.set_index('period').sort_index();return {'Headline':s,'Conditions':pd.to_numeric(c.ICC,errors='coerce'),'Expectations':pd.to_numeric(c.ICE,errors='coerce')}