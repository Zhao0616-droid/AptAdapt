import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')

const evaluationPanel = await readFile(path.join(frontendRoot, 'src', 'components', 'EvaluationPanel.vue'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(evaluationPanel.includes('emptyEvaluation'), 'EvaluationPanel should define an empty evaluation state for new users.')
assert(evaluationPanel.includes('hasEvaluationData'), 'EvaluationPanel should detect whether real evaluation data exists.')
assert(evaluationPanel.includes('evaluation-empty'), 'EvaluationPanel should render an empty state instead of a demo chart for new users.')
assert(evaluationPanel.includes('radar?.clear()'), 'EvaluationPanel should clear old chart data when evaluation data is empty.')
assert(evaluationPanel.includes('evaluation.value = normalizeRemoteEvaluation(res.data)'), 'Remote evaluation should replace demo data, not merge into it.')
assert(!evaluationPanel.includes('...evaluation.value,'), 'Remote empty evaluation must not inherit stale demo mastery_list.')

console.log('Empty evaluation behavior checks passed.')
