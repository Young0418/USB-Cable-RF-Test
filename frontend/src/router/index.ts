import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/detection',
    },
    {
      path: '/detection',
      name: 'detection',
      component: () => import('@/views/DetectionView.vue'),
      meta: { title: '单次检测' },
    },
    {
      path: '/batch',
      name: 'batch',
      component: () => import('@/views/BatchDetectionView.vue'),
      meta: { title: '批量检测' },
    },
    {
      path: '/agent',
      name: 'agent',
      component: () => import('@/views/AgentChatView.vue'),
      meta: { title: 'AI 助手' },
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('@/views/HistoryView.vue'),
      meta: { title: '历史记录' },
    },
    {
      path: '/thresholds',
      name: 'thresholds',
      component: () => import('@/views/ThresholdsView.vue'),
      meta: { title: '阈值标准' },
    },
  ],
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? '')} - USB 线缆射频测试系统`
})

export default router
