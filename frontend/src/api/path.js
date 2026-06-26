import api from './index'

export function getLearningPath(userId = 'demo_user', course = 'computer_organization') {
  return api.get('/path/get', {
    params: {
      user_id: userId,
      course
    }
  })
}
