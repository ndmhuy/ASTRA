// Cost-free real React + HTTP-boundary test. Run Vite, then:
// node astra-frontend/tests/browserActions.mjs
// Local tooling: npm install --prefix tmp/browser-tooling playwright-core
import { chromium } from '../../tmp/browser-tooling/node_modules/playwright-core/index.mjs';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const format = JSON.parse(readFileSync(new URL('../../src/exam_baseline/resources/exam_formats/thpt_math_v1.json', import.meta.url), 'utf8'));
const question = { id: 1, stableId: 'P1-1', stem: 'Synthetic: 1+1?', choices: { A:'2',B:'3',C:'4',D:'5' }, key:'A', explanation:'Synthetic explanation', status:'VERIFIED', topic:'test', level:'NHAN_BIET' };
const session = { id:'fixture', title:'Synthetic exam', mode:'custom', status:'complete', createdAt:'2026-11-19T00:00:00Z', messages:[], questions:[question], draft:'', jobId:'fixture', agentNotes:[], previousCount:1, meta:{title:'Synthetic exam',subject:'Math',duration:90,completedCount:1,totalCount:1}, package:{examId:'fixture',revision:1,contentHash:'a'.repeat(64),approved:false,questions:[question]}, preview:{status:'unavailable',revision:1,contentHash:'a'.repeat(64)} };
const browser = await chromium.launch({ channel:'chrome', headless:true });
try {
  const page = await browser.newPage({ reducedMotion:'reduce' });
  await page.addInitScript(s => localStorage.setItem('astra.sessions.v1',JSON.stringify([s])), session);
  await page.route('**/*', async route => {
    const url=route.request().url();
    if(url.includes('/agent/session')) return route.fulfill({json:{token:'offline-test-only'}});
    if(url.includes('/agent/interpret')) {
      const body=route.request().postDataJSON(), ctx=body.context;
      const mode=body.message==='Quay lại đề'?'paper':'review';
      const specs=body.message==='Thiết lập trước khi tạo'
        ? [['ui.exam.open_setup',{}],['ui.exam.configure_setup',{formatId:format.id,prompt:'Synthetic intake draft'}]]
        : [['ui.exam.view_mode',{mode}]];
      if(body.message.includes('câu này')) specs.push(['ui.question.focus',{questionId:1}]);
      assert.deepEqual(ctx.capabilities.find(c=>c.id==='ui.exam.view_mode').parameterSchema.mode,['paper','review','pdf']);
      return route.fulfill({json:{turnId:body.turnId,provider:'offline',knowledgeStatus:'verified_ui_registry_only',decisions:specs.map(([capabilityId,params])=>({kind:'propose_ui_action',text:'Offline test action',actionId:crypto.randomUUID(),capabilityId,params,target:{},expectedStateVersion:ctx.stateVersion}))}});
    }
    if(url.includes('/api/exam-formats')) return route.fulfill({json:{formats:[format]}});
    if(url.includes('/api/')) return route.fulfill({status:503,json:{error:{code:'offline_fixture'}}});
    return route.continue();
  });
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:5173');
  await page.locator('.sidebar-exam').click();
  const composer=page.locator('.workspace-composer-slot textarea');
  for(const text of ['Tôi muốn xem đáp án','Quay lại đề','Cho xem đáp án câu này']) {
    await composer.fill(text); await composer.press('Enter');
    const mode=text==='Quay lại đề'?'paper':'review';
    await page.waitForFunction(mode=>document.querySelectorAll('.view-switch button')[mode==='review'?1:0]?.getAttribute('aria-pressed')==='true',mode);
    await page.waitForFunction(()=>!document.querySelector('.workspace-composer-slot textarea').disabled);
  }
  assert.equal(await page.locator('.answer-label').isVisible(),true);
  assert.equal(await page.locator('#question-1').getAttribute('class'),'agent-question-focus');
  const task=await page.evaluate(()=>JSON.parse(localStorage.getItem('astra.sessions.v1'))[0].agentTask);
  assert.equal(task.taskStatus,'completed'); assert.equal(task.completedSteps.length,2);
  assert.equal(task.lastExecutionReceipt.status,'success'); assert.deepEqual(errors,[]);
  await composer.fill('Thiết lập trước khi tạo'); await composer.press('Enter');
  await page.waitForFunction(()=>JSON.parse(localStorage.getItem('astra.sessions.v1'))[0].agentTask?.taskStatus==='awaiting_confirmation');
  assert.equal(await page.locator('[role="dialog"] input[type="radio"]:checked').count(),1);
  const setupTask=await page.evaluate(()=>JSON.parse(localStorage.getItem('astra.sessions.v1'))[0].agentTask);
  assert.equal(setupTask.completedSteps.length,2);
  assert.equal(setupTask.lastExecutionReceipt.status,'success');
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({browser:'chrome',turns:4,answers:'passed',questionFocus:'passed',setup:'awaiting_confirmation',setupReceipts:2,liveCalls:0}));
} finally { await browser.close(); }
