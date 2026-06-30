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
        <span>待巩固数量</span>
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
import { useCourseStore } from '../stores/course'

const radarEl = ref(null)
const courseStore = useCourseStore()
const loading = ref(false)
const error = ref('')
const source = ref('demo')
const evaluation = ref(getDemoEvaluation(courseStore.currentId))
let radar = null
let resizeObserver = null

function getDemoEvaluation(courseId) {
  const evaluations = {
    computer_organization: {
      overall_mastery: 0.68,
      weak_points: ['Cache 映射方式', '流水线冲突'],
      strong_points: ['数据表示', '指令系统'],
      mastery_list: [
        { knowledge_point: '数据表示', mastery: 0.86, status: 'strong' },
        { knowledge_point: '指令系统', mastery: 0.78, status: 'normal' },
        { knowledge_point: '存储系统', mastery: 0.65, status: 'normal' },
        { knowledge_point: 'Cache 映射', mastery: 0.42, status: 'weak' },
        { knowledge_point: '流水线冲突', mastery: 0.38, status: 'weak' }
      ],
      suggestion: '演示数据：建议先巩固 Cache 映射方式，再补充流水线冲突练习。'
    },
    data_structure: {
      overall_mastery: 0.61,
      weak_points: ['二叉树遍历', '图的最短路径', '快速排序'],
      strong_points: ['线性表', '栈与队列'],
      mastery_list: [
        { knowledge_point: '线性表', mastery: 0.82, status: 'strong' },
        { knowledge_point: '栈与队列', mastery: 0.74, status: 'normal' },
        { knowledge_point: '二叉树遍历', mastery: 0.36, status: 'weak' },
        { knowledge_point: '图的最短路径', mastery: 0.31, status: 'weak' },
        { knowledge_point: '快速排序', mastery: 0.48, status: 'weak' }
      ],
      suggestion: '演示数据：建议先用手算例题攻克二叉树遍历，再进入图算法。'
    },
    operating_system: {
      overall_mastery: 0.63,
      weak_points: ['进程同步', '页面置换算法', '死锁检测'],
      strong_points: ['操作系统概述'],
      mastery_list: [
        { knowledge_point: '操作系统概述', mastery: 0.88, status: 'strong' },
        { knowledge_point: '进程调度', mastery: 0.66, status: 'normal' },
        { knowledge_point: '进程同步', mastery: 0.4, status: 'weak' },
        { knowledge_point: '页面置换算法', mastery: 0.44, status: 'weak' },
        { knowledge_point: '死锁检测', mastery: 0.35, status: 'weak' }
      ],
      suggestion: '演示数据：建议用流程图推演进程同步，再练习页面置换表格题。'
    },
    computer_network: {
      overall_mastery: 0.6,
      weak_points: ['子网划分', 'TCP 拥塞控制', '路由选择算法'],
      strong_points: ['网络概述'],
      mastery_list: [
        { knowledge_point: '网络概述', mastery: 0.8, status: 'normal' },
        { knowledge_point: '数据链路层', mastery: 0.62, status: 'normal' },
        { knowledge_point: '子网划分', mastery: 0.34, status: 'weak' },
        { knowledge_point: 'TCP 拥塞控制', mastery: 0.37, status: 'weak' },
        { knowledge_point: '路由选择算法', mastery: 0.46, status: 'weak' }
      ],
      suggestion: '演示数据：建议先练子网掩码计算，再结合抓包理解 TCP 拥塞控制。'
    }
  }
  return evaluations[courseId] || evaluations.computer_organization
}

const displayEvaluation = computed(() => evaluation.value)

const metrics = computed(() => {
  const ev = evaluation.value
  return {
    overallMastery: ev?.overall_mastery || 0,
    strongCount: ev?.strong_points?.length || 0,
    weakCount: ev?.weak_points?.length || 0
  }
})

const suggestion = computed(() =>
  evaluation.value?.suggestion || '暂无评估数据，完成练习后系统将自动生成评估。'
)

const statusText = computed(() => {
  if (loading.value) return '加载中'
  if (error.value) return '演示数据'
  return source.value === 'remote' ? '后端数据' : '演示数据'
})

function percent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`
}

function chartData() {
  const list = displayEvaluation.value?.mastery_list || []
  return list.slice(0, 6).map(item => ({
    name: item.knowledge_point || '知识点',
    value: Math.round((Number(item.mastery) || 0) * 100),
    status: item.status || 'weak'
  }))
}

function formatMasteryLabel(params) {
  return params.data?.status === 'untested' ? '未测评' : `${params.value}%`
}

function renderChart() {
  if (!radarEl.value) return
  if (!radar) radar = echarts.init(radarEl.value)

  const data = chartData()
  if (!data.length) return
  radar.setOption({
    color: ['#19bfea', '#27c994'],
    tooltip: {
      trigger: 'axis',
      formatter: params => {
        const item = Array.isArray(params) ? params[0] : params
        if (!item) return ''
        return `${item.name}：${formatMasteryLabel(item)}`
      }
    },
    grid: {
      left: 18,
      right: 18,
      top: 34,
      bottom: 18,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { formatter: '{value}%', color: '#60788e' },
      splitLine: { lineStyle: { color: 'rgba(89,128,176,.14)' } }
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: data.map(item => item.name),
      axisLabel: {
        color: '#31516c',
        width: 96,
        overflow: 'truncate'
      },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: 'rgba(89,128,176,.14)' } }
    },
    series: [{
      name: '掌握度',
      type: 'bar',
      data: data.map(item => ({ value: item.value, status: item.status })),
      barWidth: 18,
      itemStyle: {
        borderRadius: [0, 8, 8, 0],
        color: params => {
          if (params.data?.status === 'untested') return '#b8c7d4'
          if (params.value < 50) return '#ff7cac'
          return params.value >= 80 ? '#27c994' : '#19bfea'
        }
      },
      label: {
        show: true,
        position: 'right',
        formatter: formatMasteryLabel,
        color: '#31516c',
        fontWeight: 700
      }
    }]
  })
  radar.resize()
}

async function loadEvaluation() {
  loading.value = true
  error.value = ''
  try {
    const res = await getEvaluation()
    if (res.data?.mastery_list?.length) {
      evaluation.value = res.data
      source.value = 'remote'
    } else if (res.data) {
      evaluation.value = {
        ...evaluation.value,
        ...res.data,
        suggestion: res.data.suggestion || evaluation.value.suggestion
      }
      source.value = 'remote'
    }
  } catch (e) {
    error.value = e.message || 'load evaluation failed'
    source.value = 'demo'
  } finally {
    loading.value = false
    await nextTick()
    renderChart()
  }
}

async function handleCourseChanged(event) {
  const courseId = event.detail?.courseId || courseStore.currentId
  evaluation.value = getDemoEvaluation(courseId)
  source.value = 'demo'
  error.value = ''
  await nextTick()
  renderChart()
  loadEvaluation()
}

onMounted(() => {
  nextTick(() => {
    renderChart()
    resizeObserver = new ResizeObserver(() => radar?.resize())
    if (radarEl.value) resizeObserver.observe(radarEl.value)
  })
  window.setTimeout(loadEvaluation, 120)
  window.addEventListener('aptadapt:evaluation-refresh', loadEvaluation)
  window.addEventListener('aptadapt:course-changed', handleCourseChanged)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  window.removeEventListener('aptadapt:evaluation-refresh', loadEvaluation)
  window.removeEventListener('aptadapt:course-changed', handleCourseChanged)
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
  height: clamp(420px, 48vh, 620px);
  min-height: 420px;
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
    height: 380px;
    min-height: 380px;
  }
}
</style>
