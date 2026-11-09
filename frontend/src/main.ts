import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { api } from './api/client'
import { authMiddleware } from './api/auth'
import { useAuth } from './stores/auth'

const app = createApp(App)

app.use(createPinia())
api.use(authMiddleware)
// Recuperar a sessão antes do router: o guard decide com informação certa no 1.º ecrã
await useAuth().bootstrap()
app.use(router)

app.mount('#app')
