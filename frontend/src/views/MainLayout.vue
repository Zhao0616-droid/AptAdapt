<template>
  <div class="workspace">
    <!-- 左侧: 学习路径树 -->
    <aside class="sidebar-left">
      <div class="sidebar-header">
        <h2>AptAdapt</h2>
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
import { ref } from 'vue'
import ChatPanel from '../components/ChatPanel.vue'
import PathTree from '../components/PathTree.vue'
import ResourcePanel from '../components/ResourcePanel.vue'
import ProfileCard from '../components/ProfileCard.vue'
import EvaluationPanel from '../components/EvaluationPanel.vue'
import AgentStatusBar from '../components/AgentStatusBar.vue'

const activeTab = ref('resources')
</script>

<style scoped>
.workspace {
  display: grid;
  grid-template-columns: 260px 1fr 320px;
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
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}
.sidebar-header h2 {
  font-size: 18px;
  color: #303133;
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
