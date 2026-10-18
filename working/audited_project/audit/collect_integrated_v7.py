"""Bounded original archive sampling. Cached public metadata, explicit frame and rate handling."""
import os
os.environ["ORT_DISABLE_TELEMETRY"]="1"
from pathlib import Path
import urllib.request,urllib.parse,urllib.error,json,time,re,html,hashlib,calendar,threading,concurrent.futures
import pandas as pd
from collect_corpus_v7 import ECON,FOREIGN,EXCLUDE,USDOM,clean
R=Path(__file__).resolve().parent;D=R/'data/v7_media';D.mkdir(exist_ok=True);O=R/'outputs_v7';O.mkdir(exist_ok=True)
MONTHS=pd.date_range('2019-11-01','2026-09-01',freq='MS');LOCK=threading.Lock();BLOCKED=set();EVENT=[]; HOST_SLOTS={h:threading.BoundedSemaphore(2) for h in ['www.npr.org','fortune.com','www.texastribune.org','hn.algolia.com']}
US=re.compile(r'\b((?-i:US|U\.S)|United States|Americans?|America|Federal Reserve|(?-i:Fed)|Biden|Trump|Powell|California|Texas|New York|NYC|Brooklyn|Florida|Ohio|Michigan|Congress|Washington|Bureau of Labor|(?-i:BLS|BEA|USDA))\b',re.I)
TAGS=[12556012,161717,447824896,447864895] # Returned exact public tags: U.S.economy, inflation, housing, jobs.
def get_inner(url):
 host=urllib.parse.urlparse(url).hostname
 if host not in {'www.npr.org','fortune.com','www.texastribune.org','hn.algolia.com'}:raise RuntimeError('Non-data host blocked: '+str(host))
 with LOCK:
  if host in BLOCKED:raise RuntimeError('Host paused after access/rate response')
 for attempt in range(2):
  try:
   time.sleep(.4);r=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AcademicEconomicNarratives/1.0 noncommercial-metadata-research'}),timeout=35);b=r.read()
   with LOCK:EVENT.append(dict(url=url,status=r.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
   return b,r.headers
  except urllib.error.HTTPError as e:
   with LOCK:EVENT.append(dict(url=url,status=e.code,error=str(e),retry_after=e.headers.get('Retry-After')))
   if e.code==429 and attempt==0:
    delay=max(30,min(60,int(e.headers.get('Retry-After','30')) if e.headers.get('Retry-After','30').isdigit() else 30));print('Rate response: honoring',delay,'seconds for',host,flush=True);time.sleep(delay);continue
   if e.code in [401,403,429]:
    with LOCK:BLOCKED.add(host)
   raise
  except Exception as e:
   with LOCK:EVENT.append(dict(url=url,error=str(e)))
   raise

def get(url):
 host=urllib.parse.urlparse(url).hostname
 if host not in HOST_SLOTS:raise RuntimeError('Non-data host blocked')
 with HOST_SLOTS[host]:return get_inner(url)

def npr(m):
 out=[];snapshots=[];last=calendar.monthrange(m.year,m.month)[1]
 for lower,upper in [(1,7),(8,14),(15,21),(22,last)]:
  url=f'https://www.npr.org/sections/business/archive?date={m.month}-{upper}-{m.year}';b,_=get(url);s=b.decode('utf-8','replace');rr=[]
  for card in re.split(r'<article\b[^>]*class="item\b[^\"]*"',s)[1:]:
   h=re.search(r'<h2\b[^>]*class="title"[^>]*>\s*<a\b[^>]*href="([^\"]+)"[^>]*>(.*?)</a>\s*</h2>',card,re.S);p=re.search(r'<p\b[^>]*class="teaser"[^>]*>(.*?)</p>',card,re.S)
   if not h or not p:continue
   dt=re.search(r'<time\b[^>]*datetime="(\d{4}-\d{2}-\d{2})"',p.group(1))
   if not dt:continue
   rr.append(dict(date=dt.group(1),url=html.unescape(h.group(1)),title=clean(h.group(2)),standfirst=clean(re.sub(r'<time\b.*?</time>','',p.group(1),flags=re.S)),date_precision='day',source='NPR',stratum='national',unit='headline_and_archive_standfirst',segment=str(lower)+'-'+str(upper)))
  if not rr:raise RuntimeError('No NPR cards parsed')
  a=f'{m.year}-{m.month:02}-{lower:02}';z=f'{m.year}-{m.month:02}-{upper:02}';kept=[r for r in rr if a<=r['date']<=z];out.extend(kept);snapshots.append(dict(url=url,parsed=len(rr),retained_in_segment=len(kept),earliest=min(r['date'] for r in rr),full_segment_enumeration=False))
 return out,dict(snapshots=snapshots,frame='Up to15 visible Business-archive cards at four fixed weekly endpoints, restricted to each block; not a full-publication census')

def wp(source,m):
 root='https://fortune.com' if source=='Fortune' else 'https://www.texastribune.org';end=m+pd.offsets.MonthBegin(1);out=[];total=None;npages=None
 for page in range(1,21):
  args=dict(per_page=100,page=page,after=m.strftime('%Y-%m-%dT00:00:00'),before=end.strftime('%Y-%m-%dT00:00:00'),orderby='date',order='asc',_fields='id,date,date_gmt,link,title,excerpt,categories,tags')
  if source=='Fortune':args['tags']=','.join(map(str,TAGS))
  b,h=get(root+'/wp-json/wp/v2/posts?'+urllib.parse.urlencode(args));rr=json.loads(b);total=int(h.get('X-WP-Total','0'));npages=int(h.get('X-WP-TotalPages','1'))
  if not isinstance(rr,list):raise RuntimeError('Non-list WP response')
  for r in rr:out.append(dict(date=(r.get('date_gmt') or r.get('date') or '')[:19],url=r.get('link',''),title=clean(r.get('title',{}).get('rendered','')),standfirst=clean(r.get('excerpt',{}).get('rendered','')),date_precision='publisher_datetime_GMT' if r.get('date_gmt') else 'publisher_datetime_unspecified',source=source,stratum='national' if source=='Fortune' else 'local',unit='headline_and_public_metadata_excerpt',publisher_id=str(r['id'])))
  if page>=npages:return out,dict(total=total,pages=page,frame='Union of four fixed economic tags' if source=='Fortune' else 'All public monthly publisher post metadata, then economic-title screen')
 raise RuntimeError('WP pagination exceeds explicit cap')

def hn(m):
 a=int(m.tz_localize('UTC').timestamp());b=int((m+pd.offsets.MonthBegin(1)).tz_localize('UTC').timestamp());out=[];q=[]
 for term in ['inflation','unemployment','wages','mortgage','recession','US economy','consumer spending','housing affordability']:
  u='https://hn.algolia.com/api/v1/search_by_date?'+urllib.parse.urlencode(dict(query=term,tags='story',numericFilters=f'created_at_i>={a},created_at_i<{b}',hitsPerPage=1000));raw,_=get(u);d=json.loads(raw);hits=d.get('hits',[]);q.append(dict(query=term,reported_hits=d.get('nbHits'),returned=len(hits),truncated=d.get('nbHits',0)>len(hits)))
  for r in hits:
   if r.get('title'):out.append(dict(date=r['created_at'],url='https://news.ycombinator.com/item?id='+str(r['objectID']),linked_url=r.get('url') or '',title=clean(r['title']),standfirst='',date_precision='submission_datetime_UTC',source='Hacker News',stratum='social',unit='submission_title',query=term,publisher_id=str(r['objectID'])))
 return list({r['url']:r for r in out}.values()),dict(queries=q,frame='Union of eight fixed monthly title/body search queries, title-screened; no usernames/comments/engagement weights')

def window(source,m):
 name='HN' if source=='Hacker News' else source;cache=D/(name+'_'+m.strftime('%Y-%m')+'.json')
 if cache.exists():return json.loads(cache.read_text())
 try:
  rows,meta=npr(m) if source=='NPR' else hn(m) if source=='Hacker News' else wp(source,m);d=dict(source=source,month=m.strftime('%Y-%m'),complete=True,rows=rows,**meta)
 except Exception as e:d=dict(source=source,month=m.strftime('%Y-%m'),complete=False,error=str(e),rows=[])
 temporary=cache.with_suffix('.tmp');temporary.write_text(json.dumps(d));temporary.replace(cache);print(source,m.strftime('%Y-%m'),len(d['rows']),d['complete'],d.get('error',''),flush=True);return d

def assemble():
 rr=[];audit=[];reject=[]
 for path in sorted(D.glob('*.json')):
  d=json.loads(path.read_text());audit.append({k:v for k,v in d.items() if k!='rows'})
  for r in d['rows']:
   t=r['title'];ctx=t+' '+r.get('standfirst','');why=None;geo='US_state_publisher_context' if r['stratum']=='local' else 'US_publisher_context_no_explicit_foreign'
   if not ECON.search(t):why='not_economic_title'
   elif EXCLUDE.search(t) or re.search(r'\b(show hn|launch hn|wages war|cpi inflation calculator|money-saving.*tips|grade inflation|free will inflation|software inflation|cosmolog\w*|cosmic inflation|bitcoin.s inflation)\b',t,re.I):why='advertisement_advice_or_non_economic_sense'
   elif FOREIGN.search(t) and not US.search(ctx):why='explicit_foreign_focus'
   elif r['stratum']=='social' and not US.search(ctx) and not USDOM.search(r.get('linked_url','')):why='social_geography_unverified'
   if why:reject.append(dict(source=r['source'],month=d['month'],reason=why));continue
   if US.search(ctx):geo='explicit_US_text'
   elif r['stratum']=='social':geo='US_link_context'
   row=r.copy();row['month']=r['date'][:7];row['us_relevance']=geo;row['record_id']='I'+hashlib.sha256(r['url'].encode()).hexdigest()[:14];row['normalized_title']=re.sub(r'\W+','',t.lower());row['archive_window']=d['month'];rr.append(row)
 if not rr:raise RuntimeError('No eligible records collected')
 d=pd.DataFrame(rr);d=d[d.month.between('2019-11','2026-09')].drop_duplicates('url');d=d.sort_values(['date','source','record_id']);d['exact_duplicate_title']=d.duplicated(['month','normalized_title']);d.to_csv(O/'candidate_corpus.csv',index=False)
 unique=d[~d.exact_duplicate_title].copy();unique['sample_hash']=unique.record_id.map(lambda x:hashlib.sha256(('integrated-v7-fixed-'+x).encode()).hexdigest());sel=unique.sort_values(['source','month','sample_hash']).groupby(['source','month'],group_keys=False).head(20);sel.to_csv(O/'corpus.csv',index=False)
 (O/'collection_audit.json').write_text(json.dumps(audit,indent=2));(O/'request_audit.json').write_text(json.dumps(EVENT,indent=2));pd.DataFrame(reject).value_counts().rename('n').to_csv(O/'rejection_counts.csv');pd.crosstab(sel.month,sel.source).to_csv(O/'coverage.csv')
 s=dict(n_candidates=len(d),n_unique_titles=len(unique),n_sample=len(sel),by_source=sel.source.value_counts().to_dict(),first_month=sel.month.min(),last_month=sel.month.max(),n_months=sel.month.nunique(),incomplete_windows=sum(not x['complete'] for x in audit),sampling='Max20 hash-selected unique titles per outlet-month from fixed public retrieval frames, selected before AI scores',original_data_only=True)
 (O/'corpus_summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2),flush=True)
if __name__=='__main__':
 jobs=[(source,m) for m in MONTHS[::-1] for source in ['NPR','Fortune','Hacker News']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for _ in pool.map(lambda args:window(*args),jobs):pass
 assemble()
