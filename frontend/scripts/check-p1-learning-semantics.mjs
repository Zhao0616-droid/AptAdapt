import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(scriptDir, '..', '..')
const frontendRoot = path.join(repoRoot, 'frontend')

const profileCard = await readFile(path.join(frontendRoot, 'src', 'components', 'ProfileCard.vue'), 'utf8')
const evaluationPanel = await readFile(path.join(frontendRoot, 'src', 'components', 'EvaluationPanel.vue'), 'utf8')
const evaluationRouter = await readFile(path.join(repoRoot, 'app', 'routers', 'evaluation.py'), 'utf8')
const quizRouter = await readFile(path.join(repoRoot, 'app', 'routers', 'quiz.py'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(profileCard.includes('profileTitle'), 'ProfileCard should use a computed title instead of directly rendering raw major/grade.')
assert(profileCard.includes('isUnknownValue'), 'ProfileCard should normalize unknown/missing profile fields.')
assert(!profileCard.includes("displayProfile.grade || '学习者'"), 'Profile title should not append fallback grade text when grade is missing.')

assert(evaluationRouter.includes('status="untested"'), 'Evaluation API should distinguish untested weak points from measured weak scores.')
assert(evaluationRouter.includes('measured_mastery_items'), 'Overall mastery should be averaged from measured mastery items only.')
assert(evaluationPanel.includes('formatMasteryLabel'), 'EvaluationPanel should format untested mastery points without showing misleading 0%.')
assert(evaluationPanel.includes("'未测评'"), 'EvaluationPanel should show untested weak points as 未测评.')

assert(quizRouter.includes('old = profile.mastery.get(kp)'), 'Quiz mastery update should inspect whether historical mastery exists.')
assert(quizRouter.includes('old is None'), 'First quiz submission should use current accuracy directly instead of weighting against zero.')

console.log('P1 learning semantics checks passed.')
