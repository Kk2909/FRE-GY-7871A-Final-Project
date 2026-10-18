from pathlib import Path
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,PageBreak,Table,TableStyle,Spacer
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from matplotlib.font_manager import findfont,FontProperties
R=Path(__file__).resolve().parent;DEST=R.parent.parent/'company_final'
S=json.loads((R/'company/presenter_script.json').read_text())
(R/'company/speaking_script.json').write_text(json.dumps(S,indent=2))
for n,w in [('D','normal'),('DB','bold')]:pdfmetrics.registerFont(TTFont(n,findfont(FontProperties(family='DejaVu Sans',weight=w))))
st=getSampleStyleSheet()
for n,size,lead,f,col in [('B',10.5,15,'D','#263B4C'),('H',21,27,'DB','#17293D'),('S',12,17,'DB','#008577')]:st.add(ParagraphStyle(name=n,fontName=f,fontSize=size,leading=lead,spaceAfter=9,textColor=colors.HexColor(col)))
def P(t,k='B'):return Paragraph(t,st[k])
def footer(c,d):c.setFont('D',8);c.drawString(48,26,'Khushi Khanna / Presentation and understanding guide');c.drawRightString(547,26,str(d.page))
parts=[]
def page(title,text):parts.extend([P(title,'H')]+text+[PageBreak()])
page('Understand the argument before rehearsing',[
P('The one-sentence answer','S'),P('Our original news-tone measure adds little dependable information after broader controls and previous sentiment, so the evidence does not establish media bias as the cause of pessimism.'),
P('The complete chain','S'),P('Public titles become labels. Labels become one balanced monthly index. Earlier index values enter regressions. Predictions are compared with actual sentiment on the same dates. The text data therefore feed the main statistical analysis.'),
P('Keep the units and samples separate','S'),P('670 titles produce 47 monthly index readings. Timing gives 45 finalized regression observations. The first 24 train the initial models. The next 21 evaluate predictions. The economic baseline uses a separate 81-month test. Never say that the regression has 670 independent monthly observations.'),
P('The calculation in plain language','S'),P('For a source with five labels of -1, -1, 0, 0, and +1, the mean is -0.2. Average that source mean equally with NPR and the other source. A 0.1 movement is a tenth of this -1 to +1 scale. It is not a percentage of Americans.'),
P('What is unfinished?','S'),P('The exported 300-title sheet contains automated annotations. It does not complete independent human validation. The historical evaluation uses revised snapshots and assumed posting lags. Consistency and numerical reproduction do not remove these limitations.')])
for start,end in [(0,2),(2,4),(4,6),(6,8)]:
 page('Your 6-minute script: slides '+str(start+1)+'-'+str(end),[item for title,secs,text in S[start:end] for item in [P(title+' / '+str(secs)+' seconds','S'),P(text)]])
page('Questions about the text analysis',[
P('What is the original text-analysis contribution?','S'),P('The project builds an original monthly index from 670 economic titles and enters that index directly into matched forecast comparisons. It also describes topic and price-framing vocabulary and checks selected factual claims against official releases.'),
P('Why does 68% become 53.3%?','S'),P('The same hybrid classifier performs worse against automated references on a new 300-title transfer set than in grouped development evaluation. The reference sets and class mix differ. The drop warns against assuming development performance transfers. Neither percentage measures independently validated human accuracy.'),
P('What was the hybrid classifier?','S'),P('An equal-weight combination of semantic-feature random forest predictions and word/character TF-IDF logistic regression predictions. Related stories stay grouped during development evaluation. The new 300 transfer references stay out of training.'),
P('What do the source percentages mean?','S'),P('They are the share of sampled titles matching fixed vocabulary. Colorado Sun housing: 30.9%; Hacker News: 10.1%; NPR: 13.2%. Inflation-rate wording: 2.7%, 20.3%, and 5.9%, respectively. These overlapping proxies do not describe all published coverage or readers\' beliefs.'),
P('Did the new 300-title export validate the model?','S'),P('No. It exports a selected subset of existing automated primary labels and wording proxies. It creates no independent reference or new model result. Keep that subset separate from the new 300-title classifier-transfer reference.')])
qa=[
('What exactly are the three required models?','M1 uses three economic indicators. M2 adds our original AI tone. M3 adds direct household and era controls. The controls-only comparison tests the contribution of tone separately.'),
('Why not call the 6.06 error a media success?','Controls without tone already achieve 5.82. Adding tone worsens that matched comparison. Comparing M1 with M3 changes too many variables to identify the media contribution.'),
('Does 98% agreement mean 98% accurate?','No. It means two same-session AI passes agree on 147 of 150 titles. They can share mistakes. Independent human accuracy is not established.'),
('Why is the gap not bias?','It is actual sentiment minus a prediction from a specific model. The model can omit real pressures, expectations, political differences, and measurement changes.'),
('Can negative news still be correct?','Yes. A report of job losses can accurately describe an adverse fact. Bias requires an appropriate benchmark for selection, context, or accuracy.'),
('What is R-squared versus RMSE?','R-squared describes fit to observed variation. Adjusted R-squared penalizes added predictors. Forecast RMSE measures mistakes on later observations. High fit can coexist with poor predictions.'),
('Why does the dictionary look better?','It improves one secondary dynamic point estimate. We retain that evidence, but do not select it after seeing outcomes or claim its measurement is validated.'),
('What does the presidency variable mean?','It is a calendar-era indicator. It does not measure anyone\'s party or isolate the effect of a president. Many policies and shocks change at the same time.'),
('What would make the project stronger?','Complete independent human labeling. Reconstruct release vintages. Improve balanced historical coverage. Freeze the next forecast before observing outcomes. Collect exposure or experimental evidence for causal claims.'),
('Can I say the assignment is fully complete?','No. The report and package explicitly disclose the missing independent human validation and incomplete vintage timing. Use the supplied forms to complete the human requirement, then rerun its evaluator and review the conclusions.')]
page('Questions to practise',[item for q,a in qa[:5] for item in [P(q,'S'),P(a)]])
page('Questions to practise, continued',[item for q,a in qa[5:] for item in [P(q,'S'),P(a)]])
parts.pop();SimpleDocTemplate(str(DEST/'Presentation_Speaking_Notes.pdf'),pagesize=(595.28,841.89),leftMargin=48,rightMargin=48,topMargin=43,bottomMargin=45).build(parts,onFirstPage=footer,onLaterPages=footer)
print('Script seconds:',sum(s[1] for s in S),'words:',sum(len(s[2].split()) for s in S))
