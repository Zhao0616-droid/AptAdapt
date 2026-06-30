import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
const fallbackCourses = [
  {
    id: 'computer_organization',
    name: '计算机组成原理',
    description: '当前仅扩充计算机组成原理课程，其他课程暂未扩充。',
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
    courses.value = [...fallbackCourses]
    loaded.value = true
    if (!courses.value.find(c => c.id === currentId.value)) {
      currentId.value = 'computer_organization'
      localStorage.setItem('currentCourse', currentId.value)
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
