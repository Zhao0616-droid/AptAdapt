import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi } from '../api/auth'
import { getProfile } from '../api/profile'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const profile = ref(null)
  const profileSource = ref('empty')
  const profileError = ref('')
  const isLoggedIn = ref(!!token.value)

  async function login(username, password) {
    const res = await loginApi(username, password)
    token.value = res.data.access_token
    localStorage.setItem('token', token.value)
    localStorage.removeItem('demoMode')
    isLoggedIn.value = true
    await fetchProfile().catch(() => {})
  }

  function enterDemoMode() {
    token.value = 'demo-token'
    localStorage.setItem('token', token.value)
    localStorage.setItem('demoMode', '1')
    isLoggedIn.value = true
    applyCoursePersona(localStorage.getItem('currentCourse') || 'computer_organization')
  }

  async function fetchProfile() {
    const res = await getProfile()
    const nextProfile = normalizeProfile(res.data?.profile)
    profile.value = hasProfileContent(nextProfile) ? nextProfile : null
    profileSource.value = profile.value ? 'remote' : 'empty'
    profileError.value = ''
    return profile.value
  }

  function setProfile(profileData, source = 'remote') {
    const nextProfile = normalizeProfile(profileData)
    profile.value = hasProfileContent(nextProfile) ? nextProfile : null
    profileSource.value = profile.value ? source : 'empty'
    profileError.value = ''
  }

  function setProfileError(message) {
    profileError.value = message
  }

  function applyCoursePersona(courseId = 'computer_organization') {
    const persona = COURSE_PERSONAS[courseId] || COURSE_PERSONAS.computer_organization
    setProfile(persona, 'course')
  }

  function logout() {
    token.value = ''
    profile.value = null
    profileSource.value = 'empty'
    profileError.value = ''
    isLoggedIn.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('demoMode')
  }

  return {
    token,
    profile,
    profileSource,
    profileError,
    isLoggedIn,
    login,
    enterDemoMode,
    fetchProfile,
    setProfile,
    setProfileError,
    applyCoursePersona,
    logout
  }
})

const COURSE_PERSONAS = {
  computer_organization: {
    major: '计算机类',
    grade: '大二',
    course_goal: '系统掌握计算机组成原理，重点突破 Cache 映射和流水线冲突',
    knowledge_base: { digital_logic: '中等', assembly: '较弱', computer_architecture: '入门' },
    weak_points: ['Cache 映射方式', '流水线冲突'],
    learning_preference: ['图解学习', '例题驱动', '代码示例'],
    pace: '每天 1 小时',
    resource_preference: ['讲解文档', '思维导图', '练习题'],
    mastery: {
      数据表示: 0.86,
      指令系统: 0.78,
      'Cache 映射方式': 0.42,
      流水线冲突: 0.38
    }
  },
  data_structure: {
    major: '软件工程',
    grade: '大一',
    course_goal: '用两周补齐树、图和排序算法，为算法课打基础',
    knowledge_base: { programming: '较好', math: '中等', abstraction: '较弱' },
    weak_points: ['二叉树遍历', '图的最短路径', '快速排序'],
    learning_preference: ['动画演示', '手算例题', '代码模板'],
    pace: '每天 45 分钟',
    resource_preference: ['可视化导图', '练习题', '伪代码'],
    mastery: {
      线性表: 0.82,
      栈与队列: 0.74,
      二叉树遍历: 0.36,
      图的最短路径: 0.31,
      快速排序: 0.48
    }
  },
  operating_system: {
    major: '网络空间安全',
    grade: '大三',
    course_goal: '理解进程调度、内存管理和死锁处理，准备期末复习',
    knowledge_base: { c_programming: '中等', computer_architecture: '较好', concurrency: '较弱' },
    weak_points: ['进程同步', '页面置换算法', '死锁检测'],
    learning_preference: ['流程图', '场景推演', '对比表格'],
    pace: '每天 1.5 小时',
    resource_preference: ['讲解文档', '流程图', '案例题'],
    mastery: {
      操作系统概述: 0.88,
      进程调度: 0.66,
      进程同步: 0.4,
      页面置换算法: 0.44,
      死锁检测: 0.35
    }
  },
  computer_network: {
    major: '物联网工程',
    grade: '大二',
    course_goal: '建立 TCP/IP 分层模型，重点搞懂路由和可靠传输',
    knowledge_base: { digital_communication: '入门', protocol_stack: '较弱', programming: '中等' },
    weak_points: ['子网划分', 'TCP 拥塞控制', '路由选择算法'],
    learning_preference: ['抓包示例', '分层图解', '生活类比'],
    pace: '每天 1 小时',
    resource_preference: ['思维导图', '协议流程图', '练习题'],
    mastery: {
      网络概述: 0.8,
      数据链路层: 0.62,
      子网划分: 0.34,
      'TCP 拥塞控制': 0.37,
      路由选择算法: 0.46
    }
  }
}

function normalizeProfile(profile) {
  return {
    major: profile?.major || '',
    grade: profile?.grade || '',
    course_goal: profile?.course_goal || '',
    knowledge_base: profile?.knowledge_base || {},
    weak_points: dedupeSimilarItems(Array.isArray(profile?.weak_points) ? profile.weak_points : []),
    learning_preference: dedupeSimilarItems(Array.isArray(profile?.learning_preference) ? profile.learning_preference : []),
    pace: profile?.pace || '',
    resource_preference: dedupeSimilarItems(Array.isArray(profile?.resource_preference) ? profile.resource_preference : []),
    mastery: profile?.mastery || {}
  }
}

function normalizeTagKey(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[，,、/|｜;；:：()（）【】\[\]{}<>《》"'“”‘’·.\-_\s]/g, '')
    .replace(/方式|知识点|核心|相关|学习|掌握|理解|生成/g, '')
}

function dedupeSimilarItems(items = []) {
  const result = []
  const keys = []
  const tokenSets = []
  for (const item of items) {
    const text = String(item || '').trim()
    const key = normalizeTagKey(text)
    if (!text || !key) continue
    const tokens = semanticTokens(key)
    const duplicateIndex = keys.findIndex((existing, index) =>
      existing === key ||
      existing.includes(key) ||
      key.includes(existing) ||
      isSimilarTokenSet(tokens, tokenSets[index])
    )
    if (duplicateIndex >= 0) {
      if (text.length < result[duplicateIndex].length) {
        result[duplicateIndex] = text
        keys[duplicateIndex] = key
        tokenSets[duplicateIndex] = tokens
      }
      continue
    }
    result.push(text)
    keys.push(key)
    tokenSets.push(tokens)
  }
  return result
}

function semanticTokens(key) {
  const tokens = new Set()
  const concepts = ['cache', '映射', '直接映射', '全相联', '组相联', '流水线', '冲突', '中断', 'dma', '代码', '图解', '资源', '原理']
  for (const concept of concepts) {
    if (key.includes(concept)) tokens.add(concept)
  }
  if (!tokens.size) {
    for (const char of key) tokens.add(char)
  }
  return tokens
}

function isSimilarTokenSet(a, b) {
  if (!a?.size || !b?.size) return false
  const intersection = [...a].filter(token => b.has(token))
  if (intersection.length < 2) return false
  return intersection.length / Math.min(a.size, b.size) >= 0.66
}

function hasProfileContent(profile) {
  return Boolean(
    profile.major ||
    profile.grade ||
    profile.course_goal ||
    profile.pace ||
    profile.weak_points.length ||
    profile.learning_preference.length ||
    profile.resource_preference.length ||
    Object.keys(profile.knowledge_base || {}).length ||
    Object.keys(profile.mastery || {}).length
  )
}
