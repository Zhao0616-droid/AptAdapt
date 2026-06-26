<template>
  <div class="evaluation-panel">
    <div class="panel-head">
      <div>
        <p class="aa-kicker">Evaluation</p>
        <h2 class="aa-title">学习效果</h2>
      </div>
      <div class="panel-actions">
        <span>{{ statusText }}</span>
        <el-button size="small" @click="loadEvaluation" :loading="loading">同步后端评估</el-button>
      </div>
    </div>

    <div ref="radarEl" class="chart"></div>

    <div class="metric-list">
      <div>
        <span>总体掌握度</span>
        <b>{{ percent(metrics.overallMastery) }}</b>
      </div>
      <div>
        <span>强项数量</span>
        <b>{{ metrics.strongCount }} 项</b>
      </div>
      <div>
        <span>薄弱点数量</span>
        <b>{{ metrics.weakCount }} 项</b>
      </div>
    </div>

    <p class="suggestion">{{ suggestion }}</p>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { getEvaluation } from '../api/evaluation'

const radarEl = ref(null)
const loading = ref(false)
const error = ref('')
const evaluation = ref(null)
let radar = null

const fallbackEvaluation = {
  overall_mastery: 0.76,
  weak_points: ['Cache 映射方式', '流水线冲突', '中断机制'],
  strong_points: ['ALU', '指令系统'],
  mastery_list: [
    { knowledge_point: 'Cache', mastery: 0.82, status: 'normal' },
    { knowledge_point: '流水线', mastery: 0.64, status: 'normal' },
    { knowledge_point: '中断', mastery: 0.58, status: 'weak' },
    { knowledge_point: 'ALU', mastery: 0.9, status: 'strong' },
    { knowledge_point: '指令', mastery: 0.74, status: 'normal' }
  ],
  suggestion: '建议优先巩固 Cache 映射方式、流水线冲突和中断机制。'
}

const displayEvaluation = computed(() => evaluation.value || fallbackEvaluation)

const metrics = computed(() => ({
  overallMastery: displayEvaluation.value.overall_mastery || 0,
  strongCount: displayEvaluation.value.strong_points?.length || 0,
  weakCount: displayEvaluation.value.weak_points?.length || 0
}))

const suggestion = computed(() => displayEvaluation.value.suggestion || fallbackEvaluation.suggestion)

const statusText = computed(() => {
  if (loading.value) return '加载中'
  if (error.value) return '演示数据'
  return evaluation.value ? '后端数据' : '演示数据'
})

function percent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`
}

function chartData() {
  const list = displayEvaluation.value.mastery_list?.length
    ? displayEvaluation.value.mastery_list
    : fallbackEvaluation.mastery_list

  return list.slice(0, 6).map(item => ({
    name: item.knowledge_point || '知识点',
    value: Math.round((Number(item.mastery) || 0) * 100)
  }))
}

function renderChart() {
  if (!radarEl.value) return
  if (!radar) radar = echarts.init(radarEl.value)

  const data = chartData()
  radar.setOption({
    color: ['#19bfea'],
    radar: {
      radius: '64%',
      splitNumber: 4,
      axisName: { color: '#60788e' },
      splitLine: { lineStyle: { color: 'rgba(89,128,176,.16)' } },
      splitArea: { areaStyle: { color: ['rgba(25,191,234,.04)', 'rgba(39,201,148,.04)'] } },
      axisLine: { lineStyle: { color: 'rgba(89,128,176,.16)' } },
      indicator: data.map(item => ({ name: item.name, max: 100 }))
    },
    series: [{
      type: 'radar',
      areaStyle: { opacity: 0.55 },
      data: [{ value: data.map(item => item.value), name: '掌握度' }]
    }]
  })
}

async function loadEvaluation() {
  loading.value = true
  error.value = ''
  try {
    const res = await getEvaluation('demo_user')
    evaluation.value = res.data
  } catch (e) {
    error.value = e.message || 'load evaluation failed'
    evaluation.value = null
  } finally {
    loading.value = false
    await nextTick()
    renderChart()
  }
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', renderChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderChart)
  radar?.dispose()
})
</script>

<style scoped>
.evaluation-panel {
  padding: 18px;
  display: grid;
  gap: 18px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-actions span {
  padding: 6px 10px;
  border-radius: 8px;
  color: #1b6c89;
  background: rgba(229, 249, 255, 0.78);
  border: 1px solid rgba(64, 184, 230, 0.18);
  font-size: 12px;
}

.chart {
  width: 100%;
  height: 360px;
}

.metric-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.metric-list div {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(89, 128, 176, 0.12);
  background: rgba(255, 255, 255, 0.68);
}

.metric-list span {
  color: var(--aa-muted);
  font-size: 13px;
}

.metric-list b {
  color: var(--aa-green);
  font-size: 24px;
}

.suggestion {
  margin: 0;
  padding: 14px;
  border-radius: 8px;
  color: #31516c;
  line-height: 1.7;
  background: rgba(229, 249, 255, 0.66);
  border: 1px solid rgba(64, 184, 230, 0.16);
}

@media (max-width: 760px) {
  .panel-head,
  .panel-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-list {
    grid-template-columns: 1fr;
  }

  .chart {
    height: 300px;
  }
}
</style>
