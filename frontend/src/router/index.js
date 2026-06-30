import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import MainLayout from '../views/MainLayout.vue'

const routes = [
  {
    path: '/',
    redirect: '/workspace'
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView
  },
  {
    path: '/workspace',
    name: 'Workspace',
    component: MainLayout,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !localStorage.getItem('token')) {
    localStorage.setItem('token', 'demo-token')
    localStorage.setItem('demoMode', '1')
  }
  next()
})

router.onError((error) => {
  console.error('[AptAdapt router error]', error)
  localStorage.removeItem('token')
  localStorage.removeItem('demoMode')
  window.location.href = '/login'
})

export default router
