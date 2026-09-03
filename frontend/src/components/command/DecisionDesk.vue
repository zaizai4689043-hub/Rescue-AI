<script setup>
/**
 * 右栏：参谋·决策桌。
 * 概览态（无选中）：4 KPI + 三数字员工卡。
 * 详情态（选中任务）：原始情报、萃取字段、参谋研判(真Qwen/规则)、SLA倒计时、批准/驳回。
 */
import { computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRescueStore } from '../../stores/rescue'
import { useCountdown } from '../../composables/useCountdown'
import { getAiAdvisory } from '../../api/ai'
import AdvisoryCard from '../AdvisoryCard.vue'
import { SIGNAL_TYPE_LABELS } from '../../utils/constants'

const store = useRescueStore()
const { selectedTask, clockSeconds } = storeToRefs(store)

// SLA 倒计时（响应式）
const remain = computed(() => selectedTask.value ? store.slaRemain(selectedTask.value.eventId) : 0)
const { text: slaText, urgent: slaUrgent } = useCountdown(remain, computed(() => selectedTask.value?.sla || 0))

const advisory = computed(() => selectedTask.value ? store.getAdvisory(selectedTask.value.eventId) : null)
const canApprove = computed(() => selectedTask.value?.status === 'pending')
const isApproved = computed(() => ['dispatched', 'verify', 'closed'].includes(selectedTask.value?.status))

// 选中任务变化时加载参谋研判（缓存优先，避免重复调用）
watch(selectedTask, async (task) => {
  if (!task || task.status === 'intercepted') return
  if (store.getAdvisory(task.eventId)) return
  try {
    const res = await getAiAdvisory({
      text: task.sourceText,
      signal_type: task.signalType || 'unknown',
      geo_name: task.location,
      latitude: task.lat,
      longitude: task.lng,
      confidence: task.confidence ?? 0.5,
      urgency_hint: task.urgencyHint,
      sentiment: task.sentiment,
    })
    // 缓存结果（同帖复用，避免重复烧 token）
    store.setAdvisory(task.eventId, res.data)
  } catch (e) {
    console.warn('[desk] advisory 加载失败:', e?.message)
  }
})

function approve() { if (selectedTask.value) store.approveTask(selectedTask.value.eventId) }
function reject() { if (selectedTask.value) store.rejectTask(selectedTask.value.eventId) }
function relevel() {
  alert(`改级功能演示：可将 ${selectedTask.value?.priority} 调整为其他等级`)
}
</script>

<template>
  <div class="cs-panel cs-desk deck-rise deck-rise-2">
    <div class="cs-panel-title">🧠 参谋 · 决策桌</div>
    <div class="cs-desk-content">
      <!-- 概览态 -->
      <template v-if="!selectedTask">
        <div class="cs-kpi-grid">
          <div class="cs-kpi-card">
            <div class="cs-kpi-value cyan deck-numeric">{{ store.kpis.avgClosedMin || '--' }}<span style="font-size:14px"> min</span></div>
            <div class="cs-kpi-label">平均闭环时间</div>
          </div>
          <div class="cs-kpi-card">
            <div class="cs-kpi-value green deck-numeric">{{ store.kpis.slaRate || '--' }}<span style="font-size:14px">%</span></div>
            <div class="cs-kpi-label">SLA达标率</div>
          </div>
          <div class="cs-kpi-card">
            <div class="cs-kpi-value amber deck-numeric">{{ store.kpis.intercepted }}</div>
            <div class="cs-kpi-label">误报拦截数</div>
          </div>
          <div class="cs-kpi-card">
            <div class="cs-kpi-value rose deck-numeric">{{ store.kpis.pending }}</div>
            <div class="cs-kpi-label">待批准数</div>
          </div>
        </div>
        <div class="cs-agent-card"><div class="emoji">🛰</div><div><div class="name">哨兵</div><div class="status">持续监听社交媒体数据流，实时萃取灾情要素</div></div></div>
        <div class="cs-agent-card"><div class="emoji">🧠</div><div><div class="name">参谋</div><div class="status">基于多源交叉验证生成处置方案，等待指挥长决策</div></div></div>
        <div class="cs-agent-card"><div class="emoji">📡</div><div><div class="name">通讯员</div><div class="status">跟踪已派遣任务执行进度，协调现场反馈闭环</div></div></div>
      </template>

      <!-- 详情态 -->
      <template v-else>
        <div class="cs-detail-section">
          <div class="cs-detail-label">事件编号</div>
          <div class="cs-detail-value deck-mono">
            {{ selectedTask.eventId }} · {{ selectedTask.priority }} · {{ selectedTask.extracted?.type || selectedTask.type }}
          </div>
        </div>
        <div class="cs-detail-section">
          <div class="cs-detail-label">原始情报</div>
          <div class="cs-detail-source">{{ selectedTask.sourceText }}</div>
        </div>
        <div class="cs-detail-section">
          <div class="cs-detail-label">萃取字段</div>
          <div class="cs-detail-value">
            类型：{{ selectedTask.extracted?.type || '-' }}<br />
            位置：{{ selectedTask.extracted?.location || '-' }}<br />
            人数：{{ selectedTask.extracted?.persons || '-' }}
          </div>
        </div>

        <div class="cs-detail-section">
          <AdvisoryCard v-if="advisory" :advisory="advisory" />
          <div v-else class="cs-detail-source" style="text-align:center;color:var(--deck-text-3)">🧠 参谋研判中…</div>
        </div>

        <div class="cs-sla-countdown deck-mono" :class="slaUrgent ? 'urgent' : 'normal'">
          ⏱ SLA {{ slaText }}
        </div>

        <div class="cs-desk-actions">
          <button class="cs-desk-btn approve" :disabled="!canApprove" @click="approve">批准派遣</button>
          <button class="cs-desk-btn relevel" @click="relevel">改级</button>
          <button class="cs-desk-btn reject" :disabled="!canApprove" @click="reject">驳回</button>
        </div>

        <div v-if="isApproved" class="cs-approval-stamp">
          ✔ 已由指挥长批准 · 决策责任：人
        </div>
      </template>
    </div>
  </div>
</template>
