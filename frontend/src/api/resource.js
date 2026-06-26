import api from './index'

export function generateResource(
  knowledgePoint,
  resourceTypes,
  course = 'computer_organization',
  userId = 'demo_user'
) {
  return api.post('/resource/generate', {
    user_id: userId,
    course,
    knowledge_point: knowledgePoint,
    resource_types: resourceTypes
  })
}
