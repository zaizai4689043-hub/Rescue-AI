<script setup>
/**
 * 底栏：任务看板（5列）。
 * 列内按 SLA 剩余升序排序；已派遣列 WIP 上限 6，超载弹提示。
 */
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useRescueStore } from '../../stores/rescue'
import KanbanCard from './KanbanCard.vue'

const store = useRescueStore()
const { tasks } = storeToRefs(store)

const COLUMNS = [
  { status: 'new', title: '📥 新情报', human: false },
  { status: 'pending', title: '⚠ 待批准·人类权力区', human: true },
  { status: 'dispatched', title: '📡 已派遣', human: false },
  { status: 'verify', title: '🔍 待核验', human: false },
  { status: 'closed', title: '✅ 已闭环', human: false },
]
const DISPATCH_WIP = 6

function columnTasks(status) {
  return tasks.value
    .filter(t => t.status === status)
    .sort((a, b) => store.slaRemain(a.eventId) - store.slaRemain(b.eventId))
}

const overloaded = computed(() =>
  tasks.value.filter(t => t.status === 'dispatched').length > DISPATCH_WIP
)
</script>

<template>
  <div class="cs-panel cs-kanban deck-rise deck-rise-3">
    <div
      v-for="col in COLUMNS"
      :key="col.status"
      class="cs-kanban-col"
      :class="{ 'human-zone': col.human, overload: col.status === 'dispatched' && overloaded }"
    >
      <div class="cs-kanban-col-header">
        {{ col.title }}
        <span class="cs-kanban-count">{{ columnTasks(col.status).length }}</span>
      </div>
      <div class="cs-kanban-body">
        <KanbanCard v-for="t in columnTasks(col.status)" :key="t.eventId" :task="t" />
        <div v-if="col.status === 'dispatched' && overloaded" class="cs-overload-toast">
          产能超载 · 建议升级响应级别
        </div>
      </div>
    </div>
  </div>
</template>
