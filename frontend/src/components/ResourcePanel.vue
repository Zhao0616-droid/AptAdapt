<template>
  <div class="resource-panel">
    <div class="panel-head">
      <div>
        <p class="aa-kicker">Resource Factory</p>
        <h2 class="aa-title">生成资源</h2>
      </div>
      <div class="panel-actions">
        <span>{{ statusText }}</span>
        <el-button type="primary" size="small" @click="loadGeneratedResources" :loading="loading">
          调用后端生成
        </el-button>
      </div>
    </div>

    <div class="resource-list">
      <article
        v-for="(res, index) in resources"
        :key="res.type"
        :class="['resource-card', { active: activeIndex === index }]"
        @click="activeIndex = index"
      >
        <div class="card-icon">{{ iconLabel(res.type) }}</div>
        <div>
          <h3>{{ res.title }}</h3>
          <p>{{ res.summary }}</p>
        </div>
      </article>
    </div>

    <div class="resource-detail">
      <MarkdownViewer
        v-if="activeResource.type === 'doc' || activeResource.type === 'video_script'"
        :content="activeResource.content"
      />
      <MindMapViewer v-else-if="activeResource.type === 'mindmap'" :data="activeResource.content" />
      <QuizCard v-else-if="activeResource.type === 'quiz'" :quiz="activeResource.content" />
      <CodeBlock v-else-if="activeResource.type === 'code'" :code="activeResource.content" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useCourseStore } from '../stores/course'
import { generateResource } from '../api/resource'
import MarkdownViewer from './MarkdownViewer.vue'
import MindMapViewer from './MindMapViewer.vue'
import QuizCard from './QuizCard.vue'
import CodeBlock from './CodeBlock.vue'

const courseStore = useCourseStore()
const activeIndex = ref(0)
const loading = ref(false)
const error = ref('')
const resources = ref([])

const activeResource = computed(() => resources.value[activeIndex.value])
const statusText = computed(() => {
  if (loading.value) return '生成中'
  if (error.value) return '生成失败'
  return resources.value.length ? `${resources.value.length} 类` : '待生成'
})

function iconLabel(type) {
  const map = { doc: 'DOC', mindmap: 'MAP', quiz: 'QZ', code: 'ASM', video_script: 'VID' }
  return map[type] || 'AI'
}

function parseContent(item) {
  if (item.type !== 'quiz' && item.type !== 'code') return item.content
  if (typeof item.content !== 'string') return item.content
  try {
    return JSON.parse(item.content)
  } catch {
    return item.content
  }
}

function normalizeResource(item) {
  return {
    type: item.type,
    title: item.title || iconLabel(item.type),
    summary: item.summary || '由后端资源智能体生成',
    content: parseContent(item)
  }
}

async function loadGeneratedResources() {
  loading.value = true
  error.value = ''
  try {
    const res = await generateResource(
      courseStore.currentCourse?.name || '计算机组成原理',
      ['doc', 'mindmap', 'quiz', 'code', 'video_script']
    )
    const remoteResources = res.data?.resources || []
    if (remoteResources.length) {
      resources.value = remoteResources.map(normalizeResource)
      activeIndex.value = 0
    }
  } catch (e) {
    error.value = e.message || 'generate resource failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.resource-panel {
  display: grid;
  gap: 14px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.panel-head span {
  color: var(--aa-muted);
  font-size: 14px;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.resource-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.resource-card {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 12px;
  align-items: start;
  padding: 13px;
  border-radius: 8px;
  border: 1px solid rgba(89, 128, 176, 0.15);
  background: rgba(255, 255, 255, 0.64);
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.resource-card:hover,
.resource-card.active {
  transform: translateY(-2px);
  border-color: rgba(25, 191, 234, 0.38);
  background: rgba(234, 251, 255, 0.92);
}

.card-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: var(--aa-cyan);
  font-size: 12px;
  font-weight: 900;
  background: rgba(226, 249, 255, 0.9);
  border: 1px solid rgba(64, 184, 230, 0.2);
}

.resource-card h3 {
  margin: 0 0 6px;
  color: var(--aa-text);
  font-size: 14px;
}

.resource-card p {
  margin: 0;
  color: var(--aa-muted);
  font-size: 12px;
  line-height: 1.55;
}

.resource-detail {
  min-height: 340px;
  max-height: 520px;
  overflow: auto;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(89, 128, 176, 0.12);
  background: rgba(255, 255, 255, 0.68);
}

@media (min-width: 1180px) {
  .resource-panel {
    grid-template-columns: 0.9fr 1.1fr;
    align-items: start;
  }

  .panel-head {
    grid-column: 1 / -1;
  }

  .resource-list {
    grid-template-columns: 1fr;
  }

  .resource-detail {
    min-height: 470px;
  }
}

@media (max-width: 760px) {
  .panel-head,
  .panel-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .resource-list {
    grid-template-columns: 1fr;
  }
}
</style>
