import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')

const mainLayout = await readFile(path.join(frontendRoot, 'src', 'views', 'MainLayout.vue'), 'utf8')
const evaluationPanel = await readFile(path.join(frontendRoot, 'src', 'components', 'EvaluationPanel.vue'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(mainLayout.includes('watch(activeModule'), 'MainLayout should watch activeModule changes.')
assert(
  mainLayout.includes('aptadapt:evaluation-visible'),
  'MainLayout should notify EvaluationPanel after the evaluation module becomes visible.'
)
assert(
  evaluationPanel.includes('scheduleRenderChart'),
  'EvaluationPanel should schedule chart rendering after DOM/layout updates.'
)
assert(
  evaluationPanel.includes('requestAnimationFrame'),
  'EvaluationPanel should defer chart rendering until the browser has calculated layout.'
)
assert(
  evaluationPanel.includes('clientWidth') || evaluationPanel.includes('getBoundingClientRect'),
  'EvaluationPanel should avoid initializing ECharts while its container width is collapsed.'
)
assert(
  evaluationPanel.includes("addEventListener('aptadapt:evaluation-visible'"),
  'EvaluationPanel should listen for the evaluation-visible event.'
)

console.log('Evaluation chart visibility checks passed.')
