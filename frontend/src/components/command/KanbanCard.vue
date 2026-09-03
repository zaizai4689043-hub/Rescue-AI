<script setup>
/** 看板单卡：优先级色条 + 位置/人数 + SLA 倒计时 + 负责员工 */
import { computed } from 'vue'
import { useRescueStore } from '../../stores/rescue'
import { PRIORITY_COLORS } from '../../utils/constants'

const props = defineProps({ task: { type: Object, required: true } })
const store = useRescueStore()

const remain = computed(() => store.slaRemain(props.task.eventId))
const text = computed(() => {
  const s = Math.max(0, Math.floor(remain.value))
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
})
const urgent = computed(() => remain.value < props.task.sla * 0.2)
const priorityColor = computed(() => PRIORITY_COLORS[props.task.priority] || PRIORITY_COLORS.P2)
const info = computed(() => {
  const loc = props.task.extracted?.location || props.task.location
  const persons = props.task.extracted?.persons && props.task.extracted.persons !== '-'
    ? ` · ${props.task.extracted.persons}` : ''
  return loc + persons
})
const agent = computed(() =>
  ({ new: '🛰', pending: '🧠', dispatched: '📡', verify: '🔍', closed: '✅' }[props.task.status] || '❓')
)
const selected = computed(() => store.selectedTaskId === props.task.eventId)
</script>

<template>
  <div
    class="cs-kanban-card entering"
    :class="{ selected, 'cs-link-highlight': selected }"
    @click="store.selectTask(task.eventId)"
  >
    <div class="cs-kanban-priority" :style="{ background: priorityColor }"></div>
    <div class="cs-kanban-info">{{ info }}</div>
    <div class="cs-kanban-sla" :style="{ color: urgent ? '#FB4B6B' : '#38E1FF' }">⏱{{ text }}</div>
    <div class="cs-kanban-agent">{{ agent }}</div>
  </div>
</template>
