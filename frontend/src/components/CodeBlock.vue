<template>
  <div class="code-block">
    <div class="code-header">
      <span class="lang">{{ normalizedCode.languageLabel }}</span>
      <el-button size="small" text @click="copy">复制</el-button>
    </div>
    <pre><code ref="codeEl" class="hljs">{{ normalizedCode.source }}</code></pre>
    <div v-if="normalizedCode.explanation" class="code-explanation">{{ normalizedCode.explanation }}</div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import hljs from 'highlight.js/lib/core'
import verilog from 'highlight.js/lib/languages/verilog'
import asm from 'highlight.js/lib/languages/x86asm'
import python from 'highlight.js/lib/languages/python'
import c from 'highlight.js/lib/languages/c'
import 'highlight.js/styles/github.css'
import { normalizeCodeContent, normalizeCodeLanguage } from '../utils/resourceNormalizers'

hljs.registerLanguage('verilog', verilog)
hljs.registerLanguage('x86asm', asm)
hljs.registerLanguage('python', python)
hljs.registerLanguage('c', c)

const props = defineProps({
  code: { type: [Object, String], default: () => ({ language: '', source: '', explanation: '' }) }
})
const codeEl = ref(null)

const normalizedCode = computed(() => {
  const value = normalizeCodeContent(props.code)
  const language = normalizeCodeLanguage(value.language)
  return {
    ...value,
    language,
    languageLabel: value.language && value.language !== language ? value.language : language
  }
})

const normalizedLanguage = computed(() => normalizedCode.value.language || 'x86asm')

function highlight() {
  if (codeEl.value) {
    codeEl.value.removeAttribute('data-highlighted')
    codeEl.value.className = `hljs language-${normalizedLanguage.value}`
    hljs.highlightElement(codeEl.value)
  }
}

onMounted(highlight)
watch(() => normalizedCode.value.source, highlight)

function copy() {
  navigator.clipboard.writeText(normalizedCode.value.source || '')
}
</script>

<style scoped>
.code-block {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  background: #fff;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  background: #fafafa;
  border-bottom: 1px solid #e4e7ed;
  font-size: 13px;
}

pre {
  padding: 12px;
  overflow-x: auto;
  margin: 0;
}

code {
  font-family: 'Fira Code', Consolas, monospace;
  font-size: 13px;
  line-height: 1.65;
}

.code-explanation {
  white-space: pre-wrap;
  padding: 10px 12px;
  border-top: 1px solid #e4e7ed;
  font-size: 13px;
  line-height: 1.7;
  color: #606266;
  background: #fcfdff;
}
</style>
