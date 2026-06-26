<template>
  <div class="workspace-shell">
    <header class="topbar aa-panel">
      <div class="brand">
        <div class="brand-mark">
          <span></span>
          <i></i>
        </div>
        <div>
          <p class="aa-kicker">China Software Cup A3</p>
          <h1>AptAdapt 智构学舱</h1>
        </div>
      </div>

      <nav class="nav-tabs" aria-label="主导航">
        <button
          v-for="item in navItems"
          :key="item.key"
          :class="{ active: activeModule === item.key }"
          @click="activeModule = item.key"
        >
          {{ item.label }}
        </button>
      </nav>

      <div class="user-pill">
        <span class="pulse-dot"></span>
        <span>徐英博 · 前端演示</span>
      </div>
    </header>

    <main class="module-stage">
      <section class="module-hero aa-panel">
        <div>
          <p class="aa-kicker">{{ currentModule.eyebrow }}</p>
          <h2>{{ currentModule.title }}</h2>
          <p>{{ currentModule.desc }}</p>
        </div>
        <div class="module-stats">
          <article v-for="stat in currentModule.stats" :key="stat.label">
            <span>{{ stat.label }}</span>
            <strong>{{ stat.value }}</strong>
          </article>
        </div>
      </section>

      <section v-if="activeModule === 'workspace'" class="module-grid workspace-grid">
        <aside class="side-column">
          <section class="aa-panel course-panel">
            <div class="section-head">
              <div>
                <p class="aa-kicker">Course</p>
                <h3 class="aa-title">课程选择</h3>
              </div>
            </div>
            <el-select
              v-model="courseStore.currentId"
              placeholder="选择课程"
              @change="handleCourseChange"
              size="large"
              style="width: 100%"
            >
              <el-option
                v-for="course in courseStore.courses"
                :key="course.id"
                :label="course.name"
                :value="course.id"
              >
                <span>{{ course.name }}</span>
                <span class="chapter-count">{{ course.chapters?.length || 0 }} 章</span>
              </el-option>
            </el-select>
            <p class="course-desc">
              {{ courseStore.currentCourse?.description || '围绕计算机组成原理构建个性化资源生成闭环。' }}
            </p>
          </section>

          <section class="aa-panel">
            <ProfileCard />
          </section>
        </aside>

        <section class="aa-panel chat-shell">
          <ChatPanel />
        </section>

        <aside class="side-column">
          <section class="aa-panel">
            <PathTree />
          </section>
        </aside>
      </section>

      <section v-else-if="activeModule === 'resources'" class="module-grid resource-grid">
        <section class="aa-panel resource-workbench">
          <ResourcePanel />
        </section>
        <aside class="aa-panel guide-panel">
          <p class="aa-kicker">Resource Flow</p>
          <h3 class="aa-title">资源生成流程</h3>
          <ol class="flow-list">
            <li v-for="step in resourceSteps" :key="step.title">
              <span>{{ step.no }}</span>
              <div>
                <b>{{ step.title }}</b>
                <p>{{ step.desc }}</p>
              </div>
            </li>
          </ol>
        </aside>
      </section>

      <section v-else-if="activeModule === 'agents'" class="module-grid agents-grid">
        <section class="aa-panel agent-map-panel">
          <div class="section-head">
            <div>
              <p class="aa-kicker">Agent Topology</p>
              <h3 class="aa-title">多智能体协作拓扑</h3>
            </div>
          </div>
          <div class="agent-orbit">
            <div class="orbit">
              <div class="chip-core">Supervisor</div>
              <div class="chip-node n1">Profile</div>
              <div class="chip-node n2">RAG</div>
              <div class="chip-node n3">Quiz</div>
              <div class="chip-node n4">Review</div>
            </div>
          </div>
        </section>

        <section class="aa-panel status-panel">
          <div class="section-head">
            <div>
              <p class="aa-kicker">Agent Status</p>
              <h3 class="aa-title">智能体运行状态</h3>
            </div>
          </div>
          <AgentStatusBar />
        </section>
      </section>

      <section v-else class="module-grid evaluation-grid">
        <section class="aa-panel evaluation-workbench">
          <EvaluationPanel />
        </section>
        <aside class="aa-panel guide-panel">
          <p class="aa-kicker">Learning Insight</p>
          <h3 class="aa-title">下一步学习建议</h3>
          <div class="insight-list">
            <article v-for="item in insights" :key="item.title">
              <span>{{ item.value }}</span>
              <div>
                <b>{{ item.title }}</b>
                <p>{{ item.desc }}</p>
              </div>
            </article>
          </div>
        </aside>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useCourseStore } from '../stores/course'
import ChatPanel from '../components/ChatPanel.vue'
import PathTree from '../components/PathTree.vue'
import ResourcePanel from '../components/ResourcePanel.vue'
import ProfileCard from '../components/ProfileCard.vue'
import EvaluationPanel from '../components/EvaluationPanel.vue'
import AgentStatusBar from '../components/AgentStatusBar.vue'

const courseStore = useCourseStore()
const activeModule = ref('workspace')

const navItems = [
  {
    key: 'workspace',
    label: '学习工作台',
    eyebrow: 'Learning Workspace',
    title: '从学生画像开始组织个性化学习',
    desc: '集中处理课程选择、学习画像、路径规划和对话式需求采集，作为整个系统的起点。',
    stats: [
      { label: '画像维度', value: '6 项' },
      { label: '路径进度', value: '68%' },
      { label: '当前课程', value: '计组' }
    ]
  },
  {
    key: 'resources',
    label: '资源工厂',
    eyebrow: 'Resource Factory',
    title: '把知识点生成可学习、可练习的资源包',
    desc: '统一展示讲解文档、思维导图、练习题、代码示例和视频脚本，便于演示资源生成闭环。',
    stats: [
      { label: '资源类型', value: '5 类' },
      { label: '当前知识点', value: 'Cache' },
      { label: '审核状态', value: '待审' }
    ]
  },
  {
    key: 'agents',
    label: '智能体监控',
    eyebrow: 'Agent Monitor',
    title: '观察 Supervisor 协调下的多智能体流程',
    desc: '把画像、检索、导图、练习和审核智能体拆开展示，让评委看清系统不是单一聊天框。',
    stats: [
      { label: '智能体', value: '5 个' },
      { label: '运行中', value: '2 个' },
      { label: '队列', value: '1 项' }
    ]
  },
  {
    key: 'evaluation',
    label: '学习评估',
    eyebrow: 'Learning Evaluation',
    title: '用图表反馈掌握度和后续学习建议',
    desc: '展示学生掌握度、练习正确率和薄弱点趋势，为下一轮路径规划提供依据。',
    stats: [
      { label: '完成度', value: '76%' },
      { label: '正确率', value: '84%' },
      { label: '薄弱点', value: '3 项' }
    ]
  }
]

const resourceSteps = [
  { no: '01', title: '选择知识点', desc: '从课程 DAG 或对话需求中确定本轮生成目标。' },
  { no: '02', title: '调用资源智能体', desc: '生成文档、导图、练习题、代码示例和视频脚本。' },
  { no: '03', title: '内容审核', desc: 'Reviewer Agent 检查准确性、难度和表达风格。' },
  { no: '04', title: '进入评估闭环', desc: '学生完成练习后更新画像与掌握度。' }
]

const insights = [
  { value: '优先', title: 'Cache 映射方式', desc: '建议继续用图解和例题区分直接映射、全相联和组相联。' },
  { value: '补强', title: '流水线冲突', desc: '用表格整理结构冲突、数据冲突和控制冲突的处理方式。' },
  { value: '巩固', title: '中断机制', desc: '结合 I/O 流程图理解中断响应、保护现场和恢复现场。' }
]

const currentModule = computed(() =>
  navItems.find(item => item.key === activeModule.value) || navItems[0]
)

function handleCourseChange(courseId) {
  courseStore.switchCourse(courseId)
}

onMounted(() => {
  courseStore.loadCourses()
})
</script>

<style scoped>
.workspace-shell {
  position: relative;
  z-index: 1;
  width: min(1720px, calc(100% - 40px));
  min-height: 100vh;
  margin: 0 auto;
  padding: 20px 0 28px;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 18px;
}

.topbar {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) auto minmax(220px, 1fr);
  align-items: center;
  gap: 18px;
  padding: 14px 18px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.brand-mark {
  position: relative;
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(97, 215, 255, 0.42), rgba(140, 245, 212, 0.5));
  border: 1px solid rgba(64, 184, 230, 0.34);
  box-shadow: 0 0 35px rgba(64, 215, 255, 0.18);
}

.brand-mark span {
  width: 25px;
  height: 25px;
  border: 2px solid var(--aa-cyan);
  transform: rotate(45deg);
}

.brand-mark i {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--aa-green);
  box-shadow: 0 0 18px var(--aa-green);
}

.brand h1 {
  margin: 4px 0 0;
  font-size: 24px;
  line-height: 1;
  color: var(--aa-text);
}

.nav-tabs {
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  border-radius: 8px;
  background: rgba(237, 246, 255, 0.8);
  border: 1px solid rgba(99, 145, 190, 0.12);
}

.nav-tabs button {
  min-width: 96px;
  padding: 10px 14px;
  border: 0;
  border-radius: 7px;
  color: var(--aa-muted);
  background: transparent;
  cursor: pointer;
  white-space: nowrap;
  font-weight: 700;
}

.nav-tabs button.active {
  color: #0f4e72;
  background: linear-gradient(135deg, rgba(122, 225, 255, 0.55), rgba(220, 232, 255, 0.8));
  box-shadow: inset 0 0 0 1px rgba(64, 184, 230, 0.22);
}

.user-pill {
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(39, 201, 148, 0.22);
  background: rgba(226, 255, 245, 0.76);
  color: #14664d;
  font-weight: 700;
}

.pulse-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--aa-green);
  box-shadow: 0 0 0 7px rgba(39, 201, 148, 0.12);
}

.module-stage {
  min-width: 0;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 18px;
}

.module-hero {
  min-height: 150px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 28px;
  padding: 28px;
}

.module-hero h2 {
  max-width: 820px;
  margin: 8px 0 12px;
  color: var(--aa-text);
  font-size: clamp(30px, 3vw, 46px);
  line-height: 1.12;
}

.module-hero p:last-child {
  max-width: 860px;
  margin: 0;
  color: #60788e;
  font-size: 16px;
  line-height: 1.8;
}

.module-stats {
  min-width: 360px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.module-stats article {
  min-height: 86px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid rgba(89, 128, 176, 0.14);
  background: rgba(255, 255, 255, 0.7);
}

.module-stats span {
  display: block;
  color: var(--aa-muted);
  font-size: 13px;
  margin-bottom: 10px;
}

.module-stats strong {
  color: var(--aa-cyan);
  font-size: 24px;
}

.module-grid {
  min-width: 0;
  display: grid;
  gap: 18px;
  align-items: start;
}

.workspace-grid {
  grid-template-columns: 300px minmax(0, 1fr) 320px;
}

.resource-grid {
  grid-template-columns: minmax(0, 1fr) 360px;
}

.agents-grid {
  grid-template-columns: minmax(420px, 0.85fr) minmax(0, 1fr);
}

.evaluation-grid {
  grid-template-columns: minmax(0, 1fr) 360px;
}

.side-column {
  display: grid;
  gap: 18px;
}

.course-panel,
.resource-workbench,
.guide-panel,
.agent-map-panel,
.status-panel,
.evaluation-workbench {
  padding: 18px;
}

.resource-workbench,
.evaluation-workbench,
.chat-shell {
  min-height: 560px;
}

.chat-shell {
  padding: 0;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}

.chapter-count {
  float: right;
  color: #8a9aac;
  font-size: 13px;
}

.course-desc {
  margin: 12px 0 0;
  color: var(--aa-muted);
  font-size: 13px;
  line-height: 1.7;
}

.flow-list {
  list-style: none;
  margin: 20px 0 0;
  padding: 0;
  display: grid;
  gap: 14px;
}

.flow-list li,
.insight-list article {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 12px;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(89, 128, 176, 0.13);
  background: rgba(255, 255, 255, 0.66);
}

.flow-list span,
.insight-list span {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #18abd3;
  font-weight: 900;
  background: rgba(229, 249, 255, 0.9);
  border: 1px solid rgba(64, 184, 230, 0.2);
}

.flow-list b,
.insight-list b {
  color: var(--aa-text);
}

.flow-list p,
.insight-list p {
  margin: 6px 0 0;
  color: var(--aa-muted);
  font-size: 13px;
  line-height: 1.6;
}

.insight-list {
  display: grid;
  gap: 14px;
  margin-top: 20px;
}

.agent-orbit {
  min-height: 440px;
  display: grid;
  place-items: center;
}

.orbit {
  position: relative;
  width: 330px;
  height: 330px;
  border-radius: 50%;
  border: 1px dashed rgba(25, 191, 234, 0.34);
}

.orbit::before,
.orbit::after {
  content: "";
  position: absolute;
  inset: 44px;
  border-radius: 50%;
  border: 1px solid rgba(39, 201, 148, 0.16);
}

.orbit::after {
  inset: 96px;
  border-color: rgba(255, 124, 172, 0.18);
}

.chip-core,
.chip-node {
  position: absolute;
  display: grid;
  place-items: center;
  border-radius: 8px;
  border: 1px solid rgba(89, 128, 176, 0.14);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 0 28px rgba(25, 191, 234, 0.14);
}

.chip-core {
  inset: 126px 86px;
  color: var(--aa-cyan);
  font-size: 20px;
  font-weight: 900;
}

.chip-node {
  width: 92px;
  height: 38px;
  color: #31516c;
  font-size: 13px;
  font-weight: 800;
}

.n1 { left: 119px; top: -19px; }
.n2 { right: -34px; top: 120px; }
.n3 { right: 28px; bottom: 36px; }
.n4 { left: -34px; bottom: 92px; }

@media (max-width: 1360px) {
  .topbar,
  .module-hero,
  .workspace-grid,
  .resource-grid,
  .agents-grid,
  .evaluation-grid {
    grid-template-columns: 1fr;
  }

  .user-pill {
    justify-self: start;
  }

  .module-stats {
    min-width: 0;
  }
}

@media (max-width: 900px) {
  .workspace-shell {
    width: min(calc(100vw - 24px), 1720px);
  }

  .brand h1 {
    font-size: 22px;
  }

  .nav-tabs {
    width: 100%;
    overflow-x: auto;
  }

  .nav-tabs button {
    min-width: 84px;
    padding: 10px 8px;
  }

  .module-hero {
    padding: 22px;
  }

  .module-hero h2 {
    font-size: 30px;
  }

  .module-stats {
    grid-template-columns: 1fr;
  }

  .resource-workbench,
  .evaluation-workbench,
  .chat-shell {
    min-height: 520px;
  }
}
</style>
