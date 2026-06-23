<template>
  <div class="evaluation-panel">
    <h4>学习评估</h4>
    <div ref="radarEl" style="width:100%;height:240px"></div>
    <div ref="lineEl" style="width:100%;height:200px;margin-top:12px"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const radarEl = ref(null)
const lineEl = ref(null)

onMounted(() => {
  // 雷达图
  const radar = echarts.init(radarEl.value)
  radar.setOption({
    radar: {
      indicator: [
        { name: '计算机概述', max: 100 },
        { name: '数据表示', max: 100 },
        { name: '存储器', max: 100 },
        { name: '指令系统', max: 100 },
        { name: '流水线', max: 100 }
      ]
    },
    series: [{
      type: 'radar',
      data: [{ value: [80, 60, 45, 30, 25], name: '掌握度' }]
    }]
  })

  // 折线图
  const line = echarts.init(lineEl.value)
  line.setOption({
    xAxis: { type: 'category', data: ['Day1', 'Day2', 'Day3', 'Day4', 'Day5'] },
    yAxis: { type: 'value', max: 100 },
    series: [{
      type: 'line',
      data: [30, 42, 55, 68, 75],
      smooth: true
    }]
  })
})
</script>

<style scoped>
.evaluation-panel { padding: 4px; }
h4 { margin-bottom: 12px; }
</style>
