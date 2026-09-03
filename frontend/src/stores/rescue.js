import { defineStore } from 'pinia'
import { getSocialPosts } from '../api/social'
import { createDisaster, updateDisasterStatus } from '../api/disaster'
import { SLA_WINDOWS, SIGNAL_TYPE_LABELS } from '../utils/constants'

/**
 * rescue store —— CommandScreen 的单一事实源（替代原大屏的 window.tasks）。
 *
 * 任务状态机（UI 口径）：
 *   new → pending → dispatched → verify → closed
 *   （被拦截帖：intercepted，不进看板）
 * 与后端 Disaster.status 的对应：
 *   new=reported, pending=confirmed, dispatched, verify, closed=resolved
 */

// signal_type → Disaster.disaster_type 的近似映射
// （后端 DisasterType 无 casualty，伤亡归入建筑倒塌主因；注释说明这是归一化近似）
const SIGNAL_TO_DISASTER_TYPE = {
  casualty: 'building_collapse',
  building_collapse: 'building_collapse',
  road_blocked: 'road_damage',
  secondary_hazard: 'secondary_hazard',
  felt_report: 'earthquake',
  rescue_progress: 'earthquake',
  unknown: 'earthquake',
}

// P 级 → 后端 severity(1-5)
const PRIORITY_TO_SEVERITY = { P0: 5, P1: 4, P2: 3 }

/**
 * P 级映射（口径适配）：
 * SocialPost 未入库 severity_vote（仅派生 urgency_hint），
 * 因此用 signal_type + urgency_hint + sentiment 重写大屏 mapSeverity 规则：
 *   intercept: low 且 sentiment∈(neutral,null)
 *   P0: high 且 (casualty|building_collapse) 且 sentiment=urgent
 *   P1: high 其余
 *   P2: medium，或 low 但 sentiment=urgent
 */
function mapPriority(signalType, urgency, sentiment) {
  if (urgency === 'low' && (sentiment === 'neutral' || !sentiment)) return 'intercept'
  if (urgency === 'high') {
    if ((signalType === 'casualty' || signalType === 'building_collapse') && sentiment === 'urgent') return 'P0'
    return 'P1'
  }
  return 'P2'
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, Math.round(v)))
}

/** SocialPost(API 形态) → 大屏任务对象 */
function postToTask(post) {
  const signal = post.signal_type || 'unknown'
  const urgency = post.urgency_hint || 'medium'
  const priority = mapPriority(signal, urgency, post.sentiment)
  const intercepted = priority === 'intercept'
  const credibility = clamp((post.confidence ?? 0.5) * 100, 15, 95)
  const typeLabel = SIGNAL_TYPE_LABELS[signal] || '未知信号'

  return {
    eventId: post.post_id || `sp-${post.id}`,
    type: typeLabel,
    signalType: signal,
    location: post.geo_name || '未知区域',
    lat: post.latitude ?? 21.85,
    lng: post.longitude ?? 95.95,
    priority: intercepted ? 'P2' : priority,
    credibility,
    sla: intercepted ? 999 : (SLA_WINDOWS[priority] || 300),
    status: intercepted ? 'intercepted' : 'new',
    sourceText: post.text || '',
    extracted: intercepted ? null : {
      type: typeLabel,
      location: post.geo_name || '待确认',
      persons: urgency === 'high' ? '多人' : '-',
      severity: urgency === 'high' ? '严重' : urgency === 'medium' ? '中等' : '轻微',
    },
    interceptReason: intercepted
      ? (post.sentiment === 'neutral' || !post.sentiment ? '无灾情要素：信息性内容无需响应' : '低优先级：非紧急信息')
      : null,
    urgencyHint: urgency,
    sentiment: post.sentiment,
    confidence: post.confidence,
    _isRealData: true,
    _slaStart: 0, // 注入时由 addTask 设置为当前 clockSeconds
    disasterId: null, // 建档后回填
  }
}

export const useRescueStore = defineStore('rescue', {
  state: () => ({
    tasks: [],
    selectedTaskId: null,
    stats: { raw: 0, extracted: 0, intercepted: 0 },
    clockSeconds: 0,
    dataSource: 'detecting', // detecting|live|mock|offline
    dataSourceDetail: '',
    processedIds: new Set(),
    lastIngestAt: 0, // 供哨兵徽章闪烁
    advisoryCache: {}, // eventId -> advisory 结果
  }),

  getters: {
    tasksByStatus: (state) => (status) => state.tasks.filter(t => t.status === status),
    pendingCount: (state) => state.tasks.filter(t => t.status === 'pending').length,
    dispatchedCount: (state) => state.tasks.filter(t => t.status === 'dispatched').length,
    selectedTask: (state) => state.tasks.find(t => t.eventId === state.selectedTaskId) || null,
    kpis: (state) => {
      const closed = state.tasks.filter(t => t.status === 'closed')
      const avgMin = closed.length ? Math.round(closed.reduce((s, t) => s + t.sla, 0) / closed.length / 60) : 0
      const remainOk = (t) => Math.max(0, t.sla - (state.clockSeconds - t._slaStart))
      return {
        avgClosedMin: avgMin,
        slaRate: closed.length ? Math.round(closed.filter(remainOk).length / closed.length * 100) : 0,
        intercepted: state.stats.intercepted,
        pending: state.tasks.filter(t => t.status === 'pending').length,
      }
    },
  },

  actions: {
    /** 秒级心跳：由 CommandScreen 单一 setInterval 驱动 */
    tick() {
      this.clockSeconds++
    },

    _slaRemain(task) {
      if (task.status === 'closed' || task.status === 'intercepted') return 0
      return Math.max(0, task.sla - (this.clockSeconds - task._slaStart))
    },

    slaRemain(eventId) {
      const task = this.tasks.find(t => t.eventId === eventId)
      return task ? this._slaRemain(task) : 0
    },

    /** 添加任务（去重 + 统计 + 自动流转触发） */
    addTask(task) {
      if (this.processedIds.has(task.eventId)) return
      this.processedIds.add(task.eventId)
      task._slaStart = this.clockSeconds
      this.tasks.push(task)
      this.stats.raw++
      this.lastIngestAt = Date.now()
      if (task.status === 'intercepted') {
        this.stats.intercepted++
      } else {
        // 萃取完成计数在打字机动画结束时由组件回写；这里先自动流转
        setTimeout(() => this.transitionTask(task.eventId, 'pending'), 3000)
      }
    },

    /** 状态流转 + 后端同步 */
    async transitionTask(eventId, newStatus) {
      const task = this.tasks.find(t => t.eventId === eventId)
      if (!task || task.status === 'intercepted') return
      task.status = newStatus

      if (newStatus === 'pending') {
        // 建档（reported）→ 立即推进到 confirmed（待批准）
        this._createAndConfirm(task)
      } else if (newStatus === 'dispatched') {
        this._patchStatus(task, 'dispatched')
        setTimeout(() => this.transitionTask(eventId, 'verify'), 8000)
      } else if (newStatus === 'verify') {
        this._patchStatus(task, 'verify')
        setTimeout(() => this.transitionTask(eventId, 'closed'), 3000)
      } else if (newStatus === 'closed') {
        this._patchStatus(task, 'resolved')
      } else if (newStatus === 'new') {
        // 驳回：confirmed → reported
        this._patchStatus(task, 'reported')
      }
    },

    /** 批准派遣（人类拍板） */
    approveTask(eventId) {
      const task = this.tasks.find(t => t.eventId === eventId)
      if (!task || task.status !== 'pending') return
      this.transitionTask(eventId, 'dispatched')
    },

    /** 驳回（退回新情报） */
    rejectTask(eventId) {
      const task = this.tasks.find(t => t.eventId === eventId)
      if (!task || task.status !== 'pending') return
      this.transitionTask(eventId, 'new')
    },

    selectTask(eventId) {
      this.selectedTaskId = eventId
    },

    /** 建档 + 推进到待批准（后端失败仅降级，不阻塞演示） */
    async _createAndConfirm(task) {
      try {
        const payload = {
          title: `${task.type}·${task.location}`,
          disaster_type: SIGNAL_TO_DISASTER_TYPE[task.signalType] || 'earthquake',
          severity: PRIORITY_TO_SEVERITY[task.priority] || 3,
          description: task.sourceText,
          latitude: task.lat,
          longitude: task.lng,
          address: task.location,
          estimated_people_trapped: task.extracted?.persons === '多人' ? 5 : 0,
        }
        const res = await createDisaster(payload)
        task.disasterId = res.data.id
        await updateDisasterStatus(task.disasterId, 'confirmed')
      } catch (e) {
        console.warn('[rescue] 建档/确认失败（降级）:', e?.message)
        this.dataSourceDetail = '后端同步降级'
      }
    },

    /** 推进后端状态（失败降级） */
    async _patchStatus(task, status) {
      if (!task.disasterId) return
      try {
        await updateDisasterStatus(task.disasterId, status)
      } catch (e) {
        console.warn('[rescue] 状态同步失败（降级）:', e?.message)
      }
    },

    /** 从后端拉取社情并渐进注入 */
    async hydrateFromApi() {
      this.dataSource = 'detecting'
      try {
        const res = await getSocialPosts({ page_size: 100 })
        const items = (res.data.items || []).slice().reverse() // 按时间升序回放
        if (!items.length) {
          this.dataSource = 'offline'
          this.dataSourceDetail = '无社情数据'
          return
        }
        this.dataSource = 'live'
        this.dataSourceDetail = `真实数据 · ${items.length}条`
        // 渐进注入：每 3s 一条（复刻大屏节奏）
        items.forEach((post, i) => {
          setTimeout(() => {
            if (!this.processedIds.has(post.post_id)) {
              this.addTask(postToTask(post))
              this.dataSourceDetail = `真实数据 · ${Math.min(i + 1, items.length)}/${items.length}条`
            }
          }, i * 3000)
        })
      } catch (e) {
        console.warn('[rescue] hydrate 失败:', e?.message)
        this.dataSource = 'offline'
        this.dataSourceDetail = '接口不可达'
      }
    },

    /** 缓存参谋研判结果（避免重复烧 token） */
    setAdvisory(eventId, advisory) {
      this.advisoryCache[eventId] = advisory
    },
    getAdvisory(eventId) {
      return this.advisoryCache[eventId] || null
    },

    /** 重置（演示模式/切换场景） */
    reset() {
      this.tasks = []
      this.selectedTaskId = null
      this.stats = { raw: 0, extracted: 0, intercepted: 0 }
      this.processedIds = new Set()
      this.advisoryCache = {}
    },
  },
})
