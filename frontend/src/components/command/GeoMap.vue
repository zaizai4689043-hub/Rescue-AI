<script setup>
/**
 * 中栏：模拟地图（SVG，不用真实地图SDK）。
 * 移植大屏 geoToSvg 投影（缅滇区域），震中+等震线，队伍/安置点，灾情点涟漪与状态色。
 */
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRescueStore } from '../../stores/rescue'

const store = useRescueStore()
const { tasks, selectedTaskId } = storeToRefs(store)

// 经纬度边界（缅滇区域）→ SVG 0-1000 x 0-700
const MAP_BOUNDS = { minLng: 94.5, maxLng: 105.5, minLat: 15.5, maxLat: 31.5 }
function geoToSvg(lng, lat) {
  const x = ((lng - MAP_BOUNDS.minLng) / (MAP_BOUNDS.maxLng - MAP_BOUNDS.minLng)) * 1000
  const y = ((MAP_BOUNDS.maxLat - lat) / (MAP_BOUNDS.maxLat - MAP_BOUNDS.minLat)) * 700
  return { x: Math.max(20, Math.min(980, x)), y: Math.max(20, Math.min(680, y)) }
}

const layers = ref({ points: true, wind: true, teams: true })

// 底图网格
const gridV = computed(() => Array.from({ length: 11 }, (_, i) => i * 100))
const gridH = computed(() => Array.from({ length: 8 }, (_, i) => i * 100))

// 地形色块 + 道路
const terrains = [
  'M80,250 Q200,180 350,260 T550,230 L520,380 Q320,400 100,340Z',
  'M550,120 Q680,90 800,150 T920,220 L880,320 Q720,300 570,270Z',
  'M150,480 Q350,420 520,490 T720,520 L680,620 Q420,640 170,580Z',
]
const roads = [
  'M0,370 Q250,320 500,370 T1000,340',
  'M480,0 Q460,220 500,420 T480,700',
  'M80,620 Q300,520 600,570 T960,520',
]

// 震中（缅甸 7.9 级）与等震线
const epicenter = geoToSvg(95.95, 21.85)
const isoRings = [180, 120, 70]

// 队伍与安置点（真实地理坐标）
const teams = [
  { name: '瑞丽救援队', ...geoToSvg(97.85, 24.01) },
  { name: '保山医疗队', ...geoToSvg(99.16, 25.12) },
  { name: '昆明支援队', ...geoToSvg(102.73, 25.04) },
]
const shelters = [
  { name: '瑞丽安置点', ...geoToSvg(97.9, 24.05) },
  { name: '芒市避难所', ...geoToSvg(98.58, 24.43) },
]

// 灾情点（非拦截任务）
const points = computed(() =>
  tasks.value
    .filter(t => t.status !== 'intercepted')
    .map(t => ({ task: t, pos: geoToSvg(t.lng, t.lat) }))
)

const STATUS_COLOR = {
  new: '#FB4B6B',
  pending: '#FFB020',
  dispatched: '#38E1FF',
  verify: '#38E1FF',
  closed: '#2DD4BF',
}
function pointColor(t) { return STATUS_COLOR[t.status] || '#2DD4BF' }
function starPoints(cx, cy, outerR, innerR) {
  const pts = []
  for (let i = 0; i < 10; i++) {
    const angle = (Math.PI / 5) * i - Math.PI / 2
    const r = i % 2 === 0 ? outerR : innerR
    pts.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`)
  }
  return pts.join(' ')
}
function select(id) { store.selectTask(id) }
const cornerTL = `N${MAP_BOUNDS.maxLat}° E${MAP_BOUNDS.minLng}°`
const cornerBR = `N${MAP_BOUNDS.minLat}° E${MAP_BOUNDS.maxLng}°`
</script>

<template>
  <div class="cs-panel cs-map deck-rise deck-rise-2">
    <svg class="cs-map-svg" viewBox="0 0 1000 700" preserveAspectRatio="xMidYMid slice">
      <rect x="0" y="0" width="1000" height="700" fill="var(--deck-bg)" />
      <!-- 经纬网格 -->
      <line v-for="x in gridV" :key="'v'+x" :x1="x" y1="0" :x2="x" y2="700" stroke="#131a24" stroke-width="0.5" />
      <line v-for="y in gridH" :key="'h'+y" x1="0" :y1="y" x2="1000" :y2="y" stroke="#131a24" stroke-width="0.5" />
      <!-- 地形与道路 -->
      <path v-for="(d, i) in terrains" :key="'t'+i" :d="d" fill="#0f1520" stroke="#1a2535" stroke-width="1" />
      <path v-for="(d, i) in roads" :key="'r'+i" :d="d" fill="none" stroke="#1a2535" stroke-width="2" stroke-dasharray="6 4" />

      <!-- 等震线 + 震中 -->
      <g v-if="layers.wind">
        <circle v-for="r in isoRings" :key="'iso'+r" :cx="epicenter.x" :cy="epicenter.y" :r="r" class="cs-iso-seismic" />
        <polygon :points="starPoints(epicenter.x, epicenter.y, 14, 7)" class="cs-quake-center" />
        <text :x="epicenter.x + 20" :y="epicenter.y - 10" font-size="11" fill="#FB4B6B" font-weight="bold">M7.9 震中</text>
      </g>

      <!-- 队伍与安置点 -->
      <g v-if="layers.teams">
        <template v-for="t in teams" :key="'tm'+t.name">
          <text :x="t.x" :y="t.y + 5" text-anchor="middle" font-size="16" fill="#38E1FF">🚒</text>
          <text :x="t.x" :y="t.y + 20" text-anchor="middle" font-size="9" fill="#38E1FF" opacity="0.7">{{ t.name }}</text>
        </template>
        <template v-for="s in shelters" :key="'sh'+s.name">
          <text :x="s.x" :y="s.y + 5" text-anchor="middle" font-size="14" fill="#2DD4BF">🏕</text>
          <text :x="s.x" :y="s.y + 18" text-anchor="middle" font-size="8" fill="#2DD4BF" opacity="0.6">{{ s.name }}</text>
        </template>
      </g>

      <!-- 灾情点 -->
      <g v-if="layers.points">
        <g
          v-for="p in points"
          :key="'pt'+p.task.eventId"
          class="cs-disaster-point"
          :class="{ selected: selectedTaskId === p.task.eventId }"
          @click="select(p.task.eventId)"
        >
          <!-- new 状态脉冲光圈 -->
          <circle v-if="p.task.status === 'new'" :cx="p.pos.x" :cy="p.pos.y" r="6" fill="none"
                  :stroke="pointColor(p.task)" stroke-width="2" class="cs-pulse-circle" />
          <!-- 入场涟漪 -->
          <circle :cx="p.pos.x" :cy="p.pos.y" r="5" fill="none" :stroke="pointColor(p.task)" stroke-width="2">
            <animate attributeName="r" from="5" to="22" dur="1s" begin="0s" fill="freeze" />
            <animate attributeName="opacity" from="0.9" to="0" dur="1s" begin="0s" fill="freeze" />
          </circle>
          <circle class="cs-core" :cx="p.pos.x" :cy="p.pos.y" r="5" :fill="pointColor(p.task)" />
          <text :x="p.pos.x + 10" :y="p.pos.y + 4" font-size="10" :fill="pointColor(p.task)" font-weight="bold">{{ p.task.priority }}</text>
          <text v-if="p.task.location && p.task.location !== '未知区域'" :x="p.pos.x + 10" :y="p.pos.y + 16" font-size="8" fill="#5A6B8A">
            {{ p.task.location.slice(0, 8) }}
          </text>
        </g>
      </g>
    </svg>

    <div class="cs-map-coord tl">{{ cornerTL }}</div>
    <div class="cs-map-coord br">{{ cornerBR }}</div>
    <div class="cs-map-layers">
      <label><input type="checkbox" v-model="layers.points" />灾情点</label>
      <label><input type="checkbox" v-model="layers.wind" />等震线</label>
      <label><input type="checkbox" v-model="layers.teams" />队伍</label>
    </div>
  </div>
</template>
