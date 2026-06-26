import api from './index'

export function sendMessage(message, course = 'computer_organization', chapter = '') {
  return api.post('/chat/send', { message, course, chapter })
}
