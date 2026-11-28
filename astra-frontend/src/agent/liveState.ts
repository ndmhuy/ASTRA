/** One read-only state projection is shared by server-side Chat grounding and UI reads. */
export interface LiveWorkspace {
  title: string; lifecycle: string; subject?: string; format?: string; count?: number; minutes?: number;
  completed: number; stage?: string; requirements?: string; errorCode?: string;
  artifactAvailable: boolean; approved: boolean; revision?: number;
}
export interface LiveState {
  schemaVersion: 'astra-workspace-state-v1'; observedAt: string; current?: LiveWorkspace;
  active: LiveWorkspace[]; activeCount: number;
}
export function parseLiveState(value: unknown): LiveState {
  const record=(item:unknown):item is Record<string,unknown>=>!!item&&typeof item==='object'&&!Array.isArray(item);
  const integer=(item:unknown,optional=false)=>optional&&item===undefined||typeof item==='number'&&Number.isInteger(item)&&item>=0&&item<=9999;
  const workspace=(item:unknown)=>record(item)&&typeof item.title==='string'&&typeof item.lifecycle==='string'&&
    ['draft','queued','running','pausing','paused','resuming','retrying','interrupted','cancelled','failed','completed'].includes(item.lifecycle)&&
    typeof item.approved==='boolean'&&typeof item.artifactAvailable==='boolean'&&integer(item.completed)&&integer(item.count,true)&&integer(item.minutes,true)&&
    ['subject','format','stage','requirements','errorCode'].every(key=>item[key]===undefined||typeof item[key]==='string');
  if(!record(value)||value.schemaVersion!=='astra-workspace-state-v1'||typeof value.observedAt!=='string'||
      !Array.isArray(value.active)||value.active.length>5||!value.active.every(workspace)||
      typeof value.activeCount!=='number'||!Number.isInteger(value.activeCount)||value.activeCount<value.active.length||
      (value.current!==undefined&&!workspace(value.current)))throw new Error('live_state_contract');
  return value as unknown as LiveState;
}
export async function readLiveState(workspaceId: string): Promise<LiveState> {
  const response=await fetch(`/agent/workspace-state?workspace_id=${encodeURIComponent(workspaceId)}`,{
    cache:'no-store',credentials:'same-origin',signal:AbortSignal.timeout(6000),
  });
  if(!response.ok)throw new Error('live_state_unavailable');
  return parseLiveState(await response.json());
}

export function liveStatusText(facts: LiveWorkspace): string {
  const family=facts.format?.startsWith('thpt-')?' THPT':facts.format?.startsWith('vact')?' V-ACT':'';
  const title=facts.subject?`Đề ${facts.subject}${family}`:facts.title;
  const headline=[title,facts.count?`${facts.count} câu`:'',facts.minutes?`${facts.minutes} phút`:''].filter(Boolean).join(' · ')+'.';
  if(facts.lifecycle==='completed')return `${headline}\nĐã soạn xong ${facts.count??facts.completed} câu. ${facts.approved?'Bản hiện tại đã được duyệt.':'Bản hiện tại đang chờ giáo viên duyệt.'}`;
  const labels:Record<string,string>={draft:'Bản nháp, chưa gửi yêu cầu tạo',queued:'Đã nhận yêu cầu, đang xếp hàng',running:'Đang soạn đề',resuming:'Đang tiếp tục phần còn lại',retrying:'Đang thử lại có giới hạn',pausing:'Đang chờ lưu để tạm dừng',paused:'Đã tạm dừng',interrupted:'Quá trình bị gián đoạn',cancelled:'Đã dừng lượt tạo',failed:'Lượt tạo gặp lỗi'};
  return `${headline}\n${labels[facts.lifecycle]??'Chưa xác định trạng thái'}${facts.stage?` · ${facts.stage}`:''}.${facts.count?` Đã lưu ${facts.completed}/${facts.count} câu.`:''}${facts.artifactAvailable?' Bản đề đã lưu trước vẫn được giữ.':''}`;
}
