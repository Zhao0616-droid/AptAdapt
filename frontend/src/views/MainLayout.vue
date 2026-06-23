<template>
  <div class="workspace">
    <!-- 左侧: 课程选择 + 学习路径 -->
    <aside class="sidebar-left">
      <div class="sidebar-header">
        <h2>AptAdapt</h2>
      </div>
      <!-- 课程选择器 -->
      <div class="course-selector">
        <el-select
          v-model="courseStore.currentId"
          placeholder="选择课程"
          @change="handleCourseChange"
          size="large"
          style="width:100%"
        >
          <el-option
            v-for="c in courseStore.courses"
            :key="c.id"
            :label="c.name"
            :value="c.id"
          >
            <span style="float:left">{{ c.name }}</span>
            <span style="float:right;color:#909399;font-size:13px">{{ c.chapters?.length || 0 }} 章</span>
          </el-option>
        </el-select>
      </div>
      <div class="course-info" v-if="courseStore.currentCourse">
        <p class="course-desc">{{ courseStore.currentCourse.description }}</p>
      </div>
      <PathTree />
    </aside>

    <!-- 中间: 对话区 -->
    <main class="main-content">
      <ChatPanel />
    </main>

    <!-- 右侧: 资源展示区 -->
    <aside class="sidebar-right">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="资源" name="resources">
          <ResourcePanel />
        </el-tab-pane>
        <el-tab-pane label="画像" name="profile">
          <ProfileCard />
        </el-tab-pane>
        <el-tab-pane label="评估" name="evaluation">
          <EvaluationPanel />
        </el-tab-pane>
      </el-tabs>
    </aside>

    <!-- 底部: Agent 状态栏 -->
    <footer class="status-bar">
      <AgentStatusBar />
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCourseStore } from '../stores/course'
import ChatPanel from '../components/ChatPanel.vue'
import PathTree from '../components/PathTree.vue'
import ResourcePanel from '../components/ResourcePanel.vue'
import ProfileCard from '../components/ProfileCard.vue'
import EvaluationPanel from '../components/EvaluationPanel.vue'
import AgentStatusBar from '../components/AgentStatusBar.vue'

const courseStore = useCourseStore()
const activeTab = ref('resources')

function handleCourseChange(courseId) {
  courseStore.switchCourse(courseId)
}

onMounted(() => {
  courseStore.loadCourses()
})
</script>

<style scoped>
.workspace {
  display: grid;
  grid-template-columns: 280px 1fr 340px;
  grid-template-rows: 1fr 36px;
  height: 100vh;
  overflow: hidden;
}
.sidebar-left {
  border-right: 1px solid #e4e7ed;
  background: #fff;
  overflow-y: auto;
}
.sidebar-header {
  padding: 16px 16px 0;
}
.sidebar-header h2 {
  font-size: 18px;
  color: #303133;
}
.course-selector {
  padding: 12px 16px;
}
.course-info {
  padding: 0 16px 8px;
}
.course-desc {
  font-size: 12px;
  color: #909399;
  margin: 0;
  line-height: 1.5;
}
.main-content {
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}
.sidebar-right {
  border-left: 1px solid #e4e7ed;
  background: #fff;
  overflow-y: auto;
  padding: 12px;
}
.status-bar {
  grid-column: 1 / -1;
  border-top: 1px solid #e4e7ed;
  background: #fff;
  display: flex;
  align-items: center;
  padding: 0 16px;
  font-size: 13px;
}
</style>
