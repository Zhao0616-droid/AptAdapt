import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const agentLabels = {
  supervisor: '识别意图并编排任务',
  profile: '抽取并更新学生画像',
  retrieve: '检索课程知识库',
  doc: '生成讲解文档',
  mindmap: '生成思维导图',
  quiz: '生成练习题',
  code: '生成代码案例',
  video_script: '生成视频脚本',
  reviewer: '审核生成内容',
  planner: '规划个性化学习路径'
}

const ALL_AGENT_NAMES = [
  'supervisor',
  'profile',
  'retrieve',
  'doc',
  'mindmap',
  'quiz',
  'code',
  'video_script',
  'reviewer',
  'planner'
]

export const useWorkspaceStore = defineStore('workspace', () => {
  const resources = ref([])
  const agentSequence = ref([])
  const executionLog = ref([])
  const review = ref(null)
  const lastTaskType = ref('')
  const lastMessage = ref('')
  const source = ref('demo')

  const agentStatuses = computed(() => {
    const logMap = new Map(executionLog.value.map(item => [item.node, item]))
    const names = ALL_AGENT_NAMES

    return names.map(name => {
      const log = logMap.get(name)
      return {
        name,
        active: agentSequence.value.includes(name),
        status: log?.status || 'idle',
        label: log?.error || agentLabels[name] || '等待调度',
        duration: log?.duration_ms ? `${log.duration_ms}ms` : ''
      }
    })
  })

  function setAgentRunning(sequence = []) {
    agentSequence.value = sequence.length ? sequence : ['supervisor', 'profile', 'retrieve', 'doc', 'reviewer']
    executionLog.value = ALL_AGENT_NAMES.map(name => ({
      node: name,
      status: name === 'supervisor' ? 'running' : 'idle',
      duration_ms: 0
    }))
    source.value = 'remote'
  }

  function applyChatResult(data = {}, message = '') {
    resources.value = Array.isArray(data.resources) ? data.resources.map(normalizeResource) : []
    agentSequence.value = Array.isArray(data.agent_sequence) ? data.agent_sequence : []
    executionLog.value = Array.isArray(data.execution_log) ? data.execution_log : []
    review.value = data.review || null
    lastTaskType.value = data.task_type || ''
    lastMessage.value = message
    source.value = resources.value.length || executionLog.value.length ? 'remote' : 'demo'
  }

  function setResources(items = [], nextSource = 'remote') {
    resources.value = items.map(normalizeResource)
    source.value = nextSource
  }

  function resetForCourse() {
    resources.value = []
    agentSequence.value = []
    executionLog.value = []
    review.value = null
    lastTaskType.value = ''
    lastMessage.value = '帮我生成 Cache 直接映射、全相联、组相联的学习资源'
    source.value = 'course'
  }

  function markAgentFailed(message = 'request failed') {
    const names = agentSequence.value.length
      ? agentSequence.value
      : ['supervisor', 'profile', 'retrieve', 'doc', 'reviewer']
    agentSequence.value = names
    executionLog.value = ALL_AGENT_NAMES.map((name) => ({
      node: name,
      status: name === names[0] ? 'error' : 'idle',
      duration_ms: 0,
      error: name === names[0] ? message : ''
    }))
  }

  return {
    resources,
    agentSequence,
    executionLog,
    review,
    lastTaskType,
    lastMessage,
    source,
    agentStatuses,
    setAgentRunning,
    applyChatResult,
    setResources,
    resetForCourse,
    markAgentFailed
  }
})

function normalizeResource(item) {
  return {
    type: item.type,
    title: item.title || item.type || '学习资源',
    summary: item.summary || '由多智能体协同生成',
    content: parseContent(item)
  }
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
