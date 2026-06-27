import api from './index'

export function submitQuiz(answers) {
  return api.post('/quiz/submit', { answers })
}
