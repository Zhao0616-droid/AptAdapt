<template>
  <div class="quiz-card">
    <div class="quiz-head">
      <div>
        <p class="quiz-label">Adaptive Practice</p>
        <h3>{{ quizTitle }}</h3>
      </div>
      <div class="quiz-progress">
        <span>{{ answeredCount }}/{{ normalizedQuestions.length }}</span>
        <b v-if="submitted">{{ scoreSummary }}</b>
      </div>
    </div>

    <div class="question-list">
      <article
        v-for="(item, index) in normalizedQuestions"
        :key="item.id"
        :class="['question-card', submitted ? (isQuestionCorrect(index) ? 'correct' : 'wrong') : '']"
      >
        <div class="question-top">
          <span>第 {{ index + 1 }} 题</span>
          <em>{{ difficultyText(item.difficulty) }}</em>
        </div>

        <div class="question">{{ item.question }}</div>

        <el-radio-group
          v-model="answers[index]"
          class="options"
          :disabled="submitted || submitting"
        >
          <el-radio
            v-for="(opt, optionIndex) in item.options"
            :key="`${item.id}-${optionIndex}`"
            :value="optionIndex"
          >
            {{ optionLabel(optionIndex) }}. {{ cleanOption(opt) }}
          </el-radio>
        </el-radio-group>

        <div v-if="submitted" class="result-detail">
          <div class="answer-row">
            <span>你的答案：{{ optionLabel(answers[index]) || '未作答' }}</span>
            <span>正确答案：{{ optionLabel(item.answerIndex) }}</span>
          </div>
          <p>{{ item.explanation }}</p>
        </div>
      </article>
    </div>

    <div class="quiz-actions">
      <div class="submit-note">
        <span v-if="!submitted">提交后会更新学生画像和学习评估。</span>
        <span v-else>{{ submitSource }}</span>
      </div>
      <el-button
        v-if="!submitted"
        type="primary"
        @click="submit"
        :disabled="answeredCount !== normalizedQuestions.length || !normalizedQuestions.length"
        :loading="submitting"
      >
        提交整套练习
      </el-button>
      <el-button v-else @click="resetPractice">重新作答</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { submitQuiz } from '../api/quiz'
import { useUserStore } from '../stores/user'

const props = defineProps({ quiz: { type: [Object, Array], default: () => ({}) } })
const userStore = useUserStore()
const answers = ref([])
const submitted = ref(false)
const submitting = ref(false)
const remoteResults = ref([])
const submitError = ref('')

const letters = ['A', 'B', 'C', 'D', 'E', 'F']

const normalizedQuestions = computed(() => normalizeQuestions(props.quiz))
const quizTitle = computed(() => props.quiz?.title || `${normalizedQuestions.value[0]?.knowledge_point || '知识点'} 巩固练习`)
const answeredCount = computed(() => answers.value.filter(value => value !== null && value !== undefined).length)
const localCorrectCount = computed(() =>
  normalizedQuestions.value.reduce((total, item, index) => total + (answers.value[index] === item.answerIndex ? 1 : 0), 0)
)
const correctCount = computed(() =>
  remoteResults.value.length
    ? remoteResults.value.filter(item => item.correct).length
    : localCorrectCount.value
)
const scoreSummary = computed(() => {
  const total = normalizedQuestions.value.length || 0
  return total ? `${correctCount.value}/${total} · ${Math.round((correctCount.value / total) * 100)}分` : '0分'
})
const submitSource = computed(() => {
  if (remoteResults.value.length) return '已提交后端，画像与学习评估已刷新。'
  if (submitError.value) return '后端暂不可用，当前保留本地判题结果。'
  return '已完成本地判题。'
})

watch(normalizedQuestions, (questions) => {
  answers.value = questions.map(() => null)
  submitted.value = false
  submitting.value = false
  remoteResults.value = []
  submitError.value = ''
}, { immediate: true })

function normalizeQuestions(rawQuiz) {
  const rawQuestions = Array.isArray(rawQuiz)
    ? rawQuiz
    : Array.isArray(rawQuiz?.questions)
      ? rawQuiz.questions
      : rawQuiz?.question
        ? [rawQuiz]
        : []

  return rawQuestions.map((item, index) => {
    const type = item.type || 'choice'
    const options = normalizeOptions(item.options, type)
    return {
      id: item.id || `${item.knowledge_point || rawQuiz?.knowledge_point || 'quiz'}_${index + 1}`,
      type,
      question: item.question || `关于${item.knowledge_point || rawQuiz?.knowledge_point || '该知识点'}的练习题`,
      options,
      answerIndex: normalizeAnswerIndex(item.answer, options),
      explanation: item.explanation || '请结合生成的讲解文档复盘本题。',
      difficulty: item.difficulty || 'medium',
      knowledge_point: item.knowledge_point || rawQuiz?.knowledge_point || 'Cache 映射方式'
    }
  })
}

function normalizeOptions(options, type) {
  if (Array.isArray(options) && options.length) return options.map(cleanOption)
  if (type === 'true_false') return ['正确', '错误']
  return ['选项 A', '选项 B', '选项 C', '选项 D']
}

function normalizeAnswerIndex(answer, options = []) {
  if (typeof answer === 'number' && Number.isFinite(answer)) {
    return clampAnswer(answer, options.length)
  }
  const text = String(answer ?? '').trim()
  if (!text) return 0
  const letterIndex = letters.indexOf(text[0]?.toUpperCase())
  if (letterIndex >= 0) return clampAnswer(letterIndex, options.length)
  const numberIndex = Number(text)
  if (Number.isFinite(numberIndex)) return clampAnswer(numberIndex, options.length)
  const optionIndex = options.findIndex(option => cleanOption(option) === cleanOption(text))
  return optionIndex >= 0 ? optionIndex : 0
}

function clampAnswer(index, total) {
  if (!total) return 0
  return Math.min(Math.max(index, 0), total - 1)
}

function cleanOption(option) {
  return String(option ?? '').replace(/^[A-Fa-f][.、:：]\s*/, '').trim()
}

function optionLabel(index) {
  if (index === null || index === undefined || index < 0) return ''
  return letters[index] || String(index + 1)
}

function difficultyText(value) {
  const map = { easy: '基础', medium: '中等', hard: '提高' }
  return map[value] || '中等'
}

function isQuestionCorrect(index) {
  if (remoteResults.value[index]) return remoteResults.value[index].correct
  return answers.value[index] === normalizedQuestions.value[index]?.answerIndex
}

function buildPayload() {
  return normalizedQuestions.value.map((item, index) => ({
    question_id: item.id,
    knowledge_point: item.knowledge_point,
    question: item.question,
    correct_answer: optionLabel(item.answerIndex),
    user_answer: optionLabel(answers.value[index]),
    difficulty: item.difficulty
  }))
}

async function submit() {
  if (answeredCount.value !== normalizedQuestions.value.length || submitting.value) return

  submitting.value = true
  submitError.value = ''
  remoteResults.value = []

  const payload = buildPayload()
  try {
    const res = await submitQuiz(payload)
    remoteResults.value = res.data?.results || []
    if (res.data?.updated_profile) {
      userStore.setProfile(res.data.updated_profile, 'remote')
    }
    window.dispatchEvent(new CustomEvent('aptadapt:evaluation-refresh'))
  } catch (e) {
    submitError.value = e.message || 'submit quiz failed'
  } finally {
    submitted.value = true
    submitting.value = false
  }
}

function resetPractice() {
  answers.value = normalizedQuestions.value.map(() => null)
  submitted.value = false
  remoteResults.value = []
  submitError.value = ''
}
</script>

<style scoped>
.quiz-card {
  display: grid;
  gap: 16px;
}

.quiz-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.quiz-label {
  margin: 0 0 6px;
  color: var(--aa-muted);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

.quiz-head h3 {
  margin: 0;
  color: var(--aa-text);
  font-size: 18px;
  line-height: 1.35;
}

.quiz-progress {
  display: grid;
  gap: 6px;
  justify-items: end;
  color: var(--aa-muted);
  white-space: nowrap;
}

.quiz-progress b {
  color: var(--aa-green);
  font-size: 18px;
}

.question-list {
  display: grid;
  gap: 12px;
}

.question-card {
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(89, 128, 176, 0.13);
  background: rgba(255, 255, 255, 0.74);
}

.question-card.correct {
  border-color: rgba(39, 201, 148, 0.35);
  background: rgba(240, 249, 235, 0.9);
}

.question-card.wrong {
  border-color: rgba(255, 124, 172, 0.35);
  background: rgba(254, 240, 240, 0.92);
}

.question-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
  color: var(--aa-muted);
  font-size: 12px;
  font-weight: 800;
}

.question-top em {
  font-style: normal;
  color: #1b6c89;
}

.question {
  font-weight: 800;
  margin-bottom: 12px;
  color: var(--aa-text);
  line-height: 1.7;
}

.options {
  display: grid;
  gap: 8px;
}

.result-detail {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(89, 128, 176, 0.13);
}

.answer-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #31516c;
  font-size: 13px;
  font-weight: 800;
}

.result-detail p {
  margin: 10px 0 0;
  color: #31516c;
  font-size: 13px;
  line-height: 1.7;
}

.quiz-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 2px;
}

.submit-note {
  color: var(--aa-muted);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 760px) {
  .quiz-head,
  .quiz-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .quiz-progress {
    justify-items: start;
  }
}
</style>
