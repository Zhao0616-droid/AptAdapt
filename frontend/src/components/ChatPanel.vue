<template>
  <div class="chat-panel">
    <div class="chat-header">
      <div>
        <p class="aa-kicker">Conversation</p>
        <h2 class="aa-title">对话式学习画像</h2>
      </div>
      <span class="stream-badge">SSE 流式输出</span>
    </div>

    <div class="chat-messages" ref="msgContainer">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
        <div class="content" v-html="renderMarkdown(msg.content)"></div>
      </div>
      <div v-if="streaming" class="message assistant">
        <div class="avatar">AI</div>
        <div class="content" v-html="renderMarkdown(streamContent)"></div>
        <span class="cursor">|</span>
      </div>
    </div>

    <div class="quick-prompts">
      <button @click="fillPrompt('我 Cache 映射方式总是分不清，希望用图解和例题学习。')">
        Cache 映射
      </button>
      <button @click="fillPrompt('帮我梳理流水线冲突，并生成一组选择题。')">
        流水线冲突
      </button>
      <button @click="fillPrompt('我想用汇编和图示理解中断处理流程。')">
        中断机制
      </button>
    </div>

    <div class="chat-input">
      <el-input
        v-model="input"
        placeholder="输入你的学习问题，如：我 Cache 映射方式分不清..."
        @keyup.enter="send"
        :disabled="streaming"
        size="large"
      />
      <el-button type="primary" size="large" @click="send" :disabled="streaming" :loading="streaming">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useCourseStore } from '../stores/course'
import { useUserStore } from '../stores/user'
import { useWorkspaceStore } from '../stores/workspace'
import markdownit from 'markdown-it'

const md = markdownit()
const courseStore = useCourseStore()
const userStore = useUserStore()
const workspaceStore = useWorkspaceStore()
const messages = ref([])
const input = ref('帮我生成 Cache 直接映射、全相联、组相联的学习资源')
const streamContent = ref('')
const streaming = ref(false)
const msgContainer = ref(null)
const activeCourseId = ref(courseStore.currentId)

function welcomeMessage(courseName = courseStore.currentCourse?.name || '计算机组成原理') {
  return {
    role: 'assistant',
    content: `你好，我是 AptAdapt 学习助手。当前课程是 **${courseName}**，你可以描述薄弱点或直接提问知识点。`
  }
}

function storageKey(courseId = courseStore.currentId) {
  return `aptadapt:chat:${courseId || 'computer_organization'}`
}

function saveCurrentMessages(courseId = activeCourseId.value) {
  if (!courseId || !messages.value.length) return
  localStorage.setItem(storageKey(courseId), JSON.stringify(messages.value))
}

function loadMessagesForCourse(courseId = courseStore.currentId) {
  activeCourseId.value = courseId || 'computer_organization'
  const raw = localStorage.getItem(storageKey(courseId))
  if (raw) {
    try {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length) {
        messages.value = parsed
        scrollToBottom()
        return
      }
    } catch {
      localStorage.removeItem(storageKey(courseId))
    }
  }
  messages.value = [welcomeMessage(courseStore.currentCourse?.name)]
  scrollToBottom()
}

function createFreshConversation(courseId = courseStore.currentId) {
  activeCourseId.value = courseId || 'computer_organization'
  input.value = '帮我生成 Cache 直接映射、全相联、组相联的学习资源'
  streamContent.value = ''
  streaming.value = false
  messages.value = [welcomeMessage(courseStore.currentCourse?.name)]
  localStorage.setItem(storageKey(activeCourseId.value), JSON.stringify(messages.value))
  scrollToBottom()
}

function handleCourseChanged(event) {
  saveCurrentMessages(activeCourseId.value)
  input.value = ''
  streamContent.value = ''
  streaming.value = false
  loadMessagesForCourse(event.detail?.courseId || courseStore.currentId)
}

function handleChatReset(event) {
  createFreshConversation(event.detail?.courseId || courseStore.currentId)
}

function renderMarkdown(text) {
  return text ? md.render(text) : ''
}

function scrollToBottom() {
  nextTick(() => {
    const el = msgContainer.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function fillPrompt(text) {
  input.value = text
}

function formatResponse(apiData) {
  if (!apiData) return '后端没有返回有效结果，请稍后重试。'
  const resources = apiData.resources || []
  const review = apiData.review || {}
  const taskType = apiData.task_type || ''
  const agentText = apiData.agent_sequence?.length
    ? `\n\n**智能体流程**：${apiData.agent_sequence.join(' → ')}`
    : ''

  const doc = resources.find(r => r.type === 'doc')
  if (doc && doc.content) {
    let text = doc.content
    text += agentText
    if (review.notes && review.notes.length) {
      text += '\n\n---\n**审核反馈**：' + review.notes.map(n => '\n- ' + n).join('')
    }
    return text
  }

  if (resources.length) {
    const names = resources.map(r => '- **' + (r.title || r.type) + '**').join('\n')
    return `## 已生成以下学习资源\n\n${names}${agentText}\n\n${review.passed ? '审核通过' : '审核未通过'}`
  }

  if (taskType === 'profile') return '画像已更新。你可以继续描述学习情况，或直接提问知识点。'
  if (taskType === 'path' || taskType === 'planner') return '学习路径已规划完成，请在下方个性化路径面板查看。'
  if (apiData.error) {
    return `本次智能体流程已停止：${apiData.error}\n\n请缩短问题范围后再试。`
  }
  return '本次智能体流程已完成，但没有生成资源。你可以明确说明要生成“讲解文档、练习题、思维导图或代码案例”。'
}

function formatRequestError(error) {
  const detail = error?.response?.data?.detail || error?.message || '未知错误'
  if (error?.code === 'ECONNABORTED') {
    return '后端智能体执行超过前端等待时间，本次没有确认生成资源。请稍后查看后端日志，或先在资源工厂生成单类资源。'
  }
  if (error?.response?.status === 500) {
    return `后端资源生成接口报错：${detail}\n\n这不是前端已经生成了资源，而是后端流程中断了。`
  }
  return `请求后端失败：${detail}\n\n当前不会伪造生成结果。`
}

async function send() {
  if (!input.value.trim() || streaming.value) return
  const userMsg = input.value.trim()
  messages.value.push({ role: 'user', content: userMsg })
  input.value = ''
  saveCurrentMessages()
  scrollToBottom()

  streaming.value = true
  streamContent.value = ''
  workspaceStore.setAgentRunning()

  try {
    const { sendMessage } = await import('../api/chat')
    const res = await sendMessage(userMsg, courseStore.currentId)
    const data = res.data.data
    workspaceStore.applyChatResult(data, userMsg)
    streamContent.value = formatResponse(data)
    userStore.fetchProfile().catch(() => {})
  } catch (error) {
    workspaceStore.markAgentFailed(error?.response?.data?.detail || error?.message || 'request failed')
    streamContent.value = formatRequestError(error)
  } finally {
    messages.value.push({ role: 'assistant', content: streamContent.value })
    streaming.value = false
    streamContent.value = ''
    saveCurrentMessages()
    scrollToBottom()
  }
}

onMounted(() => {
  createFreshConversation(courseStore.currentId)
  window.addEventListener('aptadapt:course-changed', handleCourseChanged)
  window.addEventListener('aptadapt:chat-reset', handleChatReset)
})

onBeforeUnmount(() => {
  saveCurrentMessages()
  window.removeEventListener('aptadapt:course-changed', handleCourseChanged)
  window.removeEventListener('aptadapt:chat-reset', handleChatReset)
})
</script>

<style scoped>
.chat-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto auto;
  height: 100%;
  min-height: 0;
}

.chat-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px 0;
}

.chat-header .aa-title {
  font-size: 22px;
}

.stream-badge {
  padding: 6px 10px;
  border-radius: 8px;
  color: #1b6c89;
  background: rgba(229, 249, 255, 0.78);
  border: 1px solid rgba(64, 184, 230, 0.18);
  font-size: 12px;
  white-space: nowrap;
}

.chat-messages {
  min-height: 0;
  overflow-y: auto;
  padding: 14px 18px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: #0f4e72;
  font-size: 13px;
  font-weight: 900;
  background: linear-gradient(135deg, rgba(122, 225, 255, 0.55), rgba(220, 232, 255, 0.8));
  border: 1px solid rgba(64, 184, 230, 0.2);
}

.message.assistant .avatar {
  color: #14664d;
  background: rgba(226, 255, 245, 0.9);
  border-color: rgba(39, 201, 148, 0.2);
}

.content {
  max-width: min(78%, 720px);
  padding: 13px 15px;
  border-radius: 8px;
  color: var(--aa-text);
  line-height: 1.75;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(89, 128, 176, 0.12);
}

.content :deep(h1) {
  font-size: 24px;
  line-height: 1.25;
  margin: 0 0 12px;
}

.content :deep(h2) {
  font-size: 20px;
  line-height: 1.3;
  margin: 12px 0 8px;
}

.content :deep(h3) {
  font-size: 17px;
  line-height: 1.35;
  margin: 10px 0 6px;
}

.content :deep(p) {
  margin: 0;
}

.content :deep(p + p),
.content :deep(ul),
.content :deep(ol) {
  margin-top: 8px;
}

.message.user .content {
  color: #0f4e72;
  background: linear-gradient(135deg, rgba(208, 247, 255, 0.95), rgba(224, 233, 255, 0.92));
  border-color: rgba(64, 184, 230, 0.22);
}

.cursor {
  align-self: center;
  color: var(--aa-cyan);
  animation: blink 1s infinite;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 18px 8px;
}

.quick-prompts button {
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid rgba(64, 184, 230, 0.16);
  border-radius: 8px;
  color: #1b6c89;
  background: rgba(229, 249, 255, 0.72);
  cursor: pointer;
}

.chat-input {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  padding: 10px 18px 14px;
  border-top: 1px solid rgba(89, 128, 176, 0.12);
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
