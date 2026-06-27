import api from './index'

export function getLearningPath(course = 'computer_organization') {
  return api.get('/path/get', { params: { course } })
}
