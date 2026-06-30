import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './assets/theme.css'

window.addEventListener('error', (event) => {
  console.error('[AptAdapt boot error]', event.error || event.message)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('[AptAdapt async error]', event.reason)
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
