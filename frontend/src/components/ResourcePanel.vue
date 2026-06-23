<template>
  <div class="resource-panel">
    <div v-if="resources.length === 0" class="empty-tip">
      在左侧对话框中提问，AI 将为你生成个性化学习资源
    </div>
    <div v-for="(res, i) in resources" :key="i" class="resource-card">
      <div class="card-header">
        <el-tag :type="tagType(res.type)" size="small">{{ typeLabel(res.type) }}</el-tag>
        <span class="card-title">{{ res.title }}</span>
      </div>
      <div class="card-body">
        <MarkdownViewer v-if="res.type === 'doc'" :content="res.content" />
        <MindMapViewer v-else-if="res.type === 'mindmap'" :data="res.content" />
        <QuizCard v-else-if="res.type === 'quiz'" :quiz="parsedContent(res)" />
        <CodeBlock v-else-if="res.type === 'code'" :code="parsedContent(res)" />
        <MarkdownViewer v-else :content="res.content" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MarkdownViewer from './MarkdownViewer.vue'
import MindMapViewer from './MindMapViewer.vue'
import QuizCard from './QuizCard.vue'
import CodeBlock from './CodeBlock.vue'

const resources = ref([])

function parsedContent(res) {
  // quiz 和 code 的 content 是 JSON 字符串，需要转为对象
  if ((res.type === 'quiz' || res.type === 'code') && typeof res.content === 'string') {
    try {
      return JSON.parse(res.content)
    } catch {
      return res.content
    }
  }
  return res.content
}

function tagType(type) {
  const map = { doc: 'success', mindmap: 'warning', quiz: 'danger', code: '', video_script: 'info' }
  return map[type] || ''
}

function typeLabel(type) {
  const map = { doc: '讲解文档', mindmap: '思维导图', quiz: '练习题', code: '代码案例', video_script: '视频脚本' }
  return map[type] || type
}
</script>

<style scoped>
.resource-panel { display: flex; flex-direction: column; gap: 12px; }
.empty-tip { color: #909399; text-align: center; padding: 40px 0; font-size: 14px; }
.resource-card {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fafafa;
  border-bottom: 1px solid #e4e7ed;
}
.card-title { font-size: 14px; font-weight: 500; }
.card-body { padding: 12px; }
</style>
