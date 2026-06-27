<template>
  <div class="quiz-card">
    <div class="question">{{ quiz.question }}</div>

    <el-radio-group v-model="selected" class="options" v-if="quiz.options">
      <el-radio v-for="(opt, i) in quiz.options" :key="i" :value="i" :disabled="submitted || submitting">
        {{ optionLabel(i) }}. {{ opt }}
      </el-radio>
    </el-radio-group>

    <div class="actions" v-if="!submitted">
      <el-button type="primary" size="small" @click="submit" :disabled="selected === null" :loading="submitting">
        提交答案
      </el-button>
    </div>

    <div v-if="submitted" :class="['result', isCorrect ? 'correct' : 'wrong']">
      <strong>{{ isCorrect ? '回答正确' : '回答错误' }}</strong>
      <p v-if="submitSource" class="submit-source">{{ submitSource }}</p>
      <div class="answer-row">
        <span>你的答案：{{ selectedAnswer }}</span>
        <span>正确答案：{{ correctAnswer }}</span>
      </div>
      <div class="explanation">{{ quiz.explanation }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { submitQuiz } from '../api/quiz'
import { useUserStore } from '../stores/user'

const props = defineProps({ quiz: { type: Object, default: () => ({}) } })
const userStore = useUserStore()
const selected = ref(null)
const submitted = ref(false)
const submitting = ref(false)
const remoteResult = ref(null)
const submitError = ref('')

const letters = ['A', 'B', 'C', 'D', 'E', 'F']

const correctIndex = computed(() => Number(props.quiz.answer ?? 0))
const selectedAnswer = computed(() => props.quiz.options?.[selected.value] ?? '')
const correctAnswer = computed(() => props.quiz.options?.[correctIndex.value] ?? '')
const localCorrect = computed(() => selected.value === correctIndex.value)
const isCorrect = computed(() => remoteResult.value?.correct ?? localCorrect.value)

const submitSource = computed(() => {
  if (remoteResult.value) return '已提交到后端，学生画像掌握度会同步更新'
  if (submitError.value) return '后端暂不可用，当前展示本地判题结果'
  return ''
})

function optionLabel(index) {
  return letters[index] || String(index + 1)
}

function buildAnswer() {
  return {
    question_id: props.quiz.id || 'demo_cache_mapping_1',
    knowledge_point: props.quiz.knowledge_point || 'Cache 映射方式',
    question: props.quiz.question || '',
    correct_answer: optionLabel(correctIndex.value),
    user_answer: optionLabel(selected.value),
    difficulty: props.quiz.difficulty || 'medium'
  }
}

async function submit() {
  if (selected.value === null || submitting.value) return

  submitting.value = true
  submitError.value = ''
  remoteResult.value = null

  try {
    const res = await submitQuiz([buildAnswer()])
    remoteResult.value = res.data?.results?.[0] || null
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
</script>

<style scoped>
.quiz-card {
  padding: 4px;
}

.question {
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--aa-text);
  line-height: 1.7;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.actions {
  margin-top: 12px;
}

.result {
  margin-top: 12px;
  padding: 12px;
  border-radius: 8px;
}

.result.correct {
  background: #f0f9eb;
  color: #2f8f5b;
}

.result.wrong {
  background: #fef0f0;
  color: #c45656;
}

.submit-source {
  margin: 6px 0 0;
  font-size: 12px;
}

.answer-row {
  display: grid;
  gap: 6px;
  margin-top: 10px;
  font-size: 13px;
}

.explanation {
  margin-top: 10px;
  font-size: 13px;
  line-height: 1.6;
}
</style>
