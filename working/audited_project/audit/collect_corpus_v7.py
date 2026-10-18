"""Original fixed-window metadata collection. Public archives only, no credential bypass."""
from pathlib import Path
import urllib.request,urllib.parse,urllib.error,html,re,json,time,hashlib,calendar,concurrent.futures,threading
import pandas as pd
R=Path(__file__).resolve().parent;D=R/'data/v7_raw';O=R/'outputs_v7';D.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
MONTHS=pd.date_range('2018-01-01','2026-09-01',freq='MS');HEAD={'User-Agent':'AcademicEconomicNarratives/1.0 (noncommercial metadata research)'}
ECON=re.compile(r'\b(economy|economic|inflation|unemployment|employment|jobless|labor market|labour market|job market|jobs|wages?|payrolls?|prices?|cost of living|consumer spending|retail sales|recession|gdp|gross domestic product|mortgages?|housing|rents?|affordability|interest rates?|federal reserve|tariffs?|household debt|credit card debt|debt payments|grocer(?:y|ies)|gasoline|food costs?|home prices?|evictions?|layoffs?|laid off|hiring|costs? of|utility bills?|electricity bills?|food stamps?|minimum wage|real income|disposable income)\b',re.I)
FOREIGN=re.compile(r'\b(China|Chinese|Japan|Japanese|India|Indian|Canada|Canadian|Australia|Australian|Britain|British|UK|U\.K\.|Eurozone|European|Europe|Germany|German|France|French|Argentina|Russia|Russian|Pakistan|Turkey|Turkish|Israel|Israeli|Gaza)\b',re.I)
US=re.compile(r'\b(U\.?S\.?\b|United States|American?s?|Federal Reserve|Fed|Biden|Trump|Powell|California|Texas|New York|NYC|Brooklyn|Florida|Ohio|Michigan|Congress|Washington|Bureau of Labor|BLS|BEA|USDA)\b',re.I)
EXCLUDE=re.compile(r'\b(cosmic inflation|cosmological|quantum|eternal inflation|who is hiring|who wants to be hired|best credit cards|best mortgage lenders|best savings accounts|stock picks|buy these stocks)\b',re.I)
USDOM=re.compile(r'(bls\.gov|bea\.gov|fred\.stlouisfed|federalreserve\.gov|nytimes\.com|wsj\.com|cnbc\.com|npr\.org|pbs\.org|calmatters\.org|texastribune\.org|fortune\.com|apnews\.com|bloomberg\.com|census\.gov|axios\.com|reason\.com)',re.I)
LOCK=threading.Lock();EVENTS=[];BLOCKED_HOSTS={'calmatters.org'}
def clean(s):return ' '.join(html.unescape(re.sub('<[^>]+>',' ',s or '')).split())
def event(**kw):
 with LOCK:EVENTS.append(kw)
def fetch(url):
 host=urllib.parse.urlparse(url).hostname
 with LOCK:
  if host in BLOCKED_HOSTS:raise RuntimeError('Source disabled after access/rate response')
 try:
  r=urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=35);b=r.read();event(url=url,status=r.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b,r.headers
 except urllib.error.HTTPError as e:
  if e.code in [401,403,429]:
   with LOCK:BLOCKED_HOSTS.add(host)
  event(url=url,status=e.code,error=str(e));raise
 except Exception as e:event(url=url,error=str(e));raise

def npr(month):
 label=month.strftime('%Y-%m');cache=D/('NPR_'+label+'.json')
 if cache.exists():return json.loads(cache.read_text())
 first=month.strftime('%Y-%m-%d');last=f'{month.year}-{month.month:02}-{calendar.monthrange(month.year,month.month)[1]:02}';rows=[];seen=set();pages=0;complete=False;error=None
 for start in range(0,450,15):
  u=f'https://www.npr.org/sections/business/archive?start={start}&date={month.month}-{calendar.monthrange(month.year,month.month)[1]}-{month.year}'
  try:b,_=fetch(u);s=b.decode('utf-8','replace')
  except Exception as e:error=str(e);break
  rr=[]
  for card in re.split(r'<article\b[^>]*class="item\b[^\"]*"',s)[1:]:
   h=re.search(r'<h2\b[^>]*class="title"[^>]*>\s*<a\b[^>]*href="([^\"]+)"[^>]*>(.*?)</a>\s*</h2>',card,re.S);p=re.search(r'<p\b[^>]*class="teaser"[^>]*>(.*?)</p>',card,re.S)
   if not h or not p:continue
   dt=re.search(r'<time\b[^>]*datetime="(\d{4}-\d{2}-\d{2})"',p.group(1))
   if not dt:continue
   rr.append(dict(date=dt.group(1),url=html.unescape(h.group(1)),title=clean(h.group(2)),standfirst=clean(re.sub(r'<time\b.*?</time>','',p.group(1),flags=re.S)),date_precision='day',source='NPR',stratum='national',unit='headline_and_archive_standfirst'))
  pages+=1
  if not rr:error='No archive cards parsed';break
  fresh=[r for r in rr if r['url'] not in seen]
  if not fresh:error='Repeated archive page';break
  seen.update(r['url'] for r in rr);rows.extend(r for r in fresh if first<=r['date']<=last)
  if min(r['date'] for r in rr)<first or len(rr)<15:complete=True;break
  time.sleep(.12)
 out=dict(source='NPR',month=label,pages=pages,complete=complete,error=error,rows=rows);cache.write_text(json.dumps(out));print('NPR',label,len(rows),complete,error,flush=True);return out

def wp(source,root,stratum,month):
 label=month.strftime('%Y-%m');cache=D/(source+'_'+label+'.json')
 if cache.exists():return json.loads(cache.read_text())
 first=month.strftime('%Y-%m-%d');end=(month+pd.offsets.MonthBegin(1)).strftime('%Y-%m-%d');rows=[];pages=0;complete=False;error=None;total=None
 # Enumerate all month metadata, then apply the same title-based economic relevance screen.
 for page in range(1,31):
  args=dict(per_page=100,page=page,after=first+'T00:00:00',before=end+'T00:00:00',orderby='date',order='asc',_fields='id,date,date_gmt,link,title,excerpt,categories')
  u=root+'/wp-json/wp/v2/posts?'+urllib.parse.urlencode(args)
  try:b,headers=fetch(u);rr=json.loads(b);total=int(headers.get('X-WP-Total','0'));npages=int(headers.get('X-WP-TotalPages','1'))
  except Exception as e:error=str(e);break
  if not isinstance(rr,list):error='Non-list WordPress response';break
  pages+=1
  for r in rr:
   rows.append(dict(date=(r.get('date_gmt') or r.get('date') or '')[:19],url=r.get('link',''),title=clean(r.get('title',{}).get('rendered','')),standfirst=clean(r.get('excerpt',{}).get('rendered','')),date_precision='publisher_datetime_gmt' if r.get('date_gmt') else 'publisher_datetime_unspecified',source=source,stratum=stratum,unit='headline_and_publisher_excerpt',publisher_id=str(r['id'])))
  if page>=npages:complete=True;break
  time.sleep(.12)
 out=dict(source=source,month=label,pages=pages,total=total,complete=complete,error=error,rows=rows);cache.write_text(json.dumps(out));print(source,label,len(rows),complete,error,flush=True);return out

def hn(month):
 label=month.strftime('%Y-%m');cache=D/('HN_'+label+'.json')
 if cache.exists():return json.loads(cache.read_text())
 first=int(month.tz_localize('UTC').timestamp());end=int((month+pd.offsets.MonthBegin(1)).tz_localize('UTC').timestamp());rows=[];queries=[];error=None
 for term in ['inflation','unemployment','wages','mortgage','recession','US economy','consumer spending','housing affordability']:
  u='https://hn.algolia.com/api/v1/search_by_date?'+urllib.parse.urlencode(dict(query=term,tags='story',numericFilters=f'created_at_i>={first},created_at_i<{end}',hitsPerPage=1000))
  try:b,_=fetch(u);d=json.loads(b)
  except Exception as e:error=str(e);break
  q=dict(query=term,reported_hits=d.get('nbHits'),returned=len(d.get('hits',[])),truncated=d.get('nbHits',0)>len(d.get('hits',[])));queries.append(q)
  for r in d.get('hits',[]):
   if not r.get('title'):continue
   rows.append(dict(date=r.get('created_at',''),url='https://news.ycombinator.com/item?id='+str(r['objectID']),linked_url=r.get('url') or '',title=clean(r['title']),standfirst='',date_precision='submission_datetime_UTC',source='Hacker News',stratum='social',unit='submission_title',publisher_id=str(r['objectID']),query=term))
  time.sleep(.1)
 unique={r['url']:r for r in rows};out=dict(source='Hacker News',month=label,complete=error is None and not any(q['truncated'] for q in queries),queries=queries,error=error,rows=list(unique.values()));cache.write_text(json.dumps(out));print('HN',label,len(unique),out['complete'],error,flush=True);return out

def eligible(r):
 t=r['title'];combined=t+' '+r.get('standfirst','');link=r.get('linked_url','');reason=None;geo='US_local_publisher_context' if r['stratum']=='local' else 'US_publisher_context_no_explicit_foreign'
 if not ECON.search(t):reason='no_economic_term_in_title'
 elif EXCLUDE.search(t):reason='advertisement_advice_or_non_economic_sense'
 elif FOREIGN.search(t) and not US.search(combined):reason='explicit_foreign_focus'
 elif r['stratum']=='social' and not US.search(combined) and not USDOM.search(link):reason='social_US_geography_unverified'
 if US.search(combined):geo='explicit_US_text'
 elif r['stratum']=='social':geo='US_link_context'
 return reason,geo

def assemble():
 rows=[];logs=[];reject=[]
 for cache in sorted(D.glob('*.json')):
  d=json.loads(cache.read_text());logs.append({k:v for k,v in d.items() if k!='rows'})
  for r in d['rows']:
   reason,geo=eligible(r)
   if reason:reject.append(dict(source=r['source'],month=d['month'],reason=reason));continue
   rr=r.copy();rr['month']=rr['date'][:7];rr['us_relevance']=geo;rr['archive_month']=d['month'];rr['archive_complete']=d['complete'];rr['normalized_title']=re.sub(r'\W+','',r['title'].lower());rr['record_id']='C'+hashlib.sha256(r['url'].encode()).hexdigest()[:14];rows.append(rr)
 d=pd.DataFrame(rows).drop_duplicates('url').sort_values(['source','month','date','record_id']);d['is_duplicate_title']=d.duplicated('normalized_title');d.to_csv(O/'candidate_corpus.csv',index=False)
 # Balanced a priori hash samples, up to20 independent title clusters per outlet-month.
 unique=d[~d.is_duplicate_title].copy();unique['sample_hash']=unique.record_id.map(lambda v:hashlib.sha256(('frozen-v7-'+v).encode()).hexdigest());selected=unique.sort_values(['source','month','sample_hash']).groupby(['source','month'],group_keys=False).head(20).copy();selected.to_csv(O/'corpus.csv',index=False)
 pd.DataFrame(logs).to_json(O/'collection_audit.json',orient='records',indent=2);pd.DataFrame(EVENTS).to_json(O/'request_audit.json',orient='records',indent=2)
 if reject:pd.DataFrame(reject).value_counts().rename('n').to_csv(O/'rejection_counts.csv')
 summary=dict(n_candidates=len(d),n_selected=len(selected),sources=selected.source.value_counts().to_dict(),month_first=selected.month.min(),month_last=selected.month.max(),n_months=selected.month.nunique(),incomplete_archive_windows=sum(not a.get('complete',False) for a in logs),selection='Up to20 SHA256-selected unique titles per outlet-month, before seeing any AI labels',unit='Primary model uses titles only for comparability; public standfirst retained for context/sensitivity, no full article bodies')
 (O/'corpus_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
 tasks=[]
 for month in MONTHS:
  tasks.extend([('NPR',month),('Fortune',month),('CalMatters',month),('Texas Tribune',month),('HN',month)])
 def run(task):
  source,month=task
  try:
   if source=='NPR':return npr(month)
   if source=='HN':return hn(month)
   roots={'Fortune':'https://fortune.com','CalMatters':'https://calmatters.org','Texas Tribune':'https://www.texastribune.org'};return wp(source,roots[source],'national' if source=='Fortune' else 'local',month)
  except Exception as e:print('FAILED WINDOW',source,month,str(e),flush=True);return None
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
  for _ in ex.map(run,tasks):pass
 assemble()
