"""Recorded source-blind assistant reference coding, before viewing model predictions.
This is an AI reference, not human annotation or independent ground truth.
Tone: -1 adverse, 0 undirected/mixed, +1 improving. Factual correctness is separate.
All300 new titles are transfer evaluation only; none trains the selected classifier.
"""
from pathlib import Path
import pandas as pd,json
R=Path(__file__).resolve().parent;O=R/'outputs_v7'
# Rows correspond to the immutable shuffled N001-N300 blind-title file.
GROUPS=[
[0,0,1,-1,0,-1,0,1,-1,0],
[-1,0,-1,-1,0,0,1,1,0,-1],
[1,-1,0,0,1,-1,0,-1,1,0],
[-1,-1,-1,-1,0,0,0,1,0,-1],
[1,-1,0,1,1,-1,-1,-1,-1,0],
[-1,-1,0,1,1,1,0,-1,-1,-1],
[0,1,-1,1,1,0,-1,-1,0,0],
[0,1,-1,-1,1,0,-1,-1,0,-1],
[1,1,0,-1,0,0,0,0,-1,0],
[1,-1,0,0,0,0,0,1,1,-1],
[0,0,1,1,0,-1,-1,0,1,1],
[-1,0,0,1,0,0,-1,-1,0,0],
[1,0,-1,0,0,-1,-1,0,-1,-1],
[1,-1,1,-1,1,0,-1,-1,1,0],
[0,0,-1,-1,0,-1,1,0,0,-1],
[0,1,0,0,-1,0,0,0,0,0],
[0,1,-1,1,0,0,0,0,1,1],
[0,-1,0,1,-1,0,-1,-1,-1,0],
[0,0,1,-1,0,0,0,-1,1,1],
[-1,0,-1,-1,-1,-1,0,-1,0,0],
[-1,-1,0,-1,0,0,0,1,1,0],
[0,-1,0,-1,1,-1,-1,1,0,0],
[0,-1,-1,-1,-1,-1,-1,0,-1,0],
[-1,0,-1,-1,0,-1,0,-1,0,0],
[0,-1,-1,-1,1,0,-1,0,0,0],
[0,0,-1,-1,-1,1,-1,1,1,1],
[0,-1,1,-1,-1,-1,-1,1,-1,0],
[-1,0,0,1,-1,0,0,-1,0,-1],
[-1,-1,-1,-1,0,-1,-1,0,-1,-1],
[0,1,0,-1,0,-1,0,0,-1,0]]
y=[v for group in GROUPS for v in group];assert len(y)==300
p=pd.read_csv(O/'new_reference_mapping.csv',keep_default_na=False).sort_values('audit_id');assert p.audit_id.tolist()==['N'+str(i+1).zfill(3) for i in range(300)]
p['reference_tone']=y;p['reference_type']='source-metadata-blind assistant coding, one pass';p['split']='heldout_transfer_only';p['reference_relevant']=1
# Clearly non-current-US-economic or self-promotional title examples found in the blind audit.
EXCLUDE={7:'Show HN self-promotion',43:'wages war is a non-economic sense of wages',53:'human-interest shopping positivity without economic conditions',58:'euro-zone outcome, US shock is context',93:'Argentina dollarisation, US dollar is not US economic geography',105:'Chinese growth prospects rather than US conditions',180:'Show HN self-promotion',200:'data product promotion',206:'historical1872 conditions',211:'personal shopping tips',212:'Shenzhen outcome with US policy context',230:'calculator resource',241:'Indian policy worldview',250:'calculator resource',251:'food human-interest without economic conditions',258:'Dominican Republic growth',266:'physical health of device use'}
p['relevance_note']='Within broad economic-content scope, conditional on metadata';
for i,note in EXCLUDE.items():p.loc[p.audit_id=='N'+str(i).zfill(3),['reference_relevant','relevance_note']]=[0,note]
NOTES={1:'Recession risk and entrepreneurial opportunity point in opposite directions.',19:'Hiring improves while unemployment worsens.',35:'Rent distress and new relief both appear.',41:'Falling rents and slower inflation improve household affordability.',57:'Slowing growth and still-solid output are mixed.',90:'Improvement and low-income lag coexist.',94:'Jobs increase while unemployment rises.',147:'Negation matters: not crashing conveys reassurance.',167:'Strong hiring and a higher jobless rate are mixed.',203:'Housing emergency and worker-housing purchase coexist.',204:'Large GDP contraction is adverse even without adjectives.',210:'Lower prices and higher unemployment are mixed.',213:'Higher unemployment and benefit relief coexist.',245:'Recovery and refunds are favorable.',274:'The headline conveys a favorable price claim; the CEO claim is not independently certified.',291:'New housing supply and unmet demand are mixed.'}
p['coding_note']=['Adverse economic direction or burden.' if v<0 else ('Favorable economic direction or relief.' if v>0 else 'Mixed directions, a question without an answer, or no explicit directional economic claim.') for v in y]
for i,note in NOTES.items():p.loc[p.audit_id=='N'+str(i).zfill(3),'coding_note']=note
p.to_csv(O/'new_ai_reference_300.csv',index=False)
(O/'new_reference_protocol.json').write_text(json.dumps(dict(n=300,selection='100 per primary source, each balanced across early2019-21, middle2022-24 and recent2025-26 available records, hash-selected without model scores; old exact-title references excluded',source_metadata_blind=True,model_predictions_hidden_when_coding=True,human_annotators=0,training_use=False,original_planned_split='An initially drafted training-extension split was unused. All300 remain evaluation-only; no new reference labels train or tune the selected classifier.',limitations='Same assistant/conversation, one new reference pass, subjective mixed-tone decisions, no independent human ground truth.'),indent=2))
print(p.reference_tone.value_counts().to_dict());print('Relevant',int(p.reference_relevant.sum()))
