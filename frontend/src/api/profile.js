import api from './index'

export function getProfile(userId = 'demo_user') {
  return api.get('/profile/get', {
    params: {
      user_id: userId
    }
  })
}

export function updateProfile(profile, userId = 'demo_user') {
  return api.post('/profile/update', { profile }, {
    params: {
      user_id: userId
    }
  })
}
