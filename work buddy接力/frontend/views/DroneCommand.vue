<template>
  <div class="drone-command">
    <!-- 顶部：机队状态 -->
    <el-row :gutter="12" style="margin-bottom: 12px">
      <el-col :span="4" v-for="(card, i) in statusCards" :key="i">
        <div class="stat-card" :style="{ borderColor: card.color }">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" style="borderColor: #409eff">
          <div style="display:flex; align-items:center; gap:8px">
            <el-progress type="dashboard" :percentage="fleetStatus.avg_battery || 0" :width="56" :stroke-width="6" />
            <div>
              <div class="stat-value" style="color:#409eff; font-size:20px">{{ fleetStatus.avg_battery?.toFixed(0) || 0 }}%</div>
              <div class="stat-label">平均电量</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 左：巡逻画布 -->
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div style="display:flex; justify-content:space-between; align-items:center">
              <span><el-icon><Monitor /></el-icon> 无人机巡逻 — 数字孪生沙盘</span>
              <div>
                <el-button size="small" @click="initSim" :loading="initLoading">初始化机队</el-button>
                <el-button type="primary" size="small" @click="togglePatrol" :loading="patrolLoading">
                  {{ patrolActive ? '停止搜索' : '启动空中搜索' }}
                </el-button>
              </div>
            </div>
          </template>

          <!-- Canvas 巡逻动画（从演示版迁移） -->
          <div class="canvas-wrapper">
            <canvas ref="canvasRef" width="1000" height="660" />
            <div class="canvas-overlay" v-if="patrolActive">
              <el-tag type="success" effect="dark" size="small">
                <span class="blink-dot" /> 无人机-01 搜索中
              </el-tag>
            </div>
          </div>

          <!-- KPI 行 -->
          <el-row :gutter="8" style="margin-top: 12px">
            <el-col :span="6">
              <div class="kpi-box">
                <div class="kpi-value">{{ coverage.toFixed(0) }}%</div>
                <div class="kpi-label">搜索覆盖率</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="kpi-box">
                <div class="kpi-value">{{ discoveredCount }} / {{ survivors.length }}</div>
                <div class="kpi-label">发现生命迹象</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="kpi-box">
                <div class="kpi-value">{{ lidarCount.toLocaleString() }}</div>
                <div class="kpi-label">激光点云点数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="kpi-box">
                <div class="kpi-value">{{ temperature }}°C</div>
                <div class="kpi-label">热成像最高温</div>
              </div>
            </el-col>
          </el-row>

          <!-- 事件日志 -->
          <div class="event-log" v-if="events.length">
            <div v-for="(evt, i) in events.slice(-5)" :key="i" class="event-line">
              <el-icon v-if="evt.type === 'survivor_discovered'" color="#f56c6c"><Warning /></el-icon>
              <el-icon v-else color="#67c23a"><CircleCheck /></el-icon>
              {{ evt.message }}
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右：遥测 + 机队 -->
      <el-col :span="8">
        <!-- 无人机遥测面板 -->
        <el-card shadow="hover" style="margin-bottom: 12px">
          <template #header><span><el-icon><Odometer /></el-icon> 无人机遥测</span></template>
          <div class="telemetry-panel">
            <div class="tel-row">
              <span>电池电量</span>
              <span>{{ battery.toFixed(0) }}%</span>
            </div>
            <el-progress :percentage="battery" :stroke-width="8" :color="batteryColor" />
            <div class="tel-row">
              <span>飞行高度 / 速度</span>
              <span>80 m · 12 m/s</span>
            </div>
            <div class="tel-row">
              <span>激光点云累计点数</span>
              <span>{{ lidarCount.toLocaleString() }}</span>
            </div>
            <div class="tel-row">
              <span>热成像最高温度</span>
              <span>{{ temperature }}°C</span>
            </div>
            <div class="tel-row">
              <span>飞行模式</span>
              <el-tag size="small" :type="patrolActive ? 'success' : 'info'">
                {{ patrolActive ? '搜索中' : '待命' }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <!-- 机队列表 -->
        <el-card shadow="hover">
          <template #header><span><el-icon><Operation /></el-icon> 机队列表</span></template>
          <div v-for="drone in fleet" :key="drone.drone_id_str" class="drone-item">
            <div class="drone-header">
              <span class="drone-id">{{ drone.drone_id_str }}</span>
              <el-tag size="small" :type="statusType(drone.status)">{{ statusLabel(drone.status) }}</el-tag>
            </div>
            <div class="drone-info">
              <span>{{ drone.call_sign }} · {{ drone.model }}</span>
            </div>
            <div class="drone-cap">
              <el-tag v-for="cap in drone.capabilities" :key="cap" size="small" type="info" effect="plain" style="margin-right:4px">
                {{ capLabel(cap) }}
              </el-tag>
            </div>
            <el-progress :percentage="drone.battery" :stroke-width="4" :color="drone.battery > 30 ? '#67c23a' : '#f56c6c'" />
          </div>
          <el-empty v-if="!fleet.length" description="点击初始化机队" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { droneApi } from '../api/drone'

const canvasRef = ref(null)
const fleet = ref([])
const fleetStatus = ref({})
const initLoading = ref(false)
const patrolLoading = ref(false)
const patrolActive = ref(false)

// 巡逻仿真状态
const sim = ref(null)
const survivors = ref([])
const events = ref([])

// KPI
const coverage = ref(0)
const battery = ref(100)
const lidarCount = ref(0)
const temperature = ref(22.4)
const discoveredCount = computed(() => survivors.value.filter(s => s.discovered).length)

// 动画
let rafId = null
let ctx = null
let lastTs = 0

// ---- 演示版被困人员（仿真） ----
const SIM_SURVIVORS = [
  { id: 'SV-01', x: 180, y: 130, discovered: false },
  { id: 'SV-02', x: 420, y: 196, discovered: false },
  { id: 'SV-03', x: 680, y: 328, discovered: false },
  { id: 'SV-04', x: 320, y: 460, discovered: false },
  { id: 'SV-05', x: 750, y: 526, discovered: false },
]

// 扫描行
const ROWS = [64, 130, 196, 262, 328, 394, 460, 526, 592]

const statusCards = computed(() => [
  { label: '总数', value: fleetStatus.value.total || 0, color: '#409eff' },
  { label: '待命', value: fleetStatus.value.standby || 0, color: '#909399' },
  { label: '搜索中', value: fleetStatus.value.searching || 0, color: '#67c23a' },
  { label: '物资运输', value: fleetStatus.value.supplying || 0, color: '#e6a23c' },
  { label: '侦察', value: fleetStatus.value.recon || 0, color: '#f56c6c' },
])

const batteryColor = computed(() => {
  if (battery.value > 50) return '#67c23a'
  if (battery.value > 20) return '#e6a23c'
  return '#f56c6c'
})

function statusType(s) {
  return { standby: 'info', searching: 'success', supplying: 'warning', recon: 'danger', returning: '', charging: 'info', offline: 'info' }[s] || 'info'
}
function statusLabel(s) {
  return { standby: '待命', searching: '搜索中', supplying: '物资运输', recon: '侦察中', returning: '返航', charging: '充电中', offline: '离线' }[s] || s
}
function capLabel(c) {
  return { search: '搜索', supply: '运输', recon: '侦察', comm_relay: '通信中继' }[c] || c
}

// ---- 初始化机队 ----
async function initSim() {
  initLoading.value = true
  try {
    await droneApi.initSimFleet()
    await loadFleet()
  } finally {
    initLoading.value = false
  }
}

async function loadFleet() {
  try {
    const [f, s] = await Promise.all([droneApi.getFleet(), droneApi.getFleetStatus()])
    fleet.value = f
    fleetStatus.value = s
  } catch (e) {
    // 降级：本地模拟
  }
}

// ---- 巡逻动画（从演示版迁移） ----
async function togglePatrol() {
  if (patrolActive.value) {
    // 停止
    patrolActive.value = false
    if (sim.value) sim.value.active = false
    if (rafId) cancelAnimationFrame(rafId)
    return
  }

  patrolLoading.value = true
  try {
    // 创建仿真会话
    if (!sim.value) {
      sim.value = await droneApi.createPatrol({
        drone_id_str: '无人机-01',
        canvas_width: 1000,
        canvas_height: 660,
        row_count: 9,
      })
    }

    // 重置被困人员
    survivors.value = SIM_SURVIVORS.map(s => ({ ...s, discovered: false }))
    events.value = []

    // 启动
    sim.value = await droneApi.startPatrol(sim.value)
    patrolActive.value = true

    // 初始化画布
    ctx = canvasRef.value.getContext('2d')
    lastTs = 0

    // 启动动画循环
    rafId = requestAnimationFrame(animateLoop)
  } finally {
    patrolLoading.value = false
  }
}

function animateLoop(ts) {
  const dt = Math.min(3, ((ts - lastTs) / 16.67) || 1)
  lastTs = ts

  // 本地推进仿真（减少 API 调用）
  stepSimLocally(dt)

  // 绘制
  draw(ts)

  // 更新 KPI
  coverage.value = sim.value.coverage
  battery.value = sim.value.battery
  lidarCount.value = sim.value.lidar_points.length * 37
  temperature.value = sim.value.temperature

  if (sim.value.active) {
    rafId = requestAnimationFrame(animateLoop)
  } else {
    patrolActive.value = false
  }
}

function stepSimLocally(dt) {
  if (!sim.value || !sim.value.active) return

  const s = sim.value
  s.x += 3.1 * s.dir * dt
  s.battery = Math.max(5, s.battery - 0.006 * dt)

  // 激光点云
  for (let k = 0; k < 3; k++) {
    const a = Math.random() * Math.PI * 2
    const r = Math.sqrt(Math.random()) * 70
    s.lidar_points.push({ x: s.x + Math.cos(a) * r, y: ROWS[s.row_idx] + Math.sin(a) * r })
  }
  if (s.lidar_points.length > 6000) s.lidar_points.splice(0, s.lidar_points.length - 6000)

  // 温度波动
  s.temperature = +(34 + Math.sin(ts / 1500) * 1.6 + Math.random()).toFixed(1)

  // 生命探测
  const currentY = ROWS[s.row_idx]
  survivors.value.forEach(sv => {
    if (!sv.discovered && Math.hypot(sv.x - s.x, sv.y - currentY) < 75) {
      sv.discovered = true
      events.value.push({ type: 'survivor_discovered', message: `热成像发现疑似生命迹象 ${sv.id}` })
    }
  })

  // 边界 → 换行
  const MW = 1000
  if ((s.dir === 1 && s.x > MW + 30) || (s.dir === -1 && s.x < -30)) {
    s.row_idx++
    if (s.row_idx >= ROWS.length) {
      s.active = false
      s.coverage = 100
      events.value.push({ type: 'scan_complete', message: '全域搜索完成 · 覆盖率 100%' })
    } else {
      s.dir *= -1
      s.x = s.dir === 1 ? -30 : MW + 30
    }
  }

  // 覆盖率
  const prog = s.dir === 1 ? Math.min(1, s.x / MW) : Math.min(1, (MW - s.x) / MW)
  s.coverage = Math.min(100, ((s.row_idx + prog) / ROWS.length) * 100)
}

let ts = 0

function draw(now) {
  ts = now
  if (!ctx || !sim.value) return

  const s = sim.value
  const MW = 1000, MH = 660

  // 背景
  ctx.fillStyle = '#0a0e1a'
  ctx.fillRect(0, 0, MW, MH)

  // 网格
  ctx.strokeStyle = 'rgba(30,40,60,.4)'
  ctx.lineWidth = 0.5
  for (let x = 0; x <= MW; x += 50) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, MH); ctx.stroke()
  }
  for (let y = 0; y <= MH; y += 50) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(MW, y); ctx.stroke()
  }

  // 激光点云
  ctx.fillStyle = 'rgba(34,211,238,.3)'
  s.lidar_points.forEach(p => {
    ctx.fillRect(p.x, p.y, 1, 1)
  })

  // 被困人员
  survivors.value.forEach(sv => {
    if (sv.discovered) {
      ctx.fillStyle = 'rgba(239,68,68,.8)'
      ctx.beginPath()
      ctx.arc(sv.x, sv.y, 6, 0, 7)
      ctx.fill()
      ctx.strokeStyle = 'rgba(239,68,68,.4)'
      ctx.beginPath()
      ctx.arc(sv.x, sv.y, 12 + Math.sin(now / 200) * 3, 0, 7)
      ctx.stroke()
    } else {
      ctx.fillStyle = 'rgba(100,116,139,.3)'
      ctx.fillRect(sv.x - 2, sv.y - 2, 4, 4)
    }
  })

  // 无人机
  if (s.active) {
    const dy = ROWS[s.row_idx]

    // 扫描圈
    ctx.fillStyle = 'rgba(34,211,238,.06)'
    ctx.beginPath()
    ctx.arc(s.x, dy, 70, 0, 7)
    ctx.fill()

    ctx.strokeStyle = 'rgba(34,211,238,.25)'
    ctx.beginPath()
    ctx.arc(s.x, dy, 70, 0, 7)
    ctx.stroke()

    // 雷达扫描线
    const ang = now / 160
    ctx.strokeStyle = 'rgba(34,211,238,.5)'
    ctx.beginPath()
    ctx.moveTo(s.x, dy)
    ctx.lineTo(s.x + Math.cos(ang) * 70, dy + Math.sin(ang) * 70)
    ctx.stroke()

    // 扫描轨迹
    ctx.strokeStyle = 'rgba(251,191,36,.3)'
    ctx.lineWidth = 2
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(s.dir === 1 ? -30 : MW + 30, dy)
    ctx.lineTo(s.x, dy)
    ctx.stroke()
    ctx.setLineDash([])
    ctx.lineWidth = 1

    // 无人机图标
    drawDrone(s.x, dy, now)
  }
}

function drawDrone(x, y, now) {
  ctx.save()
  ctx.translate(x, y)

  // X 形机身
  ctx.strokeStyle = '#22d3ee'
  ctx.fillStyle = '#22d3ee'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.moveTo(-7, -7); ctx.lineTo(7, 7)
  ctx.moveTo(7, -7); ctx.lineTo(-7, 7)
  ctx.stroke()

  // 四个旋翼
  const rr = 4 + Math.sin(now / 60) * 0.6
  for (const [px, py] of [[-7,-7], [7,-7], [-7,7], [7,7]]) {
    ctx.globalAlpha = 0.5
    ctx.beginPath()
    ctx.arc(px, py, rr, 0, 7)
    ctx.stroke()
    ctx.globalAlpha = 1
  }

  // 中心
  ctx.beginPath()
  ctx.arc(0, 0, 2.5, 0, 7)
  ctx.fill()
  ctx.restore()
}

onMounted(() => {
  loadFleet()
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
.drone-command { padding: 4px; }
.stat-card {
  background: #fff; border: 1px solid #e4e7ed; border-radius: 8px;
  padding: 12px; text-align: center; border-left-width: 3px;
}
.stat-value { font-size: 24px; font-weight: 700; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.canvas-wrapper { position: relative; }
.canvas-wrapper canvas {
  width: 100%; border-radius: 8px; background: #0a0e1a; display: block;
}
.canvas-overlay {
  position: absolute; top: 12px; left: 12px;
}
.blink-dot {
  display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: #67c23a; animation: blink 1.2s infinite; margin-right: 4px;
}
@keyframes blink { 50% { opacity: 0.25; } }
.kpi-box {
  background: #f5f7fa; border-radius: 6px; padding: 10px; text-align: center;
}
.kpi-value { font-size: 20px; font-weight: 700; color: #303133; }
.kpi-label { font-size: 11px; color: #909399; margin-top: 2px; }
.event-log {
  margin-top: 10px; max-height: 80px; overflow-y: auto;
  background: #f5f7fa; border-radius: 6px; padding: 8px;
}
.event-line {
  font-size: 12px; color: #606266; padding: 2px 0;
  display: flex; align-items: center; gap: 4px;
}
.telemetry-panel { font-size: 13px; }
.tel-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 0; color: #606266;
}
.drone-item {
  padding: 8px 0; border-bottom: 1px solid #f0f0f0;
}
.drone-item:last-child { border-bottom: none; }
.drone-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 4px;
}
.drone-id { font-weight: 600; font-size: 14px; }
.drone-info { font-size: 12px; color: #909399; margin-bottom: 4px; }
.drone-cap { margin-bottom: 6px; }
</style>
