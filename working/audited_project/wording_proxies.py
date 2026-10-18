import re
import pandas as pd,numpy as np
PATTERNS={
 'prices':r'\b(inflation|prices?|cost of living|grocer\w*|gasoline|food costs?)\b',
 'labor':r'\b(jobs?|wages?|employment|unemployment|jobless|hiring|layoffs?|laid off|payrolls?|labor|labour)\b',
 'housing':r'\b(hous\w*|homes?|rents?|mortgages?|evictions?)\b',
 'growth':r'\b(gdp|econom\w*|recession|growth|consumer spending|retail sales)\b',
 'debt':r'\b(debt|credit cards?|loan payments?|delinquen\w*)\b',
 'policy':r'\b(tariffs?|tax\w*|federal reserve|interest rates?|(?-i:Fed)|government spending)\b',
 'level_frame':r'\b(high prices?|higher prices?|high costs?|higher costs?|cost of living|afford\w*|expensive|price levels?|record prices?|still high|remain\w* high|elevated prices?)\b',
 'rate_frame':r'\b(inflation|disinflation|deflation|prices? (?:rise|rose|rising|fall|fell|falling|increase|decrease|drop|climb)|price (?:growth|increases?|declines?))\b',
 'political_mention':r'\b(Trump|Biden|Democrat\w*|Republican\w*|White House|president\w*|Congress)\b',
 'blame_word':r'\b(blam\w*|fault|caus\w*|responsib\w*|hurt\w*|fail\w*|damage\w*)\b',
 'emotion_word':r'\b(crisis|panic|fear\w*|terrify\w*|disaster\w*|nightmare|pain\w*|anger|angry|outrag\w*|soar\w*|skyrocket\w*|plung\w*|crash\w*|suffer\w*|struggl\w*)\b'}
def operational(d):
 for k,v in PATTERNS.items():d[k]=d.title.str.contains(v,case=False,regex=True).astype(int)
 d['political_blame_proxy']=d.political_mention*d.blame_word
 d['dictionary_tone']=d.title.str.count(r'(?i)\b(improv\w*|recover\w*|rebound\w*|booming|gains?|strong|cool\w*|eas\w*)\b')-d.title.str.count(r'(?i)\b(recession|layoffs?|crisis|struggl\w*|surge\w*|soar\w*|skyrocket\w*|slump\w*|plung\w*|weak\w*|declin\w*)\b')
 d['dictionary_tone']=np.sign(d.dictionary_tone);return d
