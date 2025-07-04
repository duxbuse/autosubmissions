import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../views/HomePage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage
    },
    {
      path: '/form/submit/:id',
      name: 'form-submit',
      component: () => import('../views/FormSubmitter.vue')
    },
    {
      path: '/form/build/:id',
      name: 'form-build',
      component: () => import('../views/FormBuilder.vue')
    }
  ]
})

export default router

