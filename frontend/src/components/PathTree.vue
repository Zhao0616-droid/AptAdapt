<template>
  <div class="path-tree">
    <h3 class="tree-title">学习路径</h3>
    <el-tree
      :data="treeData"
      :props="{ children: 'children', label: 'label' }"
      node-key="id"
      default-expand-all
      highlight-current
    >
      <template #default="{ data }">
        <span class="tree-node">
          <el-icon v-if="data.status === 'done'" color="#67c23a"><Check /></el-icon>
          <el-icon v-else-if="data.status === 'current'" color="#409eff"><Loading /></el-icon>
          <el-icon v-else color="#c0c4cc"><Clock /></el-icon>
          <span :class="{ 'text-done': data.status === 'done', 'text-current': data.status === 'current' }">
            {{ data.label }}
          </span>
        </span>
      </template>
    </el-tree>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const treeData = ref([
  {
    id: '1',
    label: '1. 计算机系统概述',
    status: 'done',
    children: []
  },
  {
    id: '2',
    label: '2. 数据表示与编码',
    status: 'current',
    children: [
      { id: '2-1', label: '定点数与浮点数', status: 'current' },
      { id: '2-2', label: '运算器与ALU', status: 'pending' }
    ]
  },
  {
    id: '3',
    label: '3. 存储器层次结构',
    status: 'pending',
    children: [
      { id: '3-1', label: 'Cache基本原理', status: 'pending' },
      { id: '3-2', label: 'Cache映射方式', status: 'pending' }
    ]
  },
  {
    id: '4',
    label: '4. 指令系统与CPU',
    status: 'pending',
    children: []
  },
  {
    id: '5',
    label: '5. 流水线技术',
    status: 'pending',
    children: []
  }
])
</script>

<style scoped>
.path-tree {
  padding: 12px;
}
.tree-title {
  font-size: 15px;
  padding: 8px 0 12px;
  color: #303133;
}
.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}
.text-done { color: #67c23a; }
.text-current { color: #409eff; font-weight: 600; }
</style>
