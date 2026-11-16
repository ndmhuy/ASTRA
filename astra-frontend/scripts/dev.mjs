import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const frontend = fileURLToPath(new URL('..', import.meta.url));
const root = resolve(frontend, '..');
const python = resolve(root, '.venv-agent', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const children = [];
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) child.kill();
  process.exitCode = code;
}
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
async function healthy() {
  try {
    const response = await fetch('http://127.0.0.1:8010/agent/health', { signal: AbortSignal.timeout(800) });
    const data = await response.json();
    return response.ok && data.service === 'astra-agent' && data.schema_version === 'agent-turn/0.1';
  } catch { return false; }
}
function launch(command, args, cwd) {
  const child = spawn(command, args, { cwd, stdio: 'inherit', windowsHide: true });
  children.push(child);
  child.on('error', error => { console.error(error.message); stop(1); });
  child.on('exit', code => { if (!stopping) stop(code || 1); });
}
if (!(await healthy())) {
  if (!existsSync(python)) {
    console.error('Missing .venv-agent Python. Install project dependencies before starting ASTRA.');
    process.exitCode = 1;
  } else {
    launch(python, ['-m', 'uvicorn', 'exam_baseline.agent.http:create_agent_app', '--factory', '--host', '127.0.0.1', '--port', '8010'], root);
    for (let attempt = 0; attempt < 50 && !stopping; attempt++) {
      if (await healthy()) break;
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    if (!(await healthy())) { console.error('Agent failed to start on port 8010. See error above.'); stop(1); }
  }
}
if (!stopping && !process.exitCode) {
  console.log('ASTRA Agent ready: http://127.0.0.1:8010');
  launch(process.execPath, [resolve(frontend, 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', ...process.argv.slice(2)], frontend);
}
