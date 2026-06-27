import api from './index'

export function sendMessage(message, course = 'computer_organization', chapter = '') {
  return api.post('/chat/send', { message, course, chapter }, { timeout: 120000 })
}

export function streamMessage(message, course = 'computer_organization', chapter = '') {
  return api.post('/chat/stream', { message, course, chapter }, {
    responseType: 'stream'
  })
}
