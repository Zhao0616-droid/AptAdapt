import api from './index'

export function getEvaluation(userId = 'demo_user') {
  return api.get('/evaluation/get', {
    params: {
      user_id: userId
    }
  })
}
