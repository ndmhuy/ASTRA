"""Separate a named misconception from a distractor that also avoids wording giveaways."""
from common import *
import collections

def attach(result):
 from file_matching import ascii_fold
 for comparison in result['metrics']['answer_comparisons']:
  comparison['same_answer']=ascii_fold(str(comparison['published'])).strip().upper()==ascii_fold(str(comparison['independent'])).strip().upper() if comparison.get('sub') is not None else comparison['same_literal']
 comparisons={(r['part'],r['idx']):r for r in result['metrics']['answer_comparisons'] if r.get('sub') is None};counts=collections.Counter()
 for question in result['rows']:
  comparison=comparisons.get((question['part'],question['idx']))
  for option in question.get('alternatives') or []:
   if comparison and option['label']==comparison['published']:continue
   if not comparison or not comparison.get('same_literal') or comparison.get('confidence') not in ['high','medium']:counts['unverified']+=1;continue
   linked=option.get('identifiable_error');giveaway=option.get('wording_eliminable')
   if type(linked) is not bool or type(giveaway) is not bool:counts['unverified']+=1;continue
   counts['judged']+=1
   if linked and not giveaway:counts['qualified']+=1
   else:counts['not_qualified']+=1
   if linked and giveaway:counts['linked_but_wording_eliminable']+=1
 result['metrics']['distractor_quality']={**dict(counts),'qualified_share_among_judged':counts['qualified']/counts['judged'] if counts['judged'] else None,'criterion':'Confirmed independent answer agrees with key; model identifies a plausible misconception AND does not flag wording elimination. This remains model judgement, not empirical student-error frequency.'}
 return result
