<template>
  <div class="cmd-dashboard">
    <!-- 顶部状态条 -->
    <div class="cmd-topline deck-rise">
      <div class="topline-title">
        <h1>灾情总览</h1>
        <span class="topline-sub">DISASTER OVERVIEW · 实时数据流</span>
      </div>
      <div class="ai-insight">
        <div class="insight-icon">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none">
            <path d="M12 2l1.9 5.7L20 9.5l-5.6 2.3L12 18l-2.4-6.2L4 9.5l6.1-1.8L12 2z" fill="#A78BFA"/>
          </svg>
        </div>
        <span class="insight-text">{{ aiInsight }}</span>
        <span class="insight-tag">AI</span>
      </div>
      <div v-if="slaChip" class="sla-chip deck-mono" :class="{ urgent: slaChip.urgent }">
        最紧待办 ⏱ {{ slaChip.text }}
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div
        v-for="(card, i) in statCards"
        :key="card.key"
        class="stat-card deck-rise"
        :class="[`deck-rise-${i + 1}`, { 'stat-alert': card.key === 'processing' && stats.pending > 0 }]"
        :style="{ '--accent': card.color }"
      >
        <div class="stat-card-glow"></div>
        <div class="stat-head">
          <span class="stat-label">{{ card.label }}</span>
          <span class="stat-en">{{ card.en }}</span>
        </div>
        <div class="stat-value deck-numeric">{{ animatedStats[card.key] ?? 0 }}</div>
        <div class="stat-foot">
          <span class="stat-bar"><span class="stat-bar-fill" :style="{ width: barWidth(card) + '%' }"></span></span>
          <span class="stat-note">{{ card.note }}</span>
        </div>
      </div>
    </div>

    <!-- 图表区 -->
    <div class="chart-row">
      <div class="deck-panel chart-panel deck-rise deck-rise-2">
        <div class="panel-head">
          <span class="deck-panel-title">近7天灾情趋势</span>
          <span class="panel-badge deck-mono">7D TREND</span>
        </div>
        <v-chart class="chart" :option="lineOption" autoresize style="height: 300px" />
      </div>
      <div class="deck-panel chart-panel deck-rise deck-rise-3">
        <div class="panel-head">
          <span class="deck-panel-title">灾情类型分布</span>
          <span class="panel-badge deck-mono">BY TYPE</span>
        </div>
        <v-chart class="chart" :option="pieOption" autoresize style="height: 300px" />
      </div>
    </div>

    <!-- 最新灾情 -->
    <div class="deck-panel table-panel deck-rise deck-rise-4">
      <div class="panel-head">
        <span class="deck-panel-title">最新灾情</span>
        <el-select v-model="typeFilter" clearable placeholder="全部类型" style="width: 160px">
          <el-option v-for="t in DISASTER_TYPES" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
      </div>
      <el-table :data="filteredDisasters" style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column prop="disaster_type" label="类型" width="120">
          <template #default="{ row }">{{ typeLabel(row.disaster_type) }}</template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="110">
          <template #default="{ row }">
            <span class="severity-chip" :style="{ color: SEVERITY_COLORS[row.severity], background: SEVERITY_COLORS[row.severity] + '1F' }">
              {{ SEVERITY_LABELS[row.severity] || row.severity }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_rescue_requested" label="救援请求" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_rescue_requested ? 'danger' : 'info'" size="small">{{ row.is_rescue_requested ? '需要' : '无需' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上报时间" width="170">
          <template #default="{ row }"><span class="deck-mono" style="font-size:12px">{{ formatTime(row.created_at) }}</span></template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { getDisasters, getDisasterStatistics } from '../api/disaster'
import { DISASTER_TYPES, DISASTER_STATUS, DISASTER_TYPE_MAP, SEVERITY_LABELS, SEVERITY_COLORS, SLA_WINDOWS_BY_SEVERITY } from '../utils/constants'

use([CanvasRenderer, LineChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const stats = reactive({ total: 0, processing: 0, resolved: 0, today: 0, rescue_requests: 0, pending: 0 })
const animatedStats = reactive({ total: 0, processing: 0, resolved: 0, today: 0, rescue_requests: 0 })
const latestDisasters = ref([])
const typeFilter = ref('')

// ---- 最紧待办 SLA 芯片：取待批准（confirmed）灾情的最小剩余时间 ----
const nowTick = ref(Date.now())
let slaTimer = null
const slaChip = computed(() => {
  const confirmed = latestDisasters.value.filter(d => d.status === 'confirmed' && d.created_at)
  if (!confirmed.length) return null
  let best = null
  for (const d of confirmed) {
    const window = SLA_WINDOWS_BY_SEVERITY[d.severity] || 3600
    const elapsed = (nowTick.value - new Date(d.created_at).getTime()) / 1000
    const remain = window - elapsed
    if (best === null || remain < best.remain) best = { remain, title: d.title }
  }
  const s = Math.max(0, Math.floor(best.remain))
  return {
    remain: best.remain,
    text: `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`,
    urgent: best.remain < (SLA_WINDOWS_BY_SEVERITY[5] || 1800) * 0.2,
    title: best.title,
  }
})

const statCards = [
  { key: 'total', label: '灾情总数', en: 'TOTAL', color: '#38E1FF', note: '累计上报' },
  { key: 'processing', label: '处理中', en: 'ACTIVE', color: '#FFB020', note: '正在响应' },
  { key: 'rescue_requests', label: '救援请求', en: 'SOS', color: '#FB4B6B', note: '等待救援' },
  { key: 'resolved', label: '已解决', en: 'RESOLVED', color: '#2DD4BF', note: '处置完成' },
  { key: 'today', label: '今日新增', en: 'TODAY', color: '#A78BFA', note: '24小时内' },
]

const barWidth = (card) => {
  if (!stats.total) return 0
  if (card.key === 'total') return 100
  return Math.min(100, Math.round((stats[card.key] / stats.total) * 100))
}

const aiInsight = computed(() => {
  if (stats.rescue_requests > 0) return `检测到 ${stats.rescue_requests} 起待救援请求，建议优先调配搜救力量`
  if (stats.processing > 0) return `${stats.processing} 起灾情处置中，资源调度链路运行正常`
  if (stats.total > 0) return '当前态势平稳，建议保持监测并预置应急资源'
  return 'AI引擎就绪，正在持续监测多源灾情数据流…'
})

const filteredDisasters = computed(() => {
  if (!typeFilter.value) return latestDisasters.value
  return latestDisasters.value.filter(d => d.disaster_type === typeFilter.value)
})

const darkTooltip = {
  backgroundColor: 'rgba(13, 22, 41, 0.94)',
  borderColor: 'rgba(56, 225, 255, 0.3)',
  textStyle: { color: '#E8F1FF', fontSize: 12 }
}

const lineOption = ref({
  tooltip: { trigger: 'axis', ...darkTooltip },
  xAxis: {
    type: 'category', data: [], boundaryGap: false,
    axisLine: { lineStyle: { color: 'rgba(120,190,255,0.15)' } },
    axisLabel: { color: '#5A6B8A', fontFamily: 'JetBrains Mono', fontSize: 10 }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(120,190,255,0.07)' } },
    axisLabel: { color: '#5A6B8A', fontFamily: 'JetBrains Mono', fontSize: 10 }
  },
  series: [{
    data: [], type: 'line', smooth: true, symbolSize: 6,
    lineStyle: { width: 2.5, color: '#38E1FF', shadowColor: 'rgba(56,225,255,0.5)', shadowBlur: 12 },
    itemStyle: { color: '#38E1FF', borderColor: '#06121F', borderWidth: 2 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(56,225,255,0.28)' },
          { offset: 1, color: 'rgba(56,225,255,0)' }
        ]
      }
    }
  }],
  grid: { left: 40, right: 20, top: 20, bottom: 30 }
})

const pieOption = ref({
  tooltip: { trigger: 'item', ...darkTooltip },
  legend: { bottom: 0, textStyle: { color: '#93A6C4', fontSize: 11 }, itemWidth: 10, itemHeight: 10 },
  color: ['#38E1FF', '#FFB020', '#FB4B6B', '#A78BFA', '#2DD4BF', '#7CB8FF'],
  series: [{
    type: 'pie', radius: ['46%', '72%'],
    itemStyle: { borderColor: '#0A1224', borderWidth: 3, borderRadius: 6 },
    label: { color: '#93A6C4', fontSize: 11 },
    emphasis: {
      itemStyle: { shadowBlur: 20, shadowColor: 'rgba(56,225,255,0.4)' },
      label: { color: '#E8F1FF', fontWeight: 600 }
    },
    data: []
  }]
})

const typeLabel = (v) => DISASTER_TYPE_MAP[v] || v
const statusLabel = (v) => DISASTER_STATUS.find(s => s.value === v)?.label || v
const statusType = (v) => DISASTER_STATUS.find(s => s.value === v)?.type || ''
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

function animateNumber(key, target) {
  const duration = 800
  const start = performance.now()
  const step = (now) => {
    const p = Math.min(1, (now - start) / duration)
    const eased = 1 - Math.pow(1 - p, 3)
    animatedStats[key] = Math.round(target * eased)
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

onMounted(async () => {
  slaTimer = setInterval(() => { nowTick.value = Date.now() }, 1000)
  try {
    const statsRes = await getDisasterStatistics()
    const d = statsRes.data
    stats.total = d.total_count ?? d.total ?? 0
    stats.processing = d.processing ?? d.by_status?.processing ?? d.by_status?.confirmed ?? 0
    stats.resolved = d.resolved ?? d.by_status?.resolved ?? 0
    stats.today = d.today_count ?? d.today ?? 0
    stats.rescue_requests = d.rescue_requests ?? d.rescue_request_count ?? 0
    stats.pending = d.by_status?.confirmed ?? 0

    Object.keys(stats).filter(k => k !== 'pending').forEach(k => animateNumber(k, stats[k]))

    if (d.recent_trend && d.recent_trend.length) {
      lineOption.value.xAxis.data = d.recent_trend.map(t => t.date || t.day)
      lineOption.value.series[0].data = d.recent_trend.map(t => t.count ?? t.value ?? 0)
    } else if (d.trend) {
      lineOption.value.xAxis.data = d.trend.dates || []
      lineOption.value.series[0].data = d.trend.counts || []
    } else {
      const days = []
      for (let i = 6; i >= 0; i--) {
        const t = new Date(Date.now() - i * 86400000)
        days.push(`${t.getMonth() + 1}/${t.getDate()}`)
      }
      lineOption.value.xAxis.data = days
      lineOption.value.series[0].data = days.map(() => 0)
    }

    const typeDist = d.by_type || d.type_distribution
    if (Array.isArray(typeDist)) {
      pieOption.value.series[0].data = typeDist.map((item) => ({
        name: typeLabel(item.type || item.name), value: item.count || item.value
      }))
    } else if (typeDist && typeof typeDist === 'object') {
      pieOption.value.series[0].data = Object.entries(typeDist).map(([type, count]) => ({
        name: typeLabel(type), value: count
      }))
    }
  } catch (e) { /* stats may not be available */ }

  try {
    const listRes = await getDisasters({ page: 1, page_size: 20 })
    latestDisasters.value = listRes.data.items || listRes.data || []
  } catch (e) { /* list may fail */ }
})

onBeforeUnmount(() => {
  if (slaTimer) clearInterval(slaTimer)
})
</script>

<style scoped>
.cmd-dashboard { position: relative; z-index: 1; }

/* ============ 顶部状态条 ============ */
.cmd-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.topline-title h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--deck-text);
}
.topline-sub {
  font-family: var(--deck-font-display);
  font-size: 11px;
  letter-spacing: 0.28em;
  color: var(--deck-text-3);
}

.ai-insight {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(167, 139, 250, 0.12), rgba(56, 225, 255, 0.06));
  border: 1px solid rgba(167, 139, 250, 0.28);
  box-shadow: 0 0 24px rgba(167, 139, 250, 0.12);
  max-width: 560px;
}
.insight-icon {
  width: 28px; height: 28px;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px;
  background: rgba(167, 139, 250, 0.16);
}
.insight-text { font-size: 13px; color: #C9BCF5; line-height: 1.4; }
.insight-tag {
  font-family: var(--deck-font-display);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: #0A0714;
  background: linear-gradient(135deg, #A78BFA, #38E1FF);
  border-radius: 5px;
  padding: 3px 7px;
  flex-shrink: 0;
}

/* ============ 最紧待办 SLA 芯片 ============ */
.sla-chip {
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  color: var(--deck-cyan);
  background: var(--deck-cyan-soft);
  border: 1px solid rgba(56, 225, 255, 0.3);
  white-space: nowrap;
}
.sla-chip.urgent {
  color: var(--deck-rose);
  background: rgba(251, 75, 107, 0.1);
  border-color: rgba(251, 75, 107, 0.4);
  animation: slaChipFlash 1s infinite;
}
@keyframes slaChipFlash { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* 处理中卡片有待批准任务时的脉冲提醒 */
.stat-card.stat-alert { animation: statAlertPulse 1.6s ease-in-out infinite; }
@keyframes statAlertPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 176, 32, 0.35); }
  50% { box-shadow: 0 0 0 6px rgba(255, 176, 32, 0); }
}

/* ============ 统计卡片 ============ */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  position: relative;
  padding: 18px 18px 16px;
  border-radius: 14px;
  background: var(--deck-panel);
  border: 1px solid var(--deck-border);
  backdrop-filter: blur(14px);
  overflow: hidden;
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.stat-card:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35), 0 0 22px color-mix(in srgb, var(--accent) 18%, transparent);
}
.stat-card-glow {
  position: absolute;
  top: -40px; right: -40px;
  width: 110px; height: 110px;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0.13;
  filter: blur(28px);
  pointer-events: none;
}
.stat-card::after {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--accent), transparent);
  opacity: 0.85;
}
.stat-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}
.stat-label { font-size: 13px; color: var(--deck-text-2); font-weight: 500; }
.stat-en {
  font-family: var(--deck-font-display);
  font-size: 10px;
  letter-spacing: 0.2em;
  color: var(--accent);
  opacity: 0.8;
}
.stat-value {
  font-size: 34px;
  font-weight: 700;
  line-height: 1;
  color: var(--deck-text);
  text-shadow: 0 0 24px color-mix(in srgb, var(--accent) 45%, transparent);
}
.stat-foot { margin-top: 14px; }
.stat-bar {
  display: block;
  height: 3px;
  border-radius: 2px;
  background: rgba(120, 190, 255, 0.08);
  overflow: hidden;
}
.stat-bar-fill {
  display: block;
  height: 100%;
  border-radius: 2px;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent);
  transition: width 1s cubic-bezier(0.22, 1, 0.36, 1);
}
.stat-note { font-size: 11px; color: var(--deck-text-3); display: block; margin-top: 7px; }

/* ============ 图表面板 ============ */
.chart-row {
  display: grid;
  grid-template-columns: 14fr 10fr;
  gap: 16px;
  margin-bottom: 20px;
}
.chart-panel, .table-panel { padding: 18px 20px; }
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.panel-badge {
  font-size: 10px;
  letter-spacing: 0.18em;
  color: var(--deck-text-3);
  border: 1px solid var(--deck-border);
  border-radius: 6px;
  padding: 3px 8px;
}

.severity-chip {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

@media (max-width: 1200px) {
  .stat-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-row { grid-template-columns: 1fr; }
}
</style>
