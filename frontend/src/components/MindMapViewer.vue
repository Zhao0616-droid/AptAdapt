<template>
  <div class="mindmap-viewer">
    <div v-if="error" class="mindmap-fallback">
      <p>思维导图渲染暂不可用，已显示 Mermaid 源码。</p>
      <pre>{{ data }}</pre>
    </div>
    <div v-else ref="mermaidEl"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({ data: { type: String, default: '' } })
const mermaidEl = ref(null)
const error = ref('')
let mermaidInstance = null

async function render() {
  if (!props.data || !mermaidEl.value) return
  try {
    error.value = ''
    if (!mermaidInstance) {
      const mod = await import('mermaid')
      mermaidInstance = mod.default || mod
      mermaidInstance.initialize({ startOnLoad: false, theme: 'default' })
    }
    const id = `mindmap-svg-${Date.now()}`
    const { svg } = await mermaidInstance.render(id, props.data)
    mermaidEl.value.innerHTML = svg
  } catch (e) {
    error.value = e?.message || 'mermaid render failed'
  }
}

onMounted(render)
watch(() => props.data, render)
</script>

<style scoped>
.mindmap-viewer { min-height: 200px; overflow: auto; }

.mindmap-fallback {
  color: var(--aa-text);
}

.mindmap-fallback p {
  margin: 0 0 10px;
  color: var(--aa-muted);
}

.mindmap-fallback pre {
  max-height: 320px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(89, 128, 176, 0.12);
  white-space: pre-wrap;
}
</style>
