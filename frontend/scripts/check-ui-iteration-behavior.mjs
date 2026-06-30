import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')

const files = {
  workspace: await readFile(path.join(frontendRoot, 'src', 'stores', 'workspace.js'), 'utf8'),
  resource: await readFile(path.join(frontendRoot, 'src', 'components', 'ResourcePanel.vue'), 'utf8'),
  evaluation: await readFile(path.join(frontendRoot, 'src', 'components', 'EvaluationPanel.vue'), 'utf8'),
  layout: await readFile(path.join(frontendRoot, 'src', 'views', 'MainLayout.vue'), 'utf8'),
  chat: await readFile(path.join(frontendRoot, 'src', 'components', 'ChatPanel.vue'), 'utf8'),
  course: await readFile(path.join(frontendRoot, 'src', 'stores', 'course.js'), 'utf8')
}

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(files.course.includes('其他课程暂未扩充'), 'Course selector should state that only Computer Organization is expanded.')
assert(!files.course.includes('data_structure'), 'Other expanded course presets should not be exposed in course selection.')
assert(files.chat.includes('aptadapt:chat:'), 'Chat history should be stored per course.')
assert(files.chat.includes('aptadapt:course-changed'), 'Chat panel should refresh when the course changes.')

assert(!files.resource.includes('demoResources'), 'Resource factory should not show built-in generated resources.')
assert(!files.resource.includes('演示资源'), 'Resource factory should not label generated cards as demo resources.')
assert(files.resource.includes("['doc', 'quiz']"), 'Resource factory should request only core resources by default for faster backend generation.')
assert(!files.workspace.includes('COURSE_RESOURCE_PRESETS'), 'Workspace store should not inject built-in generated resources.')

assert(files.layout.includes('idleCount'), 'Agent stats should compute idle count from total minus active/error states.')
assert(files.layout.includes('startChatResize'), 'Workspace should expose a draggable chat/path resize handle.')
assert(files.layout.includes('startPathResize'), 'Workspace should expose a draggable path bottom resize handle.')
assert(files.layout.includes('pane-resizer'), 'Workspace should render visible resize handles.')

assert(files.evaluation.includes('ResizeObserver'), 'Evaluation chart should resize with its container.')
assert(files.evaluation.includes("type: 'bar'"), 'Evaluation chart should use a readable responsive bar chart.')
assert(files.evaluation.includes('clamp('), 'Evaluation chart should have responsive height constraints.')

console.log('UI iteration behavior checks passed.')
