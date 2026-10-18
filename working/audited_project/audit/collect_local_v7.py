"""Replacement independent state archives after Texas access limit. Metadata only."""
import os
os.environ['ORT_DISABLE_TELEMETRY']='1'
from pathlib import Path
import urllib.request,urllib.parse,urllib.error,json,time,concurrent.futures,hashlib
import pandas as pd
from collect_corpus_v7 import clean
R=Path(__file__).resolve().parent;D=R/'data/v7_media';O=R/'outputs_v7';EVENT=[]
SOURCES={'CT Mirror':('https://ctmirror.org',[39891]),'Colorado Sun':('https://coloradosun.com',[18554,18558,18559])}
def collect_source(name):
 root,categories=SOURCES[name];blocked=False
 for m in pd.date_range('2019-11-01','2026-09-01',freq='MS')[::-1]:
  cache=D/(name+'_'+m.strftime('%Y-%m')+'.json')
  if cache.exists():continue
  rows=[];error=None;total=0
  try:
   if blocked:raise RuntimeError('Host paused after access/rate response')
   for page in range(1,6):
    args=dict(categories=','.join(map(str,categories)),per_page=100,page=page,after=m.strftime('%Y-%m-%dT00:00:00'),before=(m+pd.offsets.MonthBegin(1)).strftime('%Y-%m-%dT00:00:00'),orderby='date',order='asc',_fields='id,date,date_gmt,link,title,excerpt,categories')
    u=root+'/wp-json/wp/v2/posts?'+urllib.parse.urlencode(args)
    for attempt in range(2):
     try:
      time.sleep(1.2);r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'AcademicEconomicNarratives/1.0 noncommercial-public-metadata'}),timeout=12);b=r.read();EVENT.append(dict(url=u,status=r.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()));break
     except urllib.error.HTTPError as e:
      EVENT.append(dict(url=u,status=e.code))
      if e.code==429 and attempt==0:time.sleep(45);continue
      if e.code in [401,403,429]:blocked=True
      raise
    z=json.loads(b);total=int(r.headers.get('X-WP-Total',0));npages=int(r.headers.get('X-WP-TotalPages',1))
    for q in z:rows.append(dict(date=(q.get('date_gmt') or q['date'])[:19],url=q['link'],title=clean(q['title']['rendered']),standfirst=clean(q.get('excerpt',{}).get('rendered','')),date_precision='publisher_datetime_GMT' if q.get('date_gmt') else 'publisher_datetime_unspecified',source=name,stratum='local',unit='headline_and_public_metadata_excerpt',publisher_id=str(q['id'])))
    if page>=npages:break
    if page==5:raise RuntimeError('Pagination exceeds explicit cap')
  except Exception as e:error=str(e)
  d=dict(source=name,month=m.strftime('%Y-%m'),complete=error is None,error=error,rows=rows,total=total,frame='Fixed public category union, followed by frozen economic-title inclusion screen',categories=categories)
  tmp=cache.with_suffix('.tmp');tmp.write_text(json.dumps(d));tmp.replace(cache);print(name,m.strftime('%Y-%m'),len(rows),error,flush=True)
 with open(O/('local_requests_'+name.replace(' ','_')+'.json'),'w') as f:json.dump(EVENT,f,indent=2)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(2) as ex:list(ex.map(collect_source,SOURCES))
