/**
 * 灾情全局 Store
 * 管理灾情态势、微博数据、热点等跨页面共享状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getFunnel, rebuildHotspots, refreshPriority } from '../api/weibo'
import { getDashboard } from '../api/analytics'

export const useDisasterStore = defineStore('disaster', () => {
  // State
  const funnel = ref(null)
  const dashboard = ref(null)
  const loading = ref(false)

  // Getters
  const totalPosts = computed(() => funnel.value?.active || 0)
  const distressCount = computed(() => funnel.value?.distress_signals || 0)

  // Actions
  async function fetchFunnel() {
    try {
      const res = await getFunnel()
      funnel.value = res.data
    } catch (e) {
      console.error('获取数据漏斗失败:', e)
    }
  }

  async function fetchDashboard() {
    loading.value = true
    try {
      const res = await getDashboard()
      dashboard.value = res.data
    } catch (e) {
      console.error('获取仪表盘数据失败:', e)
    } finally {
      loading.value = false
    }
  }

  async function rebuildAll() {
    loading.value = true
    try {
      await rebuildHotspots()
      await refreshPriority(true)
      await fetchFunnel()
      await fetchDashboard()
    } catch (e) {
      console.error('重建失败:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    funnel,
    dashboard,
    loading,
    totalPosts,
    distressCount,
    fetchFunnel,
    fetchDashboard,
    rebuildAll,
  }
})
