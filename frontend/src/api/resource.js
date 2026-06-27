import api from './index'

export function generateResource(knowledgePoint, resourceTypes, course = 'computer_organization') {
  return api.post('/resource/generate', {
    course,
    knowledge_point: knowledgePoint,
    resource_types: resourceTypes
  }, { timeout: 120000 })
}
