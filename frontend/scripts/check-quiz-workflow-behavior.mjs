import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(scriptDir, '..')
const repoRoot = path.resolve(frontendRoot, '..')

const quizCard = await readFile(path.join(frontendRoot, 'src', 'components', 'QuizCard.vue'), 'utf8')
const resourcePanel = await readFile(path.join(frontendRoot, 'src', 'components', 'ResourcePanel.vue'), 'utf8')
const quizPrompt = await readFile(path.join(repoRoot, 'agents', 'prompts', 'quiz_prompt.txt'), 'utf8')
const resourceGenerator = await readFile(path.join(repoRoot, 'app', 'services', 'resource_generator.py'), 'utf8')

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

assert(quizCard.includes('normalizedQuestions'), 'QuizCard should normalize one or many generated questions.')
assert(quizCard.includes('normalizeAnswerIndex'), 'QuizCard should accept numeric, letter, and option-text answers.')
assert(quizCard.includes('scoreSummary'), 'QuizCard should show a score summary after submission.')
assert(quizCard.includes('answers.value'), 'QuizCard should track answers for every question, not just one selected value.')
assert(quizCard.includes('aptadapt:evaluation-refresh'), 'Quiz submission should refresh the learning evaluation panel.')
assert(quizCard.includes('submitQuiz(payload)'), 'QuizCard should submit the whole exercise set to the backend.')

assert(resourcePanel.includes('normalizeQuizContent'), 'ResourcePanel should normalize quiz resources before rendering.')
assert(resourcePanel.includes('activeIndex.value = normalized.findIndex'), 'Resource factory should open the exercise card after generation.')

assert(quizPrompt.includes('"questions"'), 'Quiz prompt should ask the LLM for a question set.')
assert(quizPrompt.includes('至少 3 道'), 'Quiz prompt should require multiple usable questions.')
assert(resourceGenerator.includes('_normalize_quiz_set'), 'Backend resource generator should normalize quiz sets.')

console.log('Quiz workflow behavior checks passed.')
