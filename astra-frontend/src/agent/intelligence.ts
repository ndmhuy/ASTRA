import registry from '../../../src/exam_baseline/resources/agent/registry-v3.json' with { type: 'json' };
import domain from '../../../src/exam_baseline/resources/agent/domain.json' with { type: 'json' };
import type { Decision, ExamIntake, Intent } from './contracts.ts';
import { validIntent } from './contracts.ts';
import type { Intake } from './intake.ts';
import type { ExamFormat } from '../types/exam.ts';
import { fastRoute } from './recipes.ts';
import { fold } from './language.ts';
import { polite } from './local.ts';
import { shortSubjectIntake, mentionedFamilies, matchAdjacentTopic, familyFor } from './knowledge.ts';
import { sectionId } from './examActions.ts';

export const SEMANTIC_VERSION = registry.schemaVersion;
export const GOALS = registry.goals;
export const PRACTICE_LIMITS = registry.limits.practice;
export type GoalId = keyof typeof GOALS;
type Slots = Intent['args'];
export type Goal = { goal: GoalId; parameters: Slots; reference?: 'current' | 'previous' | 'recent'; prohibited?: boolean };
export type Frame = { schemaVersion: 'astra-semantic-v3'; dialogueAct: 'REQUEST' | 'INFORM' | 'QUESTION' | 'GUIDANCE' |
  'CORRECT' | 'CANCEL' | 'CONFIRM' | 'CONVERSATION' | 'AMBIGUOUS' | 'UNSUPPORTED' | 'OUT_OF_SCOPE';
  goals: Goal[]; constraints: Array<'NO_GENERATION' | 'NO_EXECUTION' | 'CONDITIONAL' | 'NEGATED' | 'CONTRADICTORY' | 'NO_WEB'>; title?: string };
const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const acts = ['REQUEST','INFORM','QUESTION','GUIDANCE','CORRECT','CANCEL','CONFIRM','CONVERSATION','AMBIGUOUS','UNSUPPORTED','OUT_OF_SCOPE'];
const constraints = ['NO_GENERATION','NO_EXECUTION','CONDITIONAL','NEGATED','CONTRADICTORY','NO_WEB'];

export function parseCanonical(value: unknown): Frame {
  if (!record(value) || value.schemaVersion !== SEMANTIC_VERSION || !acts.includes(String(value.dialogueAct)) ||
      Object.keys(value).some(key => !['schemaVersion','dialogueAct','goals','constraints','title'].includes(key))) throw new Error('agent_semantic_contract');
  const goals = value.goals ?? [], bounds = value.constraints ?? [];
  if (!Array.isArray(goals) || goals.length > registry.limits.goalsPerTurn || !Array.isArray(bounds) || bounds.length > 6 || bounds.some(item=>!constraints.includes(item))) throw new Error('agent_semantic_contract');
  const normalized = goals.map((item): Goal => {
    if (!record(item) || !Object.hasOwn(GOALS,String(item.goal)) ||
        Object.keys(item).some(key=>!['goal','parameters','reference','prohibited'].includes(key)) ||
        (item.reference != null && !['current','previous','recent'].includes(String(item.reference))) ||
        (item.prohibited != null && typeof item.prohibited !== 'boolean')) throw new Error('agent_semantic_goal');
    const goal = item.goal as GoalId, parameters = item.parameters ?? {};
    const rules: Record<string,string> = GOALS[goal].parameters;
    if (!record(parameters) || Object.entries(parameters).some(([key,val])=> {
      const rule = rules[key]?.replace(/\?$/,'');
      const limit = (registry.parameterBounds as Record<string,{maxLength?:number;maximum?:number}>)[key];
      if (!rule) return true;
      if (rule.includes('|')) return typeof val !== 'string' || !rule.split('|').includes(val);
      if (rule==='string') return typeof val!=='string' || [...val].length<1 || [...val].length>(limit?.maxLength??600);
      if (rule==='integer') return typeof val!=='number' || !Number.isInteger(val) || val<1 || val>(limit?.maximum??999);
      return typeof val!=='boolean';
    })) throw new Error('agent_semantic_parameter');
    return {goal,parameters:parameters as Slots,...(item.reference?{reference:item.reference as Goal['reference']}:{ }),...(item.prohibited?{prohibited:true}:{})};
  });
  const title = typeof value.title==='string' ? value.title.replace(/[\p{Cc}\p{Cf}]/gu,' ').replace(/\s+/g,' ').trim() : '';
  return {schemaVersion:'astra-semantic-v3',dialogueAct:value.dialogueAct as Frame['dialogueAct'],goals:normalized,constraints:bounds,
    ...(title && [...title].length<=60?{title}:{})};
}

export function meaning(goal: GoalId, parameters: Slots = {}, act: Frame['dialogueAct'] = 'REQUEST'): Frame {
  return parseCanonical({schemaVersion:SEMANTIC_VERSION,dialogueAct:act,goals:[{goal,parameters}]});
}

// Legacy results are explicitly bridged by meaning, never by re-parsing the utterance.
export function decisionMeaning(decision: Decision, formats:ExamFormat[]=[], current?:Intake): Frame | undefined {
  if (decision.intake) {
    const {mode,...parameters} = decision.intake;
    return meaning(mode==='request'?'PREPARE_EXAM':'READ_EXAM_STRUCTURE',parameters,mode==='request'?'REQUEST':'QUESTION');
  }
  if(decision.guidance) return meaning('CAPABILITY_INQUIRY',{},'QUESTION');
  if(decision.kind!=='task') return;
  const goals = decision.intents.map(intent=> {
    if(['SELECT_FORMAT','FORMAT_DETAILS','PREPARE_GENERATION'].includes(intent.id)){
      const selected=formats.find(format=>format.available&&format.id===(intent.args.format??current?.formatId));
      if(!selected)return null;
      return {goal:intent.id==='FORMAT_DETAILS'?'READ_EXAM_STRUCTURE':intent.id==='PREPARE_GENERATION'?'REQUEST_GENERATION':'PREPARE_EXAM',
        parameters:{family:familyFor(selected),subject:selected.subjects[0],...(intent.args.topic?{topic:intent.args.topic}:{})}};
    }
    const entry = Object.entries(GOALS).find(([,def])=>'capability' in def && def.capability===intent.id);
    return entry ? {goal:entry[0],parameters:intent.args} : null;
  });
  if(goals.some(item=>!item)) return;
  return parseCanonical({schemaVersion:SEMANTIC_VERSION,dialogueAct:'REQUEST',goals});
}

export type LocalResult = {kind:'resolved'|'information'|'ambiguity';frame:Frame} | {kind:'defer'};
export function understandLocal(message: string, context: {formats:ExamFormat[];intake?:Intake}): LocalResult {
  const text = polite(message).replace(/^(?:co|thay|toi|minh|tao|tui|em) (?:muon|can) /,'');
  const done = (frame:Frame):LocalResult=>({kind:frame.dialogueAct==='QUESTION'?'information':frame.dialogueAct==='AMBIGUOUS'?'ambiguity':'resolved',frame});
  // Quoted, hypothetical and conflicting intent belongs to the configured interpreter.
  if(/["“”«»`]/.test(message) || /\b(?:neu|gia su|nhung|sau do|dong thoi)\b/.test(text)) return {kind:'defer'};
  if(/^(?:dong y|xac nhan|ok)$/.test(text)) return done(parseCanonical({schemaVersion:SEMANTIC_VERSION,dialogueAct:'CONFIRM'}));
  if(/^(?:huy tac vu|huy yeu cau|thoi dung lai)$/.test(text)) return done(parseCanonical({schemaVersion:SEMANTIC_VERSION,dialogueAct:'CANCEL'}));
  const noGeneration = /^(?:dung|khong|chua) (?:tao|sinh) de[,;]? (?:co |toi |minh )?chi (?:muon )?/.test(text);
  const reading = noGeneration ? text.replace(/^(?:dung|khong|chua) (?:tao|sinh) de[,;]? (?:co |toi |minh )?chi (?:muon )?/,'') : text;
  if (!noGeneration && (/đừng/iu.test(message) || /\b(?:khong|ko|chua)\b/.test(text))) {
    if(/^dung han (?:tao|sinh) de,? khong can tiep tuc$/.test(text)) return done(meaning('CANCEL_GENERATION'));
    return {kind:'defer'};
  }
  const subject = shortSubjectIntake(text.replace(/\s+(?:nhe|nha)(?: em)?$/,''),context.formats);
  if(subject && context.intake?.missing==='subject') return done(meaning('PREPARE_EXAM',{subject:subject.subject!}));
  if(subject) return {kind:'defer'};
  const structure = /^(?:xem cau truc|cau truc|de .* (?:co )?bao nhieu cau|thpt .*bao nhieu cau)/.test(reading);
  const request = reading.match(/^(tao|soan|ra|gen|chuan bi|chon|doi sang)(?: (?:mot|1))? (?:de(?: thi)? ?)?(.*)$/);
  const practice=matchAdjacentTopic(message);
  const practiceRequest=reading.match(/^(tim(?: kiem)?|tao|soan|chuan bi|luyen)(?: (?:de|bai|tap))*\s+(.+)$/);
  if(practice && practiceRequest && !structure){
    let tail=practiceRequest[2];
    const parameters:Slots={topic:practice.label};
    for(const [slot,unit] of [['count','cau'],['minutes','phut']] as const){
      const pattern=new RegExp('\\b(\\d+)\\s*'+unit+'\\b');
      const match=tail.match(pattern);
      if(match){parameters[slot]=Number(match[1]);tail=tail.replace(pattern,' ');}
    }
    let matchedTopic=false;
    for(const term of practice.terms.slice().sort((a,b)=>b.length-a.length)){
      const escaped=fold(term).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
      const pattern=new RegExp('(^|\\s)'+escaped+'(?=\\s|$)','g');
      if(!matchedTopic&&pattern.test(tail)){parameters.topic=term;matchedTopic=true;}
      tail=tail.replace(pattern,' ');
    }
    if(tail.replace(/[,.;]/g,'').trim())return {kind:'defer'};
    if(practiceRequest[1].startsWith('tim'))parameters.sourcePreference='web';
    return done(meaning('PREPARE_PRACTICE',parameters));
  }
  if(structure || request) {
    const rawTail = request?.[2] ?? reading.replace(/^(?:xem cau truc|cau truc)\s*/, '').replace(/^(?:de )?/,'').replace(/\s+(?:co )?bao nhieu cau\??$/,'');
    let tail = rawTail;
    const parameters: Slots = {};
    const families = mentionedFamilies(tail);
    if(families.length>1) return {kind:'defer'};
    if(families.length) {
      parameters.family=families[0];
      for(const term of domain.families[families[0]].terms.slice().sort((a,b)=>b.length-a.length)) {
        const escaped=fold(term).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
        tail=tail.replace(new RegExp('(^|\\s)'+escaped+'(?=\\s|$)','g'),' ');
      }
    }
    for(const [slot,unit] of [['count','cau'],['minutes','phut'],['grade','lop']] as const) {
      const pattern = slot==='grade'?/\blop\s+(\d+)\b/:new RegExp('\\b(\\d+)\\s*'+unit+'\\b');
      const found=tail.match(pattern);
      if(found){parameters[slot]=Number(found[1]);tail=tail.replace(pattern,' ');}
    }
    if(/\b(?:moi|khac)\b/.test(tail)){parameters.fresh=true;tail=tail.replace(/\b(?:moi|khac)\b/g,' ');}
    tail=tail.replace(/\s+/g,' ').replace(/[,.;?]/g,'').trim();
    const selected=shortSubjectIntake(tail,context.formats)?.subject;
    if(tail && !selected) return {kind:'defer'};
    if(selected) parameters.subject=selected;
    const frame=meaning(structure?'READ_EXAM_STRUCTURE':request?.[1] && ['tao','soan','ra','gen'].includes(request[1])?'REQUEST_GENERATION':'PREPARE_EXAM',parameters,structure?'QUESTION':request?.[1]==='doi sang'?'CORRECT':'REQUEST');
    if(noGeneration) frame.constraints.push('NO_GENERATION');
    return done(frame);
  }
  const item = text.match(/^(?:dap an|loi giai|giai thich)(?: y ([abcd]))? cau (\d+)(?: phan ([\w -]+?))?(?: la gi)?\??$/);
  if(item) return done(meaning('INSPECT_QUESTION',{number:Number(item[2]),...(item[1]?{subItem:item[1]}:{}),...(item[3]?{part:sectionId(item[3])}:{}),aspect:/^(?:loi giai|giai thich)/.test(text)?'explanation':'answer'},'QUESTION'));
  const version=text.match(/^(xem|khoi phuc) phien ban (dau tien|truoc|\d+)$/);
  if(version) return done(meaning(version[1]==='xem'?'INSPECT_VERSION':'RESTORE_VERSION',/^\d+$/.test(version[2])?{version:Number(version[2])}:{relative:version[2]==='dau tien'?'initial':'previous'}));
  const exportArtifact=text.match(/^(?:tai|xuat) (?:dap an giao vien|ma tran)(?: dang)? (json|tex|pdf|docx|md)$/);
  if(exportArtifact) return done(meaning('EXPORT_ARTIFACT',{artifact:/dap an/.test(text)?'teacher':'matrix',format:exportArtifact[1]}));
  if(/^(?:chi )?dung (?:luot )?tao lai cau hoi$/.test(text)) return done(meaning('STOP_ITEM_REGENERATION'));
  if(/^(?:xem )?(?:trang thai|tien do) tao lai cau hoi$/.test(text)) return done(meaning('READ_ITEM_REGENERATION',{},'QUESTION'));
  if(/^(?:xem|liet ke) tai lieu(?: dinh kem)?$/.test(text)) return done(meaning('LIST_DOCUMENTS',{},'QUESTION'));
  if(/^(?:luu chinh sua|luu cau hoi)$/.test(text)) return done(meaning('SAVE_EDITOR'));
  const local=fastRoute(message);
  if(!local) return {kind:'defer'};
  if('text' in local) {
    if(/^(?:xin chao|chao(?: em| astra)?|hello|hi|cam on(?: em)?|thanks)$/.test(text)) return done(parseCanonical({schemaVersion:SEMANTIC_VERSION,dialogueAct:'CONVERSATION'}));
    if(/^(?:upload|dinh kem file|them tai lieu tham khao)$/.test(text)) return done(meaning('UPLOAD_GUIDANCE',{},'QUESTION'));
    return {kind:'defer'};
  }
  const candidate=decisionMeaning('intents' in local?{kind:'task',intents:local.intents}:'intake' in local?{kind:'answer',intents:[],intake:local.intake}:{kind:'clarify',intents:[]},context.formats,context.intake);
  if(!candidate) return {kind:'defer'};
  // A question about an operation must not be promoted to its execution.
  if(/\b(?:co the|duoc khong|tai sao|vi sao|lam sao|the nao)\b/.test(text) || message.trim().endsWith('?')) candidate.dialogueAct='QUESTION';
  if(candidate.goals[0]?.goal==='INSPECT_QUESTION' && /xem dap an/.test(text)) candidate.dialogueAct='QUESTION';
  return done(candidate);
}

export type Plan = {kind:'text';text:string} | {kind:'confirm'} | {kind:'cancel'} |
  {kind:'intake';proposal:ExamIntake;information:boolean} | {kind:'inspect';targets:Slots[]} |
  {kind:'task';intents:Intent[]} | {kind:'practice';parameters:Slots};
export function planMeaning(frame:Frame,recent?:{number:number;part?:string},missing?:Intake['missing']):Plan {
  const stop=(text:string):Plan=>({kind:'text',text});
  if(frame.constraints.some(item=>['NO_EXECUTION','CONDITIONAL','NEGATED','CONTRADICTORY'].includes(item))) return stop('Yêu cầu có điều kiện hoặc mâu thuẫn. Thầy cô muốn thực hiện bước nào? Em chưa thay đổi dữ liệu.');
  if(frame.dialogueAct==='CONFIRM') return {kind:'confirm'};
  if(frame.dialogueAct==='CANCEL') return {kind:'cancel'};
  if(['CONVERSATION','GUIDANCE'].includes(frame.dialogueAct)) return stop('Em có thể giúp chọn mẫu đề, xem đáp án đã lưu, quản lý tài liệu, phiên chạy và lịch sử. Thầy cô muốn làm việc gì trước?');
  if(['UNSUPPORTED','OUT_OF_SCOPE','AMBIGUOUS'].includes(frame.dialogueAct)||!frame.goals.length) return stop('Em cần biết mục tiêu hoặc đề/câu cụ thể. Thầy cô có thể hỏi cấu trúc mẫu đề, trạng thái, đáp án đã lưu hoặc nêu việc cần làm.');
  const excluded=frame.goals.filter(goal=>goal.prohibited);
  const goals=frame.goals.filter(goal=>!goal.prohibited);
  const signature=(value:Slots)=>JSON.stringify(Object.entries(value).sort(([a],[b])=>a.localeCompare(b)));
  if(goals.some(goal=>excluded.some(other=>(goal.goal===other.goal&&signature(goal.parameters)===signature(other.parameters))||
    (GOALS[goal.goal].effect!=='read'&&GOALS[other.goal].effect!=='read'&&goal.parameters.number!==undefined&&goal.parameters.number===other.parameters.number&&
      (!goal.parameters.part||!other.parameters.part||sectionId(String(goal.parameters.part))===sectionId(String(other.parameters.part))))))) return stop('Cùng một thao tác hoặc câu hỏi đang được yêu cầu sửa và bị cấm sửa. Thầy cô hãy làm rõ trước.');
  if(!goals.length)return stop('Đã giữ nguyên trạng thái theo yêu cầu.');
  const definitions=goals.map(goal=>GOALS[goal.goal]);
  const noAI=frame.constraints.includes('NO_GENERATION');
  if(noAI && definitions.some(def=>def.effect==='inference' && !['PREPARE_EXAM','REQUEST_GENERATION'].includes(goals[definitions.indexOf(def)].goal))) return stop('Yêu cầu không gọi AI đang có hiệu lực. Em chưa kiểm tra hay tạo lại nội dung.');
  const intake=goals.every(goal=>['PREPARE_EXAM','REQUEST_GENERATION','READ_EXAM_STRUCTURE'].includes(goal.goal));
  if(intake) {
    const parameters:Slots={};
    for(const item of goals) for(const [key,val] of Object.entries(item.parameters)) {
      if(parameters[key]!==undefined && parameters[key]!==val)return stop(`Các yêu cầu ${key} chưa thống nhất. Thầy cô muốn giữ giá trị nào?`);
      parameters[key]=val;
    }
    const information=frame.dialogueAct==='QUESTION'||goals.every(goal=>goal.goal==='READ_EXAM_STRUCTURE');
    if(!information&&frame.dialogueAct==='INFORM'&&!missing)return stop('Em đã ghi nhận thông tin. Thầy cô muốn xem cấu trúc hay chuẩn bị một đề mới? Chưa có bước cấu hình đang chờ để điền thông tin này.');
    return {kind:'intake',proposal:{mode:information?'structure':'request',...parameters,...(frame.constraints.includes('NO_WEB')&&parameters.sourcePreference!=='attachments'?{sourcePreference:'no_web'}:{})} as ExamIntake,information};
  }
  if(frame.dialogueAct==='QUESTION' && definitions.some(def=>def.effect!=='read')) return stop('Em chưa thực hiện thao tác. Thao tác này cần đúng đề/câu và xác nhận khi có sửa dữ liệu hoặc dùng AI.');
  if(definitions.some(def=>!def.dialogueActs.includes(frame.dialogueAct))) return stop('Thầy cô đang hỏi thông tin hay muốn thực hiện thao tác? Em chưa thay đổi dữ liệu.');
  if(goals.every(goal=>goal.goal==='INSPECT_QUESTION')) {
    const targets:Slots[]=[];
    for(const goal of goals) {
      if(goal.reference==='previous'||goal.reference==='recent') {
        if(!recent)return stop('Chưa có câu vừa xem còn hiệu lực. Hãy ghi số câu và phần thi.');
        if((goal.parameters.number!==undefined&&goal.parameters.number!==recent.number)||(goal.parameters.part!==undefined&&sectionId(String(goal.parameters.part))!==sectionId(recent.part??'')))return stop('Tham chiếu câu vừa xem không khớp số/phần đã nêu.');
        targets.push({...goal.parameters,...recent});
      } else targets.push(goal.parameters);
    }
    return {kind:'inspect',targets};
  }
  if(goals.length===1 && goals[0].goal==='PREPARE_PRACTICE')return frame.constraints.includes('NO_WEB')&&goals[0].parameters.sourcePreference!=='attachments'?{kind:'practice',parameters:{...goals[0].parameters,sourcePreference:'no_web'}}:{kind:'practice',parameters:goals[0].parameters};
  if(goals.some(goal=>goal.goal==='CAPABILITY_INQUIRY'))return stop('ASTRA hỗ trợ các mẫu trong danh mục thực tế, tài liệu đính kèm, đọc đáp án/lời giải đã lưu, sửa/kiểm tra/tạo lại câu, tạm dừng/tiếp tục cùng phiên, lịch sử và xuất bản đã duyệt. Việc kiểm tra hoặc sinh nội dung mới dùng AI và cần xác nhận.');
  const intents:Intent[]=[];
  for(const goal of goals) {
    const def=GOALS[goal.goal];
    if(!('capability' in def))return stop('Mục tiêu này cần làm rõ riêng trước khi điều khiển đề.');
    let args=goal.parameters;
    if(goal.reference==='previous'||goal.reference==='recent') {
      if(!recent||goals.some(item=>item.goal==='OPEN_WORKSPACE'))return stop('Hãy mở đề đích rồi chỉ rõ câu cần thao tác.');
      if((args.number!==undefined&&args.number!==recent.number)||(args.part!==undefined&&sectionId(String(args.part))!==sectionId(recent.part??'')))return stop('Số câu/phần thi không khớp tham chiếu câu vừa xem. Hãy chỉ rõ mục tiêu.');
      args={...args,...recent};
    }
    const intent={id:def.capability,args} as Intent;
    if(!validIntent(intent))return stop(`Cần bổ sung thông tin cho: ${def.meaning}.`);
    intents.push(intent);
  }
  return {kind:'task',intents};
}
