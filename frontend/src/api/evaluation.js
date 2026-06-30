import api from './index'

export function getEvaluation() {
  return api.get('/evaluation/get', { timeout: 15000 })
}
