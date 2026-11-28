import type { ExamIntake } from './contracts.ts';
import type { Intake } from './intake.ts';
import type { ExamFormat } from '../types/exam.ts';
import { familyFor, shortSubjectIntake } from './knowledge.ts';
import { buildParamsFromDraft, recomputeDraftStatus, type ChatConfigDraft } from './chatConfig.ts';
import type { InputDocument } from '../services/inputDocuments.ts';
import { fold } from './language.ts';

// This reducer owns the evolving spec. It accepts canonical slots, never raw text.
export function reduceSpec(previous:Intake|undefined, proposal:ExamIntake, formats:ExamFormat[], sourceId:string):Intake {
  const subject = proposal.subject ? shortSubjectIntake(proposal.subject,formats)?.subject ?? proposal.subject : undefined;
  const familyChanged=!!proposal.family && proposal.family!==previous?.family;
  const subjectChanged=!!subject && fold(subject)!==fold(previous?.subject??'');
  const base=proposal.fresh?undefined:previous;
  const next:Intake={...base,sourceId,sourceIds:[...new Set([...(base?.sourceIds??(base?[base.sourceId]:[])),sourceId])],
    phase:'collecting',validation:undefined,visible:true,
    family:proposal.family??base?.family,subject:subject??(familyChanged?undefined:base?.subject),
    topic:proposal.topic??(familyChanged||subjectChanged?undefined:base?.topic),
    provenance:{...base?.provenance}};
  for(const key of ['topic','difficulty','requirements','sourcePreference','count','minutes','grade'] as const) {
    if(proposal[key]!==undefined) Object.assign(next,{[key]:proposal[key]});
  }
  if(proposal.clear) {
    const key=proposal.clear==='sources'?'sourcePreference':proposal.clear;
    delete next[key];
  }
  for(const key of Object.keys(proposal)) if(key!=='mode') next.provenance![key]=sourceId;
  const available=formats.filter(format=>format.available);
  let candidates=available.filter(format=>(!next.family||familyFor(format)===next.family) &&
    (!next.subject||format.subjects.some(item=>fold(item)===fold(next.subject!))));
  if(next.family==='vact')candidates=available.filter(format=>familyFor(format)==='vact');
  const selected=candidates.length===1?candidates[0]:undefined;
  next.formatId=selected?.id; next.version=selected?.version;
  if(selected) {next.family=familyFor(selected);next.subject=selected.subjects[0];next.missing=undefined;}
  else next.missing=!next.family?'family':'subject';
  return next;
}

export function specDraft(spec:Intake|undefined,formats:ExamFormat[]):ChatConfigDraft|undefined {
  if(!spec?.visible)return;
  return recomputeDraftStatus({id:spec.sourceId,sourceMessageId:spec.sourceId,formatId:spec.formatId,family:spec.family,subject:spec.subject,
    requestedCount:spec.count,requestedMinutes:spec.minutes,requestedGrade:spec.grade,topic:spec.topic??'',difficulty:spec.difficulty??'',
    extraNotes:spec.requirements??'',limitations:[],needsClarification:[],applied:[],hasMismatch:false},formats);
}

export function patchSpec(spec:Intake,patch:Partial<ChatConfigDraft>,formats:ExamFormat[]):Intake {
  const selected=patch.formatId?formats.find(format=>format.id===patch.formatId&&format.available):undefined;
  const changed=!!selected && selected.id!==spec.formatId;
  return {...spec,phase:'collecting',validation:undefined,
    ...(selected?{formatId:selected.id,version:selected.version,family:familyFor(selected),subject:selected.subjects[0],missing:undefined}:{}),
    ...(Object.hasOwn(patch,'formatId')&&!selected?{formatId:undefined,version:undefined,subject:undefined,missing:'subject' as const}:{}),
    ...(changed?{topic:undefined}:{}),
    ...(patch.topic!==undefined?{topic:patch.topic}:{}),...(patch.difficulty!==undefined?{difficulty:patch.difficulty}:{}),
    ...(patch.extraNotes!==undefined?{requirements:patch.extraNotes}:{}),
    provenance:{...spec.provenance,...Object.fromEntries(Object.keys(patch).map(key=>[key,'manual-ui']))}};
}

export function paramsForSpec(spec:Intake|undefined,formats:ExamFormat[],documents:InputDocument[]) {
  const draft=specDraft(spec?{...spec,visible:true}:undefined,formats);
  if(!draft)return {error:'Chưa có cấu hình đề.'};
  const selected=spec?.documentIds?documents.filter(doc=>spec.documentIds!.includes(doc.id)):documents;
  if(spec?.documentIds?.some(id=>!documents.some(doc=>doc.id===id)))return {error:'Tài liệu đã chọn không còn gắn với đề này. Hãy chọn lại nguồn.'};
  if(spec?.sourcePreference==='attachments'&&!selected.length)return {error:'Yêu cầu chỉ dùng tài liệu đính kèm đang có hiệu lực. Hãy chọn tài liệu trước khi tạo đề.'};
  const params=buildParamsFromDraft(draft,formats,selected.map(doc=>doc.id));
  return params?{params}:{error:'Mẫu đề chưa khả dụng.'};
}

export function specSummary(spec:Intake|undefined):string[] {
  if(!spec)return [];
  return ['family','subject','topic','difficulty','requirements','sourcePreference','count','minutes'].flatMap(key=> {
    const value=spec[key as keyof Intake];return value===undefined?[]:[`${key}: ${String(value).slice(0,560)}`];
  });
}
