import api from './index'

export function sendMessage(message, chapter = '') {
  return api.post('/chat/send', { message, chapter })
}

export function getProfile() {
  return api.get('/profile/get')
}

export function generateResource(knowledgePoint, resourceTypes) {
  return api.post('/resource/generate', {
    knowledge_point: knowledgePoint,
    resource_types: resourceTypes
  })
}
