import test from 'node:test';
import assert from 'node:assert/strict';
import {parseCanonical,planMeaning,understandLocal} from '../src/agent/intelligence.ts';
import {workspaceDescription} from '../src/agent/workspaceFacts.ts';
import {statusText} from '../src/agent/examActions.ts';
import {retrievedContext} from '../src/agent/memory.ts';
import {liveStatusText,parseLiveState} from '../src/agent/liveState.ts';

const running={id:'fixture',title:'Đề 1 · Từ mẫu',mode:'template',status:'generating',messages:[],questions:[],draft:'',jobId:'job',generationId:'job',meta:{subject:'Vật Lý',duration:50,totalCount:28,completedCount:3},
  lastParams:{subject:'Vật Lý',grade:12,examType:'THPT_STANDARD',formatId:'thpt-physics',itemCount:28,durationMinutes:50,prompt:'Chuyển động thẳng',uploadedFiles:[]},
  progress:{status:'running',statusMessage:'Đang soạn câu hỏi',completedItems:3,totalItems:28}};

test('template form without intake supplies actual subject, count, time and requirements',()=>{
  const text=workspaceDescription(running);
  assert.match(text,/Vật Lý THPT/);assert.match(text,/28 câu/);assert.match(text,/50 phút/);
  const context=retrievedContext(running,'new','đang làm đề gì');
  assert.match(context.facts.join(' '),/Chuyển động thẳng/);
  assert.match(statusText(running),/Vật Lý THPT[\s\S]*3\/28/);
});

test('backend facts distinguish completion, failure and an older retained artifact',()=>{
  const base={title:'Đề 1',subject:'Vật Lý',format:'thpt-physics',count:28,minutes:50,completed:3,lifecycle:'running',artifactAvailable:false,approved:false};
  assert.match(liveStatusText(base),/Đang soạn đề.*3\/28/);
  assert.match(liveStatusText({...base,lifecycle:'completed',completed:28}),/Đã soạn xong 28 câu.*chờ giáo viên duyệt/);
  assert.match(liveStatusText({...base,lifecycle:'failed',artifactAvailable:true}),/gặp lỗi.*Bản đề đã lưu trước vẫn được giữ/);
  const completed={...running,status:'complete',questions:[],progress:{...running.progress,status:'completed',completedItems:28}};
  assert.match(statusText(completed),/Đã soạn xong 28 câu.*chờ giáo viên duyệt/);
});

test('completion statements and direct status questions are reads, never generation or approval',()=>{
  for(const text of ['mày đang tạo đề gì','Đang soạn đề nào?','Đề này đã soạn xong rồi','đề này xong chưa?']){
    const local=understandLocal(text,{formats:[]});
    assert.notEqual(local.kind,'defer',text);
    const plan=planMeaning(local.frame);
    assert.equal(plan.kind,'task',text);
    assert.deepEqual(plan.intents.map(i=>i.id),['STATUS']);
  }
  assert.equal(understandLocal('mày đang tạo đề gì',{formats:[]}).frame.goals[0].parameters.scope,'active');
  assert.equal(understandLocal('Nếu đề xong rồi thì xuất luôn nhé',{formats:[]}).kind,'defer');
});

test('conversation has a bounded reply while statements cannot become destructive operations',()=>{
  const frame=parseCanonical({schemaVersion:'astra-semantic-v3',dialogueAct:'CONVERSATION',reply:'Bạn cứ xem lại đề, mình sẵn sàng hỗ trợ.',goals:[]});
  assert.equal(planMeaning(frame).text,frame.reply);
  const statement=parseCanonical({schemaVersion:'astra-semantic-v3',dialogueAct:'INFORM',goals:[{goal:'REQUEST_GENERATION',parameters:{}}]});
  assert.equal(planMeaning(statement).kind,'text');
  assert.throws(()=>parseCanonical({...frame,reply:'x'.repeat(1201)}),/semantic_reply/);
  assert.equal(planMeaning(understandLocal('Cảm ơn em',{formats:[]}).frame).kind,'text');
});

test('malformed state cannot masquerade as an approved/completed exam',()=>{
  const data={schemaVersion:'astra-workspace-state-v1',observedAt:'2026-11-28T00:00:00Z',active:[],activeCount:0,current:{title:'Fixture',lifecycle:'completed',completed:28,artifactAvailable:true,approved:false}};
  assert.equal(parseLiveState(data).current.approved,false);
  assert.throws(()=>parseLiveState({...data,current:{...data.current,approved:'false'}}),/live_state_contract/);
  assert.throws(()=>parseLiveState({...data,current:{...data.current,lifecycle:'invented'}}),/live_state_contract/);
});

test('natural variants reuse the paper navigation without calling the interpreter', () => {
  const context = {formats: []};
  for (const message of ['xem đề thi', 'tao muốn xem đề thi', 'mình muốn xem lại đề thi này', 'cho tao mở bản đề thi nhé']) {
    const result = understandLocal(message, context);
    assert.notEqual(result.kind, 'defer', message);
    assert.deepEqual(planMeaning(result.frame), {kind: 'task', intents: [{id: 'SET_VIEW', args: {view: 'paper'}}]});
  }
  const history = understandLocal('tôi muốn xem lịch sử đề này', context);
  assert.deepEqual(planMeaning(history.frame).intents, [{id: 'OPEN_HISTORY', args: {}}]);
  assert.equal(understandLocal('tôi muốn xem đề thi và duyệt luôn', context).kind, 'defer');
  assert.equal(understandLocal('xem đáp án câu 0', context).kind, 'defer');
});

test('ETA follow-ups read real state and distinguish saved items from a finished exam', () => {
  for (const message of ['khi nào xong', 'bao giờ mới xong đề', 'còn lâu không?']) {
    const result = understandLocal(message, {formats: []});
    assert.equal(result.kind, 'information', message);
    assert.deepEqual(planMeaning(result.frame).intents, [{id: 'STATUS', args: {estimate: true}}]);
  }
  const state = {
    title: 'Đề 1', subject: 'Địa Lý', count: 28, minutes: 50, completed: 28, lifecycle: 'running',
    stage: 'solver', artifactAvailable: false, approved: false,
  };
  assert.match(liveStatusText(state, true), /Đang giải kiểm tra đáp án.*28\/28.*vẫn đang được xử lý.*Chưa có ước lượng/);
  assert.match(liveStatusText({...state, estimatedSecondsLeft: 70}, true), /khoảng 2 phút/);
  assert.match(liveStatusText({...state, lifecycle: 'completed'}, true), /Đã soạn xong 28 câu/);
});

test('general product questions have a short local answer', () => {
  const result = understandLocal('cái app này làm được gì', {formats: []});
  assert.equal(result.kind, 'information');
  const plan = planMeaning(result.frame);
  assert.equal(plan.kind, 'text');
  assert.match(plan.text, /soạn đề theo mẫu/);
  assert.ok(plan.text.length < 240);
});
