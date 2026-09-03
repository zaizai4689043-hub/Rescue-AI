<script setup>
/**
 * 左栏：哨兵·社媒情报流。
 * 每条卡片两态：AI萃取中（打字机+扫描线）→ 已萃取（徽章点亮+定位/入看板标记）。
 * 打字机进度用本地 reactive map 按 eventId 管理。
 */
import { reactive, computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { storeToRefs } from 'pinia'
import { useRescueStore } from '../../stores/rescue'

const store = useRescueStore()
const { tasks, stats, selectedTaskId } = storeToRefs(store)

// 非拦截帖按注入时间倒序（新卡在上）
const feedTasks = computed(() =>
  tasks.value.filter(t => t.status !== 'intercepted').slice().reverse()
)
const interceptedTasks = computed(() => tasks.value.filter(t => t.status === 'intercepted'))

// 打字机：每个卡片当前已显示字符数
const typedLen = reactive({})
const TYPE_SPEED = 25 // ms/字符

watch(feedTasks, (list) => {
  list.forEach(t => {
    if (typedLen[t.eventId] === undefined) typedLen[t.eventId] = 0
  })
}, { immediate: true })

function typedText(task) {
  return task.sourceText.slice(0, typedLen[task.eventId] || 0)
}
function isTyping(task) {
  return (typedLen[task.eventId] || 0) < task.sourceText.length
}
function tickTyping() {
  feedTasks.value.forEach(t => {
    if (isTyping(t)) {
      typedLen[t.eventId] = Math.min(t.sourceText.length, (typedLen[t.eventId] || 0) + 1)
      // 打字完成 → 计入萃取统计（幂等）
      if (!isTyping(t) && !t._counted) {
        t._counted = true
        store.stats.extracted++
      }
    }
  })
}
// 打字机心跳
let typer = null
onMounted(() => { typer = setInterval(tickTyping, TYPE_SPEED) })
onBeforeUnmount(() => clearInterval(typer))

const interceptOpen = ref(false)

function select(id) { store.selectTask(id) }
function isSelected(id) { return selectedTaskId.value === id }
</script>

<template>
  <div class="cs-panel cs-feed deck-rise">
    <div class="cs-panel-title">🛰 哨兵 · 社媒情报流</div>
    <div class="cs-feed-stats">
      原始 <b>{{ stats.raw }}</b> 条 ·
      萃取 <b>{{ stats.extracted }}</b> 条 ·
      拦截 <b>{{ stats.intercepted }}</b> 条
    </div>
    <div class="cs-feed-list">
      <div
        v-for="task in feedTasks"
        :key="task.eventId"
        class="cs-feed-card entering"
        :class="{ selected: isSelected(task.eventId), 'cs-link-highlight': isSelected(task.eventId) }"
        @click="select(task.eventId)"
      >
        <div v-if="isTyping(task)" class="cs-scan-line"></div>
        <div class="cs-feed-source" :class="{ 'cs-typewriter': isTyping(task) }">
          {{ typedText(task) }}
        </div>
        <div class="cs-feed-badges" :class="{ visible: !isTyping(task) }">
          <span class="cs-badge cs-badge-type">{{ task.extracted?.type }}</span>
          <span class="cs-badge cs-badge-loc">{{ task.extracted?.location }}</span>
          <span class="cs-badge cs-badge-score">可信度 {{ task.credibility }}/100</span>
        </div>
        <div class="cs-feed-marks" :class="{ visible: !isTyping(task) }">
          🗺 已定位 · 📋 已入看板
        </div>
      </div>
    </div>
    <div class="cs-intercept-toggle" @click="interceptOpen = !interceptOpen">
      {{ interceptOpen ? '▲' : '▼' }} 拦截区 ({{ interceptedTasks.length }})
    </div>
    <div class="cs-intercept-list" :class="{ open: interceptOpen }">
      <div v-for="task in interceptedTasks" :key="task.eventId" class="cs-intercept-item">
        {{ task.sourceText }}
        <div class="cs-intercept-reason">🚫 {{ task.interceptReason }}</div>
      </div>
    </div>
  </div>
</template>
