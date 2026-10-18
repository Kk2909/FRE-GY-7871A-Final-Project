from pathlib import Path
import ast,csv,json,re,collections
ROOT=Path(__file__).resolve().parents[3];R=ROOT/'working/audited_project';O=ROOT/'company_final'
def read(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
corpus={r['record_id']:r for r in read(R/'outputs/coded_corpus.csv')}
mapping=read(R/'audit/human_sample_sealed_mapping.csv')
task={r['item_id']:r['title'] for r in read(O/'Human_Annotation_Rater_A.csv')}
tree=ast.parse((R/'audit/score_corpus_v7.py').read_text())
patterns=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PATTERNS' for t in n.targets))
def hits(key,title):return [m.group() for m in re.finditer(patterns[key],title,re.I)]
headers=['item_id','title','tone','economic_direction','source','month','validation_status','relevant_US','emotional_wording_proxy','topic_proxies','price_frame_proxy','time_frame_proxy','political_terms','attribution','numeric_claim_text','factual_status','coding_evidence','method','record_id','source_url']
rows=[]
for m in mapping:
    r=corpus[m['record_id']];t=r['title'];tone=int(r['tone_score']);assert task[m['item_id']]==t
    emotion=hits('emotion_word',t);topics=[k for k in ['prices','labor','housing','growth','debt','policy'] if int(r[k])]
    level=int(r['level_frame']);rate=int(r['rate_frame']);price='both' if level and rate else 'level' if level else 'rate' if rate else 'neither'
    future=bool(re.search(r'\b(will|would|could|may|might|forecast\w*|predict\w*|expect\w*|outlook|next year|next month)\b',t,re.I))
    current=bool(re.search(r'\b(today|this (?:month|year|week)|last (?:month|year|week)|now|currently)\b',t,re.I))
    frame='both' if future and current else 'forecast' if future else 'current_or_recent' if current else 'unspecified'
    political=list(dict.fromkeys(hits('political_mention',t)))
    numeric=bool(re.search(r'\d',t))
    # Literal proxies describe visible wording. They do not establish semantic completeness or accuracy.
    evidence='Tone: retained frozen title-direction label. '
    evidence+='Emotional term matches: '+('; '.join(emotion) if emotion else 'none in the fixed vocabulary')+'. '
    evidence+='Topic term matches: '+('; '.join(topics) if topics else 'none in the fixed vocabulary')+'.'
    rows.append([m['item_id'],t,tone,{-1:'Adverse',0:'Mixed / neutral',1:'Favorable'}[tone],r['source'],r['month'],'Provisional / not independently validated','yes (corpus inclusion)', 'yes' if emotion else 'no_match','; '.join(topics) if topics else 'other',price,frame,'; '.join(political) if political else 'none','undetermined' if political else 'none',t if numeric else 'none','not_checked',evidence,'Automated labeling / frozen tone plus literal wording rules',r['record_id'],r['url']])
assert len(rows)==300 and len({r[0] for r in rows})==300
assert all(r[2] in (-1,0,1) for r in rows)
assert all(all(str(v).strip() for v in r) for r in rows)
with (O/'Title_Annotations_300.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(headers);w.writerows(rows)
method=[
['Scope','The exact 300 titles selected for the original annotation task. One automated label set.'],
['Provenance','Tone labels are copied by record ID from the frozen coded corpus. Other fields use the existing fixed wording patterns or the rules below.'],
['Status','Provisional automated annotations. No independent human labels or human agreement statistics are supplied.'],
['Tone','-1 adverse economic direction; 0 mixed or no clear direction; +1 favorable economic direction. A negative fact can be accurate.'],
['Relevance','All items were retained in the US economic corpus, including state-level experiences and titles whose geography depends on publisher context. This is a prior inclusion decision.'],
['Emotional wording proxy','yes = a fixed emotional-word pattern matches; no_match = no pattern matches. Absence of a match does not establish emotionally neutral language.'],
['Topic proxies','Overlapping fixed vocabulary for prices, labor, housing, growth, debt and policy. Other means no vocabulary match.'],
['Price frame proxy','Existing literal patterns distinguish elevated price levels from change rates. Neither means no match. These rules do not capture every semantic price frame.'],
['Time frame proxy','Forecast = modal/forecast wording. Current_or_recent = today, this/last month/year/week, now or currently. Both = both types of match. Unspecified = neither.'],
['Political terms','Exact matches from the fixed political vocabulary. Mention alone does not establish credit or blame. Attribution stays undetermined when political terms occur.'],
['Numeric claim text','For titles with digits, the full title preserves the numerical context for review. None means no digit match, not proof of no quantitative assertion.'],
['Factual status','not_checked for all 300. No factual accuracy or bias prevalence claim follows from these annotations.'],
['Evidence','Records the frozen tone origin and matched literal categories. The title provides the text being coded.'],
['Independence','This file contains one label set. It must not be duplicated into two rater files or used to claim inter-rater reliability.'],
['Model connection','These frozen tone values already feed the monthly news index and reported models. Exporting this subset does not create new independent validation or change forecast results.'],
['Sources','Source links and stable record IDs are included in every row. Publication month follows the archived metadata.'],
['Fixed vocabulary',json.dumps(patterns,ensure_ascii=False)],
]
(ROOT/'work').mkdir(exist_ok=True)
(ROOT/'work/title_annotations_payload.json').write_text(json.dumps({'headers':headers,'rows':rows,'method':method},ensure_ascii=False))
(R/'company/TITLE_ANNOTATIONS_README.md').write_text('# 300-title annotation export\n\nOne automated label set covering the exact 300 task titles. Tone labels are retained from the frozen source corpus. Literal rules supply wording proxies. Factual status remains not_checked. The export supplies no independent human validation or inter-rater reliability. Main model results are unchanged. Full field definitions appear in the workbook Method sheet.\n')
print(json.dumps({'rows':len(rows),'tone_counts':dict(collections.Counter(r[2] for r in rows))}))
