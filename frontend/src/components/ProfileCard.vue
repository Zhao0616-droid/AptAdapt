<template>
  <div class="profile-card">
    <h4>学习画像</h4>
    <el-descriptions :column="1" size="small" border v-if="profile">
      <el-descriptions-item label="专业">{{ profile.major }}</el-descriptions-item>
      <el-descriptions-item label="年级">{{ profile.grade }}</el-descriptions-item>
      <el-descriptions-item label="学习目标">{{ profile.course_goal }}</el-descriptions-item>
      <el-descriptions-item label="薄弱点">
        <el-tag v-for="w in profile.weak_points" :key="w" size="small" type="danger" style="margin:2px">
          {{ w }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="学习偏好">
        <el-tag v-for="p in profile.learning_preference" :key="p" size="small" style="margin:2px">
          {{ p }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>
    <div v-else class="empty">请在对话中描述你的学习情况，AI 将自动生成画像</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const profile = computed(() => userStore.profile)
</script>

<style scoped>
.profile-card { padding: 4px; }
h4 { margin-bottom: 12px; }
.empty { color: #909399; font-size: 14px; text-align: center; padding: 20px 0; }
</style>
