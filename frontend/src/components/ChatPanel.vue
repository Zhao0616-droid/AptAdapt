<template>
  <div class="chat-panel">
    <div class="chat-messages" ref="msgContainer">
      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
        <div class="avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
        <div class="content" v-html="renderMarkdown(msg.content)"></div>
      </div>
      <div v-if="streaming" class="message assistant">
        <div class="avatar">AI</div>
        <div class="content" v-html="renderMarkdown(streamContent)"></div>
        <span class="cursor">|</span>
      </div>
    </div>
    <div class="chat-input">
      <el-input
        v-model="input"
        placeholder="输入你的学习问题，如：我Cache映射方式分不清..."
        @keyup.enter="send"
        :disabled="streaming"
      />
      <el-button type="primary" @click="send" :disabled="streaming" :loading="streaming">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import markdownit from 'markdown-it'

const md = markdownit()
const messages = ref([])
const input = ref('')
const streamContent = ref('')
const streaming = ref(false)
const msgContainer = ref(null)

function renderMarkdown(text) {
  return text ? md.render(text) : ''
}

function scrollToBottom() {
  nextTick(() => {
    const el = msgContainer.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function send() {
  if (!input.value.trim() || streaming.value) return
  const userMsg = input.value.trim()
  messages.value.push({ role: 'user', content: userMsg })
  input.value = ''
  scrollToBottom()

  streaming.value = true
  streamContent.value = ''

  // TODO: 接入 SSE 流式接口
  try {
    const { sendMessage } = await import('../api/chat')
    const res = await sendMessage(userMsg)
    streamContent.value = res.data.data.reply
    messages.value.push({ role: 'assistant', content: streamContent.value })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，生成失败：' + e.message })
  } finally {
    streaming.value = false
    streamContent.value = ''
    scrollToBottom()
  }
}

onMounted(() => {
  messages.value.push({
    role: 'assistant',
    content: '你好！我是《计算机组成原理》学习助手。请告诉我你的学习情况，我会为你生成个性化的学习资源。比如：你是什么专业、哪些知识点比较薄弱、偏好什么样的学习方式？'
  })
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.message.user {
  flex-direction: row-reverse;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  flex-shrink: 0;
}
.message.user .avatar {
  background: #409eff;
  color: #fff;
}
.message.assistant .avatar {
  background: #e6f7ff;
  color: #409eff;
}
.content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
}
.message.user .content {
  background: #409eff;
  color: #fff;
}
.message.assistant .content {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.cursor {
  animation: blink 1s infinite;
  color: #409eff;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid #e4e7ed;
  background: #fff;
}
</style>
