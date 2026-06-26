import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { fetchCourses } from '../api/course'

const fallbackCourses = [
  {
    id: 'computer_organization',
    name: '计算机组成原理',
    description: '围绕计算机组成原理构建个性化资源生成闭环。',
    chapters: []
  }
]

export const useCourseStore = defineStore('course', () => {
  const courses = ref([...fallbackCourses])
  const currentId = ref(localStorage.getItem('currentCourse') || 'computer_organization')
  const loaded = ref(false)

  const currentCourse = computed(() =>
    courses.value.find(c => c.id === currentId.value) || courses.value[0]
  )

  async function loadCourses() {
    if (loaded.value && courses.value.length > 0) return
    try {
      const res = await fetchCourses()
      courses.value = res.data.courses?.length ? res.data.courses : [...fallbackCourses]
      loaded.value = true
      if (!courses.value.find(c => c.id === currentId.value)) {
        currentId.value = res.data.default || courses.value[0]?.id
      }
    } catch {
      courses.value = [...fallbackCourses]
      loaded.value = false
    }
  }

  function switchCourse(courseId) {
    if (courses.value.find(c => c.id === courseId)) {
      currentId.value = courseId
      localStorage.setItem('currentCourse', courseId)
    }
  }

  return { courses, currentId, currentCourse, loaded, loadCourses, switchCourse }
})
