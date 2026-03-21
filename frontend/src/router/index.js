import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('../views/HomePage.vue'),
  },
  {
    path: '/admin',
    component: () => import('../views/AdminPage.vue'),
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
