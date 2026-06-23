<template>
  <div class="agent-status-bar">
    <span v-for="agent in agents" :key="agent.name" class="agent-tag">
      <span :class="['dot', agent.status]"></span>
      {{ agent.name }}
    </span>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const agents = ref([
  { name: 'Supervisor', status: 'idle' },
  { name: 'Profile', status: 'idle' },
  { name: 'Doc', status: 'idle' },
  { name: 'MindMap', status: 'idle' },
  { name: 'Quiz', status: 'idle' },
  { name: 'Code', status: 'idle' },
  { name: 'Reviewer', status: 'idle' }
])
</script>

<style scoped>
.agent-status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}
.agent-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot.idle { background: #c0c4cc; }
.dot.running { background: #409eff; animation: pulse 1s infinite; }
.dot.done { background: #67c23a; }
.dot.error { background: #f56c6c; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
