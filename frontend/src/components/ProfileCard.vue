<template>
  <div class="profile-card">
    <p class="aa-kicker">Student Profile</p>
    <h2 class="aa-title">学生画像</h2>
    <div class="profile-toolbar">
      <span :class="['source-badge', userStore.profileSource]">{{ sourceText }}</span>
      <el-button size="small" text @click="refreshProfile" :loading="loading" :disabled="loading">刷新</el-button>
    </div>

    <template v-if="displayProfile">
      <div class="avatar-ring">
        <div class="avatar-core">{{ displayProfile.major?.charAt(0) || '学' }}</div>
      </div>

      <h3>{{ displayProfile.major || '计算机类' }} · {{ displayProfile.grade || '学习者' }}</h3>
      <p class="goal">目标：{{ displayProfile.course_goal || '补齐计算机组成原理薄弱点' }}</p>

      <div class="tag-group">
        <span v-for="item in visibleWeakPoints" :key="item" class="danger">{{ item }}</span>
        <span v-for="item in visibleLearningPreferences" :key="item">{{ item }}</span>
        <span v-if="displayProfile.pace">{{ displayProfile.pace }}</span>
      </div>
    </template>
    <div v-else class="profile-empty">
      <p>尚未建立学习画像</p>
      <p class="hint">在对话中描述你的专业、基础和薄弱点，系统会自动构建画像。</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)

const displayProfile = computed(() => userStore.profile)
const visibleWeakPoints = computed(() => dedupeSimilarItems(displayProfile.value?.weak_points || []))
const visibleLearningPreferences = computed(() =>
  dedupeSimilarItems([
    ...(displayProfile.value?.learning_preference || []),
    ...(displayProfile.value?.resource_preference || [])
  ])
)
const sourceText = computed(() => {
  if (loading.value) return '同步中'
  if (userStore.profileError) return '同步失败'
  if (userStore.profileSource === 'remote') return '后端画像'
  return '待建立'
})

async function refreshProfile() {
  if (loading.value) return
  loading.value = true
  try {
    await userStore.fetchProfile()
  } catch (e) {
    userStore.setProfileError(e.message || 'profile load failed')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!userStore.profile) refreshProfile()
})

function normalizeTagKey(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[，,、/|｜;；:：()（）【】\[\]{}<>《》"'“”‘’·.\-_\s]/g, '')
    .replace(/方式|知识点|核心|相关|学习|掌握|理解|生成/g, '')
}

function dedupeSimilarItems(items = []) {
  const result = []
  const keys = []
  const tokenSets = []
  for (const item of items) {
    const text = String(item || '').trim()
    const key = normalizeTagKey(text)
    if (!text || !key) continue
    const tokens = semanticTokens(key)
    const duplicateIndex = keys.findIndex((existing, index) =>
      existing === key ||
      existing.includes(key) ||
      key.includes(existing) ||
      isSimilarTokenSet(tokens, tokenSets[index])
    )
    if (duplicateIndex >= 0) {
      if (text.length < result[duplicateIndex].length) {
        result[duplicateIndex] = text
        keys[duplicateIndex] = key
        tokenSets[duplicateIndex] = tokens
      }
      continue
    }
    result.push(text)
    keys.push(key)
    tokenSets.push(tokens)
  }
  return result.slice(0, 10)
}

function semanticTokens(key) {
  const tokens = new Set()
  const concepts = ['cache', '映射', '直接映射', '全相联', '组相联', '流水线', '冲突', '中断', 'dma', '代码', '图解', '资源', '原理']
  for (const concept of concepts) {
    if (key.includes(concept)) tokens.add(concept)
  }
  if (!tokens.size) {
    for (const char of key) tokens.add(char)
  }
  return tokens
}

function isSimilarTokenSet(a, b) {
  if (!a?.size || !b?.size) return false
  const intersection = [...a].filter(token => b.has(token))
  if (intersection.length < 2) return false
  return intersection.length / Math.min(a.size, b.size) >= 0.66
}
</script>

<style scoped>
.profile-card {
  height: 100%;
  min-height: 0;
  padding: 18px;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.profile-toolbar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.source-badge {
  padding: 4px 8px;
  border-radius: 7px;
  color: #1b6c89;
  background: rgba(229, 249, 255, 0.78);
  border: 1px solid rgba(64, 184, 230, 0.18);
  font-size: 12px;
}

.source-badge.empty {
  color: #8a6d3b;
  background: rgba(255, 248, 225, 0.82);
  border-color: rgba(255, 179, 64, 0.18);
}

.avatar-ring {
  width: 112px;
  height: 112px;
  margin: 18px auto 14px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  padding: 3px;
  background: conic-gradient(from 220deg, var(--aa-cyan), var(--aa-green), var(--aa-pink), var(--aa-cyan));
  box-shadow: 0 0 42px rgba(25, 191, 234, 0.2);
}

.avatar-core {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #fff;
  color: var(--aa-text);
  font-size: 40px;
  font-weight: 900;
}

h3 {
  margin: 0 0 10px;
  color: var(--aa-text);
  font-size: 16px;
}

.goal {
  margin: 0;
  color: var(--aa-muted);
  font-size: 13px;
  line-height: 1.7;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  min-width: 0;
}

.tag-group span {
  max-width: 100%;
  padding: 6px 9px;
  border-radius: 7px;
  color: #1b6c89;
  background: rgba(229, 249, 255, 0.78);
  border: 1px solid rgba(64, 184, 230, 0.18);
  font-size: 12px;
}

.tag-group .danger {
  color: #a75926;
  background: rgba(255, 245, 225, 0.88);
  border-color: rgba(255, 179, 64, 0.22);
}

@media (max-width: 900px) {
  .tag-group {
    gap: 7px;
  }

  .tag-group span {
    padding: 5px 7px;
    font-size: 11px;
  }
}

.profile-empty {
  padding: 28px 8px;
  color: var(--aa-muted);
  font-size: 14px;
  line-height: 1.7;
}

.profile-empty .hint {
  margin-top: 10px;
  font-size: 12px;
  color: #8a9aac;
}
</style>
