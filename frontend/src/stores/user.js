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
    setProfile({
      major: '计算机类',
      grade: '大二',
      course_goal: '系统掌握计算机组成原理，重点突破 Cache 映射和流水线冲突',
      weak_points: ['Cache 映射方式', '流水线冲突'],
      learning_preference: ['图解学习', '例题驱动', '代码示例'],
      pace: '中等节奏',
      resource_preference: ['讲解文档', '思维导图', '练习题'],
      mastery: {
        数据表示: 0.86,
        指令系统: 0.78,
        'Cache 映射方式': 0.42,
        流水线冲突: 0.38
      }
    }, 'demo')
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
    logout
  }
})

function normalizeProfile(profile) {
  return {
    major: profile?.major || '',
    grade: profile?.grade || '',
    course_goal: profile?.course_goal || '',
    knowledge_base: profile?.knowledge_base || {},
    weak_points: Array.isArray(profile?.weak_points) ? profile.weak_points : [],
    learning_preference: Array.isArray(profile?.learning_preference) ? profile.learning_preference : [],
    pace: profile?.pace || '',
    resource_preference: Array.isArray(profile?.resource_preference) ? profile.resource_preference : [],
    mastery: profile?.mastery || {}
  }
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
