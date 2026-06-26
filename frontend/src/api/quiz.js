import api from './index'

export function submitQuiz(answers, userId = 'demo_user') {
  return api.post('/quiz/submit', { answers }, {
    params: {
      user_id: userId
    }
  })
}
