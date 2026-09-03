<template>
  <div class="disaster-heatmap">
    <el-row :gutter="16">
      <!-- 地图 -->
      <el-col :span="18">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>灾情热力图 — NER 地名聚合</span>
              <div>
                <el-button type="primary" size="small" @click="rebuild" :loading="loading">重建热点</el-button>
                <el-button type="success" size="small" @click="refreshPriority" :loading="loading">刷新优先级</el-button>
              </div>
            </div>
          </template>
          <div ref="mapRef" class="map-container"></div>
        </el-card>
      </el-col>

      <!-- 优先级队列 -->
      <el-col :span="6">
        <el-card shadow="hover" class="priority-card">
          <template #header>
            <span><el-icon><List /></el-icon> 动态优先级排序</span>
          </template>
          <div class="priority-list">
            <div
              v-for="item in ranking"
              :key="item.hotspot_id"
              class="priority-item"
              :class="'priority-' + (item.priority_level || 'P3').toLowerCase()"
            >
              <div class="priority-header">
                <el-tag :type="priorityTagType(item.priority_level)" size="small" effect="dark">
                  {{ item.priority_level || 'P3' }}
                </el-tag>
                <span class="location-name">{{ item.location_name }}</span>
              </div>
              <div class="priority-meta">
                <span>帖文 {{ item.post_count }}</span>
                <span>呼救 {{ item.distress_count }}</span>
                <span>预估被困 {{ item.estimated_trapped }}</span>
              </div>
              <div class="priority-score">
                <el-progress
                  :percentage="Math.round(item.priority_score * 100)"
                  :color="priorityColor(item.priority_level)"
                  :show-text="false"
                  :stroke-width="6"
                />
              </div>
              <div v-if="item.priority_reason" class="priority-reason">{{ item.priority_reason }}</div>
              <div class="priority-badges">
                <el-tag v-if="item.has_rescue_team" type="success" size="small">已有救援队</el-tag>
                <el-tag v-if="!item.road_accessible" type="danger" size="small">道路中断</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { List } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { rebuildHotspots, refreshPriority } from '../api/weibo'

const mapRef = ref(null)
const ranking = ref([])
const loading = ref(false)
let chart = null

async function loadMapData() {
  try {
    // 获取热力图数据
    const res = await fetch('/api/v1/weibo/posts?page=1&page_size=1')
    // 使用 analytics dashboard 获取热点信息
    const dashRes = await fetch('/api/v1/analytics/dashboard')
    const dashData = await dashRes.json()

    // 构建 ECharts 散点图
    // TODO: 对接 /hotspots API
    renderMap([])
  } catch (e) {
    console.error(e)
  }
}

function renderMap(points) {
  if (!mapRef.value) return
  if (chart) chart.dispose()
  chart = echarts.init(mapRef.value)

  // 使用 ECharts geo + scatter
  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: function(p) {
        const d = p.data
        return `<b>${d.name || ''}</b><br/>帖文: ${d.post_count || 0}<br/>优先级: ${d.priority_level || '-'}`
      }
    },
    geo: {
      map: 'world',
      roam: true,
      center: [96, 22],
      zoom: 4,
      itemStyle: { areaColor: '#e7e7e7', borderColor: '#ccc' },
      emphasis: { itemStyle: { areaColor: '#ddd' } }
    },
    series: [{
      name: '灾情热点',
      type: 'scatter',
      coordinateSystem: 'geo',
      data: points,
      symbolSize: function(val) {
        return Math.max(10, Math.min(60, val[2] || 10))
      },
      itemStyle: {
        color: function(p) {
          const level = p.data.priority_level
          if (level === 'P0') return '#f56c6c'
          if (level === 'P1') return '#e6a23c'
          if (level === 'P2') return '#409eff'
          return '#909399'
        },
        shadowBlur: 10,
        shadowColor: 'rgba(0,0,0,0.2)'
      }
    }]
  })
}

async function rebuild() {
  loading.value = true
  try {
    await rebuildHotspots()
    ElMessage.success('灾情热点已重建')
    await loadRanking()
  } catch (e) {
    ElMessage.error('重建失败')
  } finally {
    loading.value = false
  }
}

async function refreshPriorityAction() {
  loading.value = true
  try {
    await refreshPriority(true)
    ElMessage.success('优先级已刷新')
    await loadRanking()
  } catch (e) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

async function loadRanking() {
  // TODO: 对接 /priority/ranking API
  // 暂时从 dashboard 获取
  try {
    const res = await fetch('/api/v1/analytics/dashboard')
    const data = await res.json()
    // 构造临时数据
    ranking.value = (data.top_distress_areas || []).map((a, i) => ({
      hotspot_id: i,
      location_name: a.area,
      post_count: a.distress_count * 3,
      distress_count: a.distress_count,
      estimated_trapped: a.distress_count * 5,
      priority_level: a.distress_count > 5 ? 'P0' : a.distress_count > 2 ? 'P1' : 'P2',
      priority_score: a.distress_count / 10,
      priority_reason: '',
      has_rescue_team: false,
      road_accessible: true,
    }))
  } catch (e) {
    console.error(e)
  }
}

function priorityTagType(level) {
  const map = { P0: 'danger', P1: 'warning', P2: 'primary', P3: 'info' }
  return map[level] || 'info'
}

function priorityColor(level) {
  const map = { P0: '#f56c6c', P1: '#e6a23c', P2: '#409eff', P3: '#909399' }
  return map[level] || '#909399'
}

onMounted(async () => {
  await nextTick()
  loadMapData()
  loadRanking()
})
</script>

<style scoped>
.map-container { height: 600px; }
.priority-card { height: 600px; overflow-y: auto; }
.priority-list { display: flex; flex-direction: column; gap: 10px; }
.priority-item {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 10px;
  border-left: 4px solid #909399;
}
.priority-p0 { border-left-color: #f56c6c; background: #fef0f0; }
.priority-p1 { border-left-color: #e6a23c; background: #fdf6ec; }
.priority-p2 { border-left-color: #409eff; background: #f0f6ff; }
.priority-p3 { border-left-color: #909399; }
.priority-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.location-name { font-weight: 600; font-size: 14px; }
.priority-meta { display: flex; gap: 12px; font-size: 12px; color: #909399; margin-bottom: 4px; }
.priority-score { margin-bottom: 4px; }
.priority-reason { font-size: 12px; color: #606266; margin-bottom: 4px; line-height: 1.4; }
.priority-badges { display: flex; gap: 4px; }
</style>
