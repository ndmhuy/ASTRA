import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {parseCanonical,meaning,planMeaning,understandLocal,decisionMeaning,GOALS} from '../src/agent/intelligence.ts';
import {reduceSpec,specDraft,patchSpec,paramsForSpec} from '../src/agent/examSpec.ts';
import {buildParamsFromDraft} from '../src/agent/chatConfig.ts';
import {inspectQuestion} from '../src/agent/examActions.ts';
import {admit,execute} from '../src/agent/recipes.ts';
import {ExamSessions} from '../src/state/examSessions.ts';

const formats=JSON.parse(fs.readFileSync(new URL('../../eval/agent-semantic/local-catalog.fixture.json',import.meta.url)));
const frame=(goals,extra={})=>parseCanonical({schemaVersion:'astra-semantic-v3',dialogueAct:'REQUEST',goals,...extra});
const context={formats};

test('ordinary request grammar creates canonical meaning, pending subject is contextual',()=>{
  for(const message of ['soạn đề tiếng anh THPT cho tao','tạo đề toán thpt mới','Soạn đề Hóa THPT 20 câu, 30 phút']){
    const local=understandLocal(message,context);
    assert.equal(local.kind,'resolved',message);
    assert.equal(planMeaning(local.frame).kind,'intake');
    assert.equal(local.frame.goals[0].goal,'REQUEST_GENERATION');
  }
  assert.equal(understandLocal('Hóa nhé em',context).kind,'defer');
  const local=understandLocal('Hóa nhé em',{...context,intake:{sourceId:'prior',family:'thpt',missing:'subject',phase:'collecting'}});
  assert.equal(local.frame.goals[0].parameters.subject,'Hóa Học');
  assert.equal(local.frame.goals[0].goal,'PREPARE_EXAM');
});

test('information and scoped no-generation read do not become spec writes',()=>{
  for(const message of ['Đề Hóa THPT có bao nhiêu câu?','Đừng tạo đề, chỉ xem cấu trúc Hóa THPT']){
    const local=understandLocal(message,context);
    assert.equal(local.kind,'information',message);
    const plan=planMeaning(local.frame);
    assert.equal(plan.kind,'intake');assert.equal(plan.information,true);
  }
  const plan=planMeaning(frame([{goal:'REQUEST_GENERATION',parameters:{family:'thpt',subject:'Toán Học'}}],{dialogueAct:'QUESTION'}));
  assert.equal(plan.information,true);
  const followup=frame([{goal:'PREPARE_EXAM',parameters:{subject:'Hóa Học'}}],{dialogueAct:'INFORM'});
  assert.equal(planMeaning(followup).kind,'text');
  assert.equal(planMeaning(followup,undefined,'subject').kind,'intake');
});

test('unconsumed requirements, quotations, hypothetical and informal input remain honest',()=>{
  for(const message of ['Soạn đề Toán THPT có hình biểu đồ và 5 câu vận dụng cao','“Tạo đề Toán THPT”','Nếu đổi sang Anh thì sao?','Đừng sửa câu 4 nhưng đổi đáp án C'])assert.equal(understandLocal(message,context).kind,'defer');
  assert.equal(admit('đm cái đề này sao rồi mày').error,undefined);
});

test('one canonical registry covers local lifecycle and actual new capabilities',()=>{
  for(const goal of ['PAUSE_GENERATION','RESUME_GENERATION','STOP_ITEM_REGENERATION','EXPORT_DOCUMENT','LIST_DOCUMENTS','INSPECT_VERSION','RESTORE_VERSION','SAVE_EDITOR','APPROVE_QUESTION']){
    assert.equal(meaning(goal).goals[0].goal,goal);
  }
  assert.throws(()=>meaning('VERIFY_ANSWER',{workspaceId:'invented'}));
  assert.throws(()=>meaning('PREPARE_EXAM',{grade:13}));
  assert.throws(()=>meaning('EXPORT_ARTIFACT',{artifact:'teacher',format:'exe'}));
  assert.equal(frame([],{title:{bad:true}}).title,undefined);
});

test('spec retains requested mismatch while submission uses acknowledged real preset',()=>{
  const spec=reduceSpec(undefined,{mode:'request',family:'thpt',subject:'Hóa',count:20,minutes:30},formats,'u1');
  const draft=specDraft(spec,formats);
  assert.equal(spec.count,20);assert.equal(spec.minutes,30);
  assert.equal(draft.hasMismatch,true);
  const params=buildParamsFromDraft(draft,formats,[]);
  const format=formats.find(item=>item.id===spec.formatId);
  assert.equal(params.itemCount,format.totalQuestions);assert.equal(params.durationMinutes,format.durationMinutes);
  assert.equal(spec.count,20);
});

test('subject correction clears stale topic, retains difficulty/notes and invalidates phase',()=>{
  const before=reduceSpec(undefined,{mode:'request',family:'thpt',subject:'Toán',topic:'Hàm số',difficulty:'Nâng cao',requirements:'Giữ $x^2$ và hình',sourcePreference:'attachments'},formats,'u1');
  const after=reduceSpec({...before,phase:'confirmed'},{mode:'request',subject:'Sinh'},formats,'u2');
  assert.equal(after.topic,undefined);assert.equal(after.difficulty,'Nâng cao');
  assert.equal(after.requirements,'Giữ $x^2$ và hình');assert.equal(after.sourcePreference,'attachments');
  assert.equal(after.phase,'collecting');assert.deepEqual(after.sourceIds,['u1','u2']);
  assert.equal(after.provenance.subject,'u2');
  const clear=reduceSpec(after,{mode:'request',clear:'difficulty'},formats,'u3');
  assert.equal(clear.difficulty,undefined);
  const patch=patchSpec(after,{extraNotes:'Giữ nguyên (a+b)^2'},formats);
  assert.ok(buildParamsFromDraft(specDraft(patch,formats),formats,[]).prompt.includes('(a+b)^2'));
});

test('unsupported Literature preserves the requested subject without math substitution',()=>{
  const spec=reduceSpec(undefined,{mode:'request',family:'thpt',subject:'Ngữ Văn'},formats,'u1');
  assert.equal(spec.subject,'Ngữ Văn');assert.equal(spec.formatId,undefined);
});

test('scoped exclusion permits opening B, conflicting writes on same item never execute',()=>{
  const valid=planMeaning(frame([{goal:'OPEN_WORKSPACE',parameters:{title:'A'},prohibited:true},{goal:'OPEN_WORKSPACE',parameters:{title:'B'}}]));
  assert.deepEqual(valid.intents,[{id:'OPEN_SESSION',args:{title:'B'}}]);
  const conflict=planMeaning(frame([{goal:'EDIT_QUESTION',parameters:{number:4},prohibited:true},
    {goal:'FILL_EDITOR',parameters:{number:4,field:'key',value:'C'}}]));
  assert.equal(conflict.kind,'text');
  const read=planMeaning(frame([{goal:'READ_PROGRESS',parameters:{}}],{constraints:['NO_GENERATION']}));
  assert.equal(read.kind,'task');
  assert.equal(planMeaning(frame([{goal:'READ_PROGRESS',parameters:{}}],{dialogueAct:'QUESTION'})).kind,'task');
});

test('selected input sources cannot cross workspace or disappear silently at submission',()=>{
  const spec=reduceSpec(undefined,{mode:'request',family:'thpt',subject:'Toán',sourcePreference:'attachments'},formats,'u1');
  assert.match(paramsForSpec(spec,formats,[]).error,/tài liệu/);
  const doc={id:'local-doc',filename:'fixture.txt'};
  assert.equal(paramsForSpec({...spec,documentIds:['foreign-doc']},formats,[doc]).params,undefined);
  assert.deepEqual(paramsForSpec({...spec,documentIds:['local-doc']},formats,[doc]).params.uploadedFiles,['local-doc']);
  assert.deepEqual(paramsForSpec({...spec,sourcePreference:'no_web'},formats,[]).params.uploadedFiles,[]);
  const cleared=patchSpec(spec,{formatId:undefined},formats);
  assert.equal(cleared.formatId,undefined);
});

test('fresh AI and NO_WEB restrictions are enforced before dispatch',()=>{
  assert.equal(planMeaning(frame([{goal:'VERIFY_ANSWER',parameters:{number:5}}],{constraints:['NO_GENERATION']})).kind,'text');
  assert.equal(planMeaning(frame([{goal:'VERIFY_ANSWER',parameters:{number:5}}],{dialogueAct:'QUESTION'})).kind,'text');
  const plan=planMeaning(frame([{goal:'PREPARE_PRACTICE',parameters:{topic:'SAT Math',count:15,sourcePreference:'web'}}],{constraints:['NO_WEB']}));
  assert.equal(plan.parameters.sourcePreference,'no_web');
  const attached=planMeaning(frame([{goal:'PREPARE_PRACTICE',parameters:{topic:'SAT Math',sourcePreference:'attachments'}}],{constraints:['NO_WEB']}));
  assert.equal(attached.parameters.sourcePreference,'attachments');
  const direct=understandLocal('Tìm đề SAT Math 15 câu 25 phút',context);
  assert.equal(direct.frame.goals[0].goal,'PREPARE_PRACTICE');
  assert.equal(direct.frame.goals[0].parameters.count,15);
  assert.equal(direct.frame.goals[0].parameters.topic,'SAT Math');
  assert.equal(direct.frame.goals[0].parameters.sourcePreference,'web');
  assert.equal(understandLocal('Tạo đề SAT Math có ngữ cảnh trường học',context).kind,'defer');
});

test('conflicting coalesced intake slots clarify rather than last-write-wins',()=>{
  assert.equal(planMeaning(frame([{goal:'PREPARE_EXAM',parameters:{subject:'Sinh'}},{goal:'REQUEST_GENERATION',parameters:{subject:'Toán'}}])).kind,'text');
  assert.equal(planMeaning(frame([{goal:'PREPARE_EXAM',parameters:{subject:'Sinh'}},{goal:'REQUEST_GENERATION',parameters:{family:'thpt'}}])).kind,'intake');
});

test('source-linked references are bounded and explicit targets cannot be overwritten',()=>{
  const recent={number:5,part:'P2'};
  assert.equal(planMeaning(frame([{goal:'VERIFY_ANSWER',parameters:{number:4},reference:'previous'}]),recent).kind,'text');
  assert.equal(planMeaning(frame([{goal:'VERIFY_ANSWER',parameters:{},reference:'previous'}])).kind,'text');
  assert.equal(planMeaning(frame([{goal:'VERIFY_ANSWER',parameters:{},reference:'previous'}]),recent).intents[0].args.number,5);
  assert.equal(planMeaning(frame([{goal:'OPEN_WORKSPACE',parameters:{title:'B'}},{goal:'EDIT_QUESTION',parameters:{},reference:'previous'}]),recent).kind,'text');
});

test('stored true-false subitem and metadata never call an inference provider',()=>{
  const q={id:5,stableId:'P2-05',part:'P2',examRevision:4,stem:'Fixture',key:'ĐSĐS',explanation:'stored',
    statements:[{text:'a',answer:true,solution:'a stored'},{text:'b',answer:false,solution:'b stored'}],answerCheck:'matched',questionApproval:{revision:4}};
  const session={status:'complete',package:{revision:4},questions:[q,{...q,stableId:'P1-05',part:'P1'}]};
  assert.equal(inspectQuestion(session,{number:5}).status,'failed');
  assert.match(inspectQuestion(session,{number:5,part:'P2',subItem:'b'}).text,/Sai/);
  assert.match(inspectQuestion(session,{number:5,part:'P2',aspect:'approval'}).text,/đã được/);
  assert.match(inspectQuestion(session,{number:5,part:'P2',aspect:'verification'}).text,/Chưa gọi/);
});

test('ordered workspace/question plan resolves question after navigation, stops at confirmation',async()=>{
  const plan=planMeaning(frame([{goal:'OPEN_WORKSPACE',parameters:{title:'Hóa'}},{goal:'EDIT_QUESTION',parameters:{number:2,part:'P2'}},{goal:'VERIFY_ANSWER',parameters:{number:2,part:'P2'}}]));
  const seen=[];let workspace='old';
  const runtime={binding:()=>workspace,dispatch:async intent=>{
    if(intent.id==='OPEN_SESSION'){workspace='chemistry';return {status:'succeeded',text:'opened',expectedAfter:workspace};}
    seen.push([workspace,intent.id]);return {status:intent.id==='VERIFY_QUESTION'?'pending':'succeeded',text:'observed'};
  }};
  const receipts=await execute(plan.intents,runtime,'old',()=>true);
  assert.deepEqual(seen.map(item=>item[0]),['chemistry','chemistry']);assert.equal(receipts.at(-1).status,'pending');
});

test('all registry capability bindings exist in the real adapter',()=>{
  const app=fs.readFileSync(new URL('../src/App.tsx',import.meta.url),'utf8');
  for(const [name,definition] of Object.entries(GOALS)){
    if(definition.resolver==='capability')assert.ok(app.includes(`case '${definition.capability}'`),name);
  }
  assert.ok(!app.includes('applyInlineDraft'));
  assert.ok(!app.includes('mayDispatch('));
});

test('legacy selection is bridged through actual catalog data without exposing execution IDs',()=>{
  const legacy={kind:'task',intents:[{id:'SELECT_FORMAT',args:{format:'thpt-math'}}]};
  assert.equal(decisionMeaning(legacy),undefined);
  const converted=decisionMeaning(legacy,formats);
  assert.equal(converted.goals[0].goal,'PREPARE_EXAM');
  assert.equal(converted.goals[0].parameters.subject,'Toán Học');
  assert.equal(converted.goals[0].parameters.format,undefined);
  assert.equal(decisionMeaning({...legacy,intents:[{id:'SELECT_FORMAT',args:{format:'invented'}}]},formats),undefined);
  const detail=decisionMeaning({kind:'task',intents:[{id:'FORMAT_DETAILS',args:{}}]},formats,{formatId:'thpt-math'});
  assert.equal(planMeaning(detail).information,true);
  assert.equal(decisionMeaning({kind:'temporarily_unavailable',intents:[],reasonCode:'schema'},formats),undefined);
});

test('moving a newly resolved exam request clears the previous paper reference and preserves that job',()=>{
  const saved=JSON.stringify([{id:'source',title:'old paper',mode:'custom',status:'complete',createdAt:'2026-11-28T00:00:00Z',
    jobId:'old-job',package:{revision:3},questions:[],draft:'',messages:[{id:'turn',role:'user',content:'new request',timestamp:'2026-11-28T00:00:00Z',examVersion:{jobId:'old-job',revision:3}}]}]);
  const memory=new Map([['astra.sessions.v1',saved]]);
  globalThis.localStorage={getItem:key=>memory.get(key)??null,setItem:(key,value)=>memory.set(key,value)};
  try{
    const store=new ExamSessions({});
    const target=store.create('custom');
    assert.equal(store.moveUserTurn('source',target,'turn'),true);
    const original=store.getSnapshot().find(item=>item.id==='source');
    const next=store.getSnapshot().find(item=>item.id===target);
    assert.equal(original.jobId,'old-job');assert.equal(original.package.revision,3);assert.equal(original.messages.length,0);
    assert.equal(next.jobId,null);assert.equal(next.messages[0].examVersion,null);assert.equal(next.messages[0].id,'turn');
    store.dispose();
  }finally{delete globalThis.localStorage;}
});
