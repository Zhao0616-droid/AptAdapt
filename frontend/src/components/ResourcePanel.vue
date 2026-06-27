<template>
  <div class="resource-panel">
    <div class="panel-head">
      <div>
        <p class="aa-kicker">Resource Factory</p>
        <h2 class="aa-title">生成资源</h2>
      </div>
      <div class="panel-actions">
        <span>{{ statusText }}</span>
        <el-button type="primary" size="small" @click="loadGeneratedResources" :loading="loading" :disabled="loading">
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
      <div v-if="!activeResource" class="resource-empty">
        <b>等待生成资源</b>
        <p>点击“调用后端生成”后，会展示文档、导图、练习题、代码示例和视频脚本。</p>
      </div>
      <MarkdownViewer
        v-else-if="activeResource.type === 'doc' || activeResource.type === 'video_script'"
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
import { useWorkspaceStore } from '../stores/workspace'
import { generateResource } from '../api/resource'
import MarkdownViewer from './MarkdownViewer.vue'
import MindMapViewer from './MindMapViewer.vue'
import QuizCard from './QuizCard.vue'
import CodeBlock from './CodeBlock.vue'

const courseStore = useCourseStore()
const workspaceStore = useWorkspaceStore()
const activeIndex = ref(0)
const loading = ref(false)
const error = ref('')
const demoResources = [
  {
    type: 'doc',
    title: 'Cache 映射方式讲解',
    summary: '演示资源：对直接映射、全相联和组相联进行对比。',
    content: '## Cache 映射方式\n\n直接映射速度快但冲突多；全相联冲突少但硬件复杂；组相联在两者之间折中。'
  },
  {
    type: 'quiz',
    title: 'Cache 映射练习',
    summary: '演示资源：完成后可提交到后端更新画像。',
    content: {
      question: '主存块只能映射到 Cache 中唯一一个位置的是哪种方式？',
      options: ['直接映射', '全相联映射', '组相联映射', '随机映射'],
      answer: 0,
      explanation: '直接映射中，主存块号通过取模确定唯一 Cache 行。'
    }
  }
]
const localResources = ref([...demoResources])
const localSource = ref('demo')

const resources = computed(() => workspaceStore.resources.length ? workspaceStore.resources : localResources.value)
const source = computed(() => workspaceStore.resources.length ? workspaceStore.source : localSource.value)
const activeResource = computed(() => resources.value[activeIndex.value])
const statusText = computed(() => {
  if (loading.value) return '生成中'
  if (error.value) return '演示资源'
  return source.value === 'remote' ? `${resources.value.length} 类后端资源` : `${resources.value.length} 类演示资源`
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
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await generateResource(
      courseStore.currentCourse?.name || '计算机组成原理',
      ['doc', 'mindmap', 'quiz', 'code', 'video_script']
    )
    const remoteResources = res.data?.resources || []
    if (remoteResources.length) {
      const normalized = remoteResources.map(normalizeResource)
      localResources.value = normalized
      workspaceStore.setResources(normalized, 'remote')
      activeIndex.value = 0
      localSource.value = 'remote'
    }
  } catch (e) {
    error.value = e.message || 'generate resource failed'
    localSource.value = 'demo'
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

.resource-empty {
  min-height: 260px;
  display: grid;
  place-content: center;
  gap: 8px;
  text-align: center;
  color: var(--aa-muted);
}

.resource-empty b {
  color: var(--aa-text);
  font-size: 16px;
}

.resource-empty p {
  max-width: 360px;
  margin: 0;
  line-height: 1.7;
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
