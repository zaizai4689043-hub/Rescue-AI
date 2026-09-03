<template>
  <div class="map-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <h2 class="page-title">灾情地图</h2>
      <div class="filters">
        <el-select v-model="filterType" clearable placeholder="灾情类型" style="width: 140px" @change="refreshMap">
          <el-option v-for="t in DISASTER_TYPES" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
        <el-select v-model="filterSeverity" clearable placeholder="严重程度" style="width: 140px" @change="refreshMap">
          <el-option v-for="i in 5" :key="i" :label="SEVERITY_LABELS[i]" :value="i" />
        </el-select>
        <el-button type="primary" :icon="RefreshIcon" @click="resetView">重置视图</el-button>
      </div>
    </div>

    <div class="map-body">
      <!-- 地图容器 -->
      <div class="map-container" ref="mapRef"></div>

      <!-- 右侧统计面板 -->
      <el-aside class="stats-panel" width="300px">
        <h3 class="panel-title">灾情统计</h3>
        <div class="stat-item">
          <span class="stat-label">灾情总数</span>
          <span class="stat-value">{{ allData.length }}</span>
        </div>
        <el-divider />
        <div class="stat-section">
          <h4>按类型</h4>
          <div v-for="t in DISASTER_TYPES" :key="t.value" class="stat-row">
            <span>{{ t.label }}</span>
            <el-tag size="small">{{ countByType(t.value) }}</el-tag>
          </div>
        </div>
        <el-divider />
        <div class="stat-section">
          <h4>按严重程度</h4>
          <div v-for="i in 5" :key="i" class="stat-row">
            <span :style="{ color: SEVERITY_COLORS[i] }">{{ SEVERITY_LABELS[i] }}</span>
            <el-tag size="small">{{ countBySeverity(i) }}</el-tag>
          </div>
        </div>
        <el-divider />
        <div class="pie-container" ref="pieRef"></div>
      </el-aside>
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="灾情详情" size="420px" direction="rtl">
      <el-descriptions :column="1" border v-if="selectedDisaster">
        <el-descriptions-item label="标题">{{ selectedDisaster.title }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ DISASTER_TYPE_MAP[selectedDisaster.disaster_type] || selectedDisaster.disaster_type }}</el-descriptions-item>
        <el-descriptions-item label="严重程度">
          <span :style="{ color: SEVERITY_COLORS[selectedDisaster.severity], fontWeight: 700 }">
            {{ SEVERITY_LABELS[selectedDisaster.severity] }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(selectedDisaster.status)" size="small">{{ statusLabel(selectedDisaster.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="坐标">{{ selectedDisaster.latitude }}, {{ selectedDisaster.longitude }}</el-descriptions-item>
        <el-descriptions-item label="地址">{{ selectedDisaster.address || '-' }}</el-descriptions-item>
      </el-descriptions>
      <el-button type="primary" style="margin-top: 20px" @click="$router.push('/disaster-list')">查看完整列表</el-button>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getMapData } from '../api/ai'
import { DISASTER_TYPES, DISASTER_TYPE_MAP, SEVERITY_LABELS, SEVERITY_COLORS, DISASTER_STATUS } from '../utils/constants'

const RefreshIcon = { render: () => null }

const mapRef = ref(null)
const pieRef = ref(null)
let mapChart = null
let pieChart = null

const allData = ref([])
const filterType = ref('')
const filterSeverity = ref(null)
const drawerVisible = ref(false)
const selectedDisaster = ref(null)

const TYPE_COLORS = {
  earthquake: '#FB4B6B',
  aftershock: '#FFB020',
  building_collapse: '#FF6B8A',
  road_damage: '#7CB8FF',
  landslide: '#D9A05B',
  secondary_hazard: '#A78BFA',
}

function countByType(type) {
  return allData.value.filter(d => d.disaster_type === type).length
}
function countBySeverity(s) {
  return allData.value.filter(d => d.severity === s).length
}
function statusLabel(v) {
  return DISASTER_STATUS.find(s => s.value === v)?.label || v
}
function statusType(v) {
  return DISASTER_STATUS.find(s => s.value === v)?.type || ''
}

function getFilteredData() {
  let data = allData.value
  if (filterType.value) data = data.filter(d => d.disaster_type === filterType.value)
  if (filterSeverity.value) data = data.filter(d => d.severity === filterSeverity.value)
  return data
}

async function loadData() {
  try {
    const res = await getMapData()
    allData.value = res.data || []
  } catch {
    allData.value = []
  }
}

function buildMapOption() {
  const data = getFilteredData()
  const scatterData = data.map(d => ({
    name: d.title,
    value: [d.longitude, d.latitude, d.severity],
    itemStyle: { color: TYPE_COLORS[d.disaster_type] || '#F56C6C' },
    _raw: d,
  }))

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(13, 22, 41, 0.94)',
      borderColor: 'rgba(56, 225, 255, 0.3)',
      textStyle: { color: '#E8F1FF', fontSize: 12 },
      formatter(params) {
        if (params.seriesType === 'scatter') {
          const d = params.data._raw || {}
          return `<b>${d.title || ''}</b><br/>类型: ${DISASTER_TYPE_MAP[d.disaster_type] || d.disaster_type}<br/>严重程度: ${SEVERITY_LABELS[d.severity] || d.severity}<br/>状态: ${statusLabel(d.status)}`
        }
        return params.name
      },
    },
    geo: {
      map: 'china',
      roam: true,
      zoom: 1.2,
      center: [105, 35],
      itemStyle: {
        areaColor: '#0C1730',
        borderColor: 'rgba(56, 225, 255, 0.35)',
        borderWidth: 1,
        shadowColor: 'rgba(56, 225, 255, 0.15)',
        shadowBlur: 14,
      },
      emphasis: {
        itemStyle: { areaColor: '#12234A' },
        label: { color: '#38E1FF' },
      },
      label: { show: false },
    },
    visualMap: {
      show: true,
      min: 1,
      max: 5,
      text: ['严重', '轻微'],
      textStyle: { color: '#93A6C4' },
      realtime: false,
      calculable: true,
      inRange: { color: ['#2DD4BF', '#FFB020', '#FB4B6B', '#DC143C'] },
      dimension: 2,
      seriesIndex: 0,
    },
    series: [
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        data: scatterData,
        symbolSize(val) {
          return Math.max(val[2] * 5, 10)
        },
        rippleEffect: { brushType: 'stroke', scale: 3 },
        encode: { value: 2 },
      },
    ],
  }
}

function initMap() {
  if (!mapRef.value) return
  mapChart = echarts.init(mapRef.value)
  mapChart.setOption(buildMapOption())
  mapChart.on('click', 'series.effectScatter', (params) => {
    selectedDisaster.value = params.data._raw
    drawerVisible.value = true
  })
}

function initPie() {
  if (!pieRef.value) return
  pieChart = echarts.init(pieRef.value)
  updatePie()
}

function updatePie() {
  if (!pieChart) return
  const pieData = DISASTER_TYPES.map(t => ({
    name: t.label,
    value: countByType(t.value),
  })).filter(d => d.value > 0)
  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(13, 22, 41, 0.94)',
      borderColor: 'rgba(56, 225, 255, 0.3)',
      textStyle: { color: '#E8F1FF', fontSize: 12 },
    },
    color: ['#38E1FF', '#FFB020', '#FB4B6B', '#A78BFA', '#2DD4BF', '#7CB8FF'],
    series: [
      {
        type: 'pie',
        radius: ['30%', '70%'],
        data: pieData,
        label: { fontSize: 10, color: '#93A6C4' },
        itemStyle: { borderColor: '#0A1224', borderWidth: 2, borderRadius: 4 },
        emphasis: { itemStyle: { shadowBlur: 16, shadowOffsetX: 0, shadowColor: 'rgba(56,225,255,0.4)' } },
      },
    ],
  })
}

async function refreshMap() {
  await loadData()
  if (mapChart) mapChart.setOption(buildMapOption(), true)
  updatePie()
}

function resetView() {
  filterType.value = ''
  filterSeverity.value = null
  refreshMap()
}

function handleResize() {
  mapChart?.resize()
  pieChart?.resize()
}

onMounted(async () => {
  // 注册地图
  try {
    const resp = await fetch('/china.json')
    const geoJson = await resp.json()
    echarts.registerMap('china', geoJson)
  } catch (e) {
    console.warn('中国地图GeoJSON加载失败', e)
  }
  await loadData()
  await nextTick()
  initMap()
  initPie()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  mapChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.map-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 110px);
  position: relative;
  z-index: 1;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--deck-text);
  margin: 0;
  letter-spacing: 0.04em;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--deck-panel);
  border: 1px solid var(--deck-border);
  backdrop-filter: blur(14px);
  margin-bottom: 14px;
}
.filters { display: flex; gap: 12px; align-items: center; }
.map-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 14px;
}
.map-container {
  flex: 1;
  min-height: 300px;
  border-radius: 14px;
  background: var(--deck-panel);
  border: 1px solid var(--deck-border);
  backdrop-filter: blur(14px);
  overflow: hidden;
}
.stats-panel {
  background: var(--deck-panel);
  border: 1px solid var(--deck-border);
  border-radius: 14px;
  backdrop-filter: blur(14px);
  padding: 18px;
  overflow-y: auto;
}
.panel-title {
  font-family: var(--deck-font-display);
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--deck-text);
  margin: 0 0 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.panel-title::before {
  content: '';
  width: 3px; height: 14px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--deck-cyan), transparent);
  box-shadow: 0 0 8px rgba(56, 225, 255, 0.6);
}
.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
  color: var(--deck-text-2);
}
.stat-value {
  font-family: var(--deck-font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--deck-cyan);
  text-shadow: 0 0 16px rgba(56, 225, 255, 0.5);
}
.stat-section h4 {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.12em;
  color: var(--deck-text-3);
  text-transform: uppercase;
}
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--deck-text-2);
}
.pie-container { width: 100%; height: 200px; }
.stats-panel :deep(.el-divider) {
  border-color: var(--deck-border);
  margin: 14px 0;
}
</style>
