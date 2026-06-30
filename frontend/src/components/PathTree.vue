<template>
  <div class="path-tree">
    <div class="section-title">
      <div>
        <p class="aa-kicker">Learning Path</p>
        <h2 class="aa-title">个性化路径</h2>
      </div>
      <strong>{{ progress }}%</strong>
    </div>

    <div class="sync-row">
      <p>{{ sourceLabel }}</p>
      <el-button size="small" @click="loadPath" :loading="loading" :disabled="loading">同步后端路径</el-button>
    </div>

    <ol class="timeline">
      <li v-for="node in displayNodes" :key="node.id || node.title" :class="node.status">
        <span></span>
        <div>
          <b>{{ node.title }}</b>
          <p>{{ node.desc }}</p>
        </div>
      </li>
    </ol>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useCourseStore } from '../stores/course'
import { getLearningPath } from '../api/path'

const courseStore = useCourseStore()
const loading = ref(false)
const error = ref('')
const source = ref('demo')
const remoteNodes = ref(getDemoPath(courseStore.currentId))

function getDemoPath(courseId) {
  const paths = {
    computer_organization: [
      { id: 'digital_logic', title: '数字逻辑基础', desc: '先补齐门电路、触发器和时序逻辑。', status: 'done' },
      { id: 'instruction', title: '指令系统', desc: '理解指令格式、寻址方式和机器指令执行。', status: 'done' },
      { id: 'cache_mapping', title: 'Cache 映射方式', desc: '当前重点：直接映射、全相联、组相联。', status: 'active' },
      { id: 'pipeline', title: '流水线冲突', desc: '下一步学习结构冲突、数据冲突和控制冲突。', status: 'pending' }
    ],
    data_structure: [
      { id: 'linear_list', title: '线性表', desc: '理解顺序表和链表的存储差异。', status: 'done' },
      { id: 'stack_queue', title: '栈与队列', desc: '掌握先进后出和先进先出的典型应用。', status: 'done' },
      { id: 'binary_tree', title: '二叉树遍历', desc: '当前重点：前序、中序、后序和层序遍历。', status: 'active' },
      { id: 'graph_shortest_path', title: '图的最短路径', desc: '下一步学习 Dijkstra 和 Floyd 算法。', status: 'pending' }
    ],
    operating_system: [
      { id: 'os_intro', title: '操作系统概述', desc: '理解系统调用和内核职责。', status: 'done' },
      { id: 'process_schedule', title: '进程调度', desc: '比较 FCFS、SJF 和时间片轮转。', status: 'done' },
      { id: 'process_sync', title: '进程同步', desc: '当前重点：临界区、信号量和管程。', status: 'active' },
      { id: 'page_replace', title: '页面置换算法', desc: '下一步学习 FIFO、LRU 和 Clock。', status: 'pending' }
    ],
    computer_network: [
      { id: 'network_model', title: '网络分层模型', desc: '建立 OSI 与 TCP/IP 分层视角。', status: 'done' },
      { id: 'data_link', title: '数据链路层', desc: '理解帧、差错控制和 MAC。', status: 'done' },
      { id: 'subnetting', title: '子网划分', desc: '当前重点：掩码、网络号和主机号计算。', status: 'active' },
      { id: 'tcp_congestion', title: 'TCP 拥塞控制', desc: '下一步学习慢启动、拥塞避免和快恢复。', status: 'pending' }
    ]
  }
  return paths[courseId] || paths.computer_organization
}

const displayNodes = computed(() => remoteNodes.value)

const progress = computed(() => {
  const nodes = displayNodes.value
  if (!nodes.length) return 0
  const completed = nodes.filter(node => node.status === 'done').length
  const activeBonus = nodes.some(node => node.status === 'active') ? 0.5 : 0
  return Math.round(((completed + activeBonus) / nodes.length) * 100)
})

const sourceLabel = computed(() => {
  if (loading.value) return '正在同步后端学习路径...'
  if (error.value) return '后端暂不可用，当前展示演示路径'
  return source.value === 'remote' ? '已接入后端个性化路径接口' : '演示路径，可登录后同步真实规划'
})

function normalizePath(path = []) {
  const firstHighIndex = path.findIndex(node => node.priority === 'high')
  return path.map((node, index) => {
    let status = 'pending'
    if (node.priority === 'high' && (firstHighIndex === -1 || index === firstHighIndex)) {
      status = 'active'
    } else if (index < Math.max(firstHighIndex, 0)) {
      status = 'done'
    }

    return {
      id: node.id || node.title,
      title: node.title || node.id || '未命名知识点',
      desc: node.note || [
        node.chapter ? `第 ${node.chapter} 章` : '',
        node.difficulty ? `难度：${node.difficulty}` : ''
      ].filter(Boolean).join(' · ') || '按课程知识图谱推荐学习',
      status
    }
  })
}

async function loadPath() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await getLearningPath(courseStore.currentId || 'computer_organization')
    const nodes = normalizePath(res.data?.path || [])
    if (nodes.length) {
      remoteNodes.value = nodes
      source.value = 'remote'
    }
  } catch (e) {
    error.value = e.message || 'load path failed'
    source.value = 'demo'
  } finally {
    loading.value = false
  }
}

function handleCourseChanged(event) {
  const courseId = event.detail?.courseId || courseStore.currentId
  source.value = 'demo'
  error.value = ''
  remoteNodes.value = getDemoPath(courseId)
  loadPath()
}

onMounted(() => {
  loadPath()
  window.addEventListener('aptadapt:course-changed', handleCourseChanged)
})

onBeforeUnmount(() => {
  window.removeEventListener('aptadapt:course-changed', handleCourseChanged)
})
</script>

<style scoped>
.path-tree {
  height: 100%;
  min-height: 0;
  padding: 14px 18px 18px;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
}

.section-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.section-title strong {
  color: var(--aa-green);
  font-size: 24px;
}

.section-title .aa-title {
  font-size: 22px;
}

.sync-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
}

.sync-row p {
  margin: 0;
  color: var(--aa-muted);
  font-size: 12px;
}

.timeline {
  list-style: none;
  padding: 8px 0 0;
  margin: 0;
  min-height: 0;
  overflow-y: auto;
}

.timeline li {
  display: grid;
  grid-template-columns: 22px 1fr;
  gap: 10px;
  position: relative;
  padding: 10px 0;
}

.timeline li:not(:last-child)::after {
  content: "";
  position: absolute;
  left: 8px;
  top: 33px;
  width: 2px;
  height: calc(100% - 24px);
  background: rgba(89, 128, 176, 0.16);
}

.timeline li > span {
  width: 18px;
  height: 18px;
  margin-top: 2px;
  border-radius: 50%;
  background: rgba(146, 168, 186, 0.2);
  border: 2px solid rgba(146, 168, 186, 0.38);
  z-index: 1;
}

.timeline li.done > span {
  background: var(--aa-green);
  border-color: var(--aa-green);
  box-shadow: 0 0 18px rgba(39, 201, 148, 0.34);
}

.timeline li.active > span {
  background: var(--aa-cyan);
  border-color: var(--aa-cyan);
  box-shadow: 0 0 20px rgba(25, 191, 234, 0.42);
}

.timeline b {
  display: block;
  color: var(--aa-text);
  font-size: 14px;
  margin-bottom: 4px;
}

.timeline p {
  color: var(--aa-muted);
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
}
</style>
