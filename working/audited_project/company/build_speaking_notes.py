from pathlib import Path
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root=Path(__file__).resolve().parents[3]
script=json.loads((Path(__file__).resolve().parent/'results_script.json').read_text())
pdfmetrics.registerFont(TTFont('Body','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('Heading','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
body=ParagraphStyle('Body',fontName='Body',fontSize=11,leading=15,spaceAfter=9,textColor=colors.HexColor('#1D2E3F'))
head=ParagraphStyle('Heading',fontName='Heading',fontSize=12,leading=16,spaceBefore=9,spaceAfter=5,keepWithNext=True,textColor=colors.HexColor('#007F78'))
title=ParagraphStyle('Title',fontName='Heading',fontSize=17,leading=22,spaceAfter=10,textColor=colors.HexColor('#142B42'))
parts=[Paragraph('Presentation script: results and interpretation',title)]
for i,(name,text) in enumerate(script,1):parts.extend([Paragraph('Slide '+str(i),head),Paragraph(text,body)])
def footer(c,d):
 c.setFont('Body',8);c.setFillColor(colors.HexColor('#64768A'));c.drawString(44,24,'Khushi Khanna / Speaking script');c.drawRightString(551,24,str(d.page))
SimpleDocTemplate(str(root/'company_final/Presentation_Speaking_Notes.pdf'),pagesize=(595.28,841.89),leftMargin=44,rightMargin=44,topMargin=36,bottomMargin=40).build(parts,onFirstPage=footer,onLaterPages=footer)
print('Words:',sum(len(text.split()) for _,text in script))
