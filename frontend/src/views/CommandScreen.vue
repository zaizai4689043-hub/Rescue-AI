<script setup>
/**
 * 指挥大屏壳：2560×1440 基准容器 + transform scale 适配。
 * 单一 setInterval 驱动 store.tick()（秒级心跳），所有 SLA/时钟为响应式。
 */
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useRescueStore } from '../stores/rescue'
import FeedStream from '../components/command/FeedStream.vue'
import GeoMap from '../components/command/GeoMap.vue'
import DecisionDesk from '../components/command/DecisionDesk.vue'
import TaskKanban from '../components/command/TaskKanban.vue'
import '../styles/command-screen.css'

const router = useRouter()
const store = useRescueStore()
const { clockSeconds, dataSource, dataSourceDetail, lastIngestAt } = storeToRefs(store)

// ---- 缩放适配 ----
const scale = ref(1)
function resize() {
  scale.value = Math.min(window.innerWidth / 2560, window.innerHeight / 1440)
}

// ---- T+ 时钟 ----
const clock = computed(() => {
  const h = String(Math.floor(clockSeconds.value / 3600)).padStart(2, '0')
  const m = String(Math.floor((clockSeconds.value % 3600) / 60)).padStart(2, '0')
  const s = String(clockSeconds.value % 60).padStart(2, '0')
  return `T+${h}:${m}:${s}`
})

// ---- 数据源徽章样式 ----
const dsStyle = computed(() => {
  const map = {
    live: { color: '#2DD4BF', border: 'rgba(45,212,191,0.3)', bg: 'rgba(45,212,191,0.1)', label: '🟢 实时数据' },
    mock: { color: '#FFB020', border: 'rgba(255,176,32,0.3)', bg: 'rgba(255,176,32,0.1)', label: '🟡 Mock回放' },
    offline: { color: '#FB4B6B', border: 'rgba(251,75,107,0.3)', bg: 'rgba(251,75,107,0.1)', label: '🔴 离线模式' },
    detecting: { color: '#5A6B8A', border: 'var(--deck-border)', bg: 'rgba(255,255,255,0.03)', label: '⏳ 检测数据源…' },
  }
  return map[dataSource.value] || map.detecting
})

// ---- 哨兵闪烁（近 2s 内有新情报注入） ----
const now = ref(Date.now())
const sentinelFlash = computed(() => now.value - lastIngestAt.value < 2000)

// ---- 心跳：时钟 + 秒级刷新 ----
let heart = null
let nowTick = null
onMounted(() => {
  resize()
  window.addEventListener('resize', resize)
  heart = setInterval(() => store.tick(), 1000)
  nowTick = setInterval(() => { now.value = Date.now() }, 500)
  store.hydrateFromApi()
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  clearInterval(heart)
  clearInterval(nowTick)
})

function exit() { router.push('/command-center') }
</script>

<template>
  <div class="cs-root">
    <div class="cs-scale" :style="{ transform: `translate(-50%,-50%) scale(${scale})` }">
      <div class="cs-layout">
        <!-- 顶栏 -->
        <div class="cs-panel cs-header">
          <div class="cs-logo">Rescue<span>AI</span> 指挥中心</div>
          <div class="cs-clock">{{ clock }}</div>
          <div class="cs-agents">
            <div class="cs-agent" :class="{ flash: sentinelFlash }">
              <div class="cs-agent-avatar">🛰</div>
              <div><div class="cs-agent-name">哨兵</div><div class="cs-agent-status">监听中</div></div>
              <div class="cs-agent-dot green"></div>
            </div>
            <div class="cs-agent">
              <div class="cs-agent-avatar">🧠</div>
              <div><div class="cs-agent-name">参谋</div><div class="cs-agent-status">待命</div></div>
              <div class="cs-agent-dot yellow"></div>
            </div>
            <div class="cs-agent">
              <div class="cs-agent-avatar">📡</div>
              <div><div class="cs-agent-name">通讯员</div><div class="cs-agent-status">跟踪中</div></div>
              <div class="cs-agent-dot blue"></div>
            </div>
          </div>
          <div class="cs-commander">👨‍✈️ 指挥长在线</div>
          <div class="cs-datasource" :style="{ color: dsStyle.color, borderColor: dsStyle.border, background: dsStyle.bg }">
            {{ dsStyle.label }} · {{ dataSourceDetail || '...' }}
          </div>
          <button class="cs-exit" @click="exit">← 返回工作台</button>
        </div>

        <!-- 左：社媒流 -->
        <FeedStream />
        <!-- 中：地图 -->
        <GeoMap />
        <!-- 右：决策桌 -->
        <DecisionDesk />
        <!-- 底：看板 -->
        <TaskKanban />
      </div>
    </div>
  </div>
</template>
