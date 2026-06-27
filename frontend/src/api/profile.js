import api from './index'

export function getProfile() {
  return api.get('/profile/get')
}

export function updateProfile(profile) {
  return api.post('/profile/update', { profile })
}
