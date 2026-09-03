<template>
  <div class="social-dashboard">
    <!-- 顶部统计 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <StatCard title="活跃帖文" :value="dashboard?.summary?.total_posts || 0" icon="ChatDotRound" color="#409eff" />
      </el-col>
      <el-col :span="6">
        <StatCard title="呼救信号" :value="dashboard?.summary?.distress_posts || 0" icon="WarnTriangleFilled" color="#f56c6c" />
      </el-col>
      <el-col :span="6">
        <StatCard title="平均严重度" :value="dashboard?.summary?.avg_severity || 0" icon="Histogram" color="#e6a23c" />
      </el-col>
      <el-col :span="6">
        <StatCard title="平均可信度" :value="((dashboard?.summary?.avg_credibility || 0) * 100).toFixed(0) + '%'" icon="CircleCheck" color="#67c23a" />
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="16">
      <!-- 损毁类型分布 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>损毁类型分布</span></template>
          <v-chart class="chart" :option="damageTypeOption" autoresize />
        </el-card>
      </el-col>

      <!-- 关键词频率排行 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>关键词频率排行 TOP15</span></template>
          <v-chart class="chart" :option="keywordOption" autoresize />
        </el-card>
      </el-col>

      <!-- 情感时间线 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>情感时间线变化</span></template>
          <v-chart class="chart" :option="sentimentOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- 新兴关键词预警 + 呼救区域 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span><el-icon><WarnTriangleFilled /></el-icon> 新兴关键词预警</span>
              <el-tag type="danger" size="small">次生灾害前兆</el-tag>
            </div>
          </template>
          <el-table :data="dashboard?.emerging_keywords || []" size="small" stripe>
            <el-table-column prop="keyword" label="关键词" width="120" />
            <el-table-column prop="recent_count" label="近期" width="80" />
            <el-table-column prop="previous_count" label="之前" width="80" />
            <el-table-column label="增长倍数">
              <template #default="{ row }">
                <el-tag type="danger">×{{ row.increase_ratio }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>呼救信号区域排行</span></template>
          <el-table :data="dashboard?.top_distress_areas || []" size="small" stripe>
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="area" label="区域" />
            <el-table-column prop="distress_count" label="呼救数" width="100">
              <template #default="{ row }">
                <el-tag type="danger">{{ row.distress_count }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 微博列表 -->
    <el-card shadow="hover" style="margin-top: 16px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>微博社情瀑布流</span>
          <div>
            <el-select v-model="filter.sentiment" placeholder="情感筛选" clearable size="small" style="width: 120px; margin-right: 8px">
              <el-option label="紧急" value="urgent" />
              <el-option label="负面" value="negative" />
              <el-option label="中性" value="neutral" />
              <el-option label=" hopeful" value="hopeful" />
            </el-select>
            <el-select v-model="filter.damage_type" placeholder="类型筛选" clearable size="small" style="width: 140px; margin-right: 8px">
              <el-option label="人员伤亡" value="人员伤亡" />
              <el-option label="房屋倒塌" value="房屋倒塌" />
              <el-option label="道路中断" value="道路中断" />
              <el-option label="次生灾害" value="次生灾害" />
              <el-option label="救援进展" value="救援进展" />
              <el-option label="震感反馈" value="震感反馈" />
            </el-select>
            <el-button type="primary" size="small" @click="loadPosts">刷新</el-button>
          </div>
        </div>
      </template>
      <el-table :data="posts" size="small" stripe style="width: 100%">
        <el-table-column prop="published_at" label="时间" width="160" />
        <el-table-column prop="text" label="内容" show-overflow-tooltip min-width="300" />
        <el-table-column prop="damage_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="damageTypeColor(row.damage_type)" size="small">{{ row.damage_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sentiment" label="情感" width="80">
          <template #default="{ row }">
            <el-tag :type="sentimentColor(row.sentiment)" size="small">{{ sentimentLabel(row.sentiment) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity_vote" label="严重度" width="80">
          <template #default="{ row }">
            <span :style="{ color: row.severity_vote >= 4 ? '#f56c6c' : '#909399' }">{{ '★'.repeat(row.severity_vote) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="呼救" width="60">
          <template #default="{ row }">
            <el-icon v-if="row.has_distress_signal" color="#f56c6c"><WarnTriangleFilled /></el-icon>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="page"
        :page-size="20"
        :total="total"
        layout="prev, pager, next"
        style="margin-top: 12px"
        @current-change="loadPosts"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { WarnTriangleFilled } from '@element-plus/icons-vue'
import StatCard from '../components/StatCard.vue'
import { getDashboard } from '../api/analytics'
import { getPosts } from '../api/weibo'

use([CanvasRenderer, PieChart, BarChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const dashboard = ref(null)
const posts = ref([])
const page = ref(1)
const total = ref(0)
const filter = reactive({ sentiment: '', damage_type: '' })

const damageTypeOption = computed(() => {
  const data = dashboard.value?.damage_type_distribution || []
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: data.map(d => ({ name: d.damage_type, value: d.count })),
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }
    }]
  }
})

const keywordOption = computed(() => {
  const data = (dashboard.value?.keyword_frequencies || []).slice(0, 15).reverse()
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '15%', right: '5%', top: '5%', bottom: '5%' },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: data.map(d => d.keyword) },
    series: [{
      type: 'bar',
      data: data.map(d => d.count),
      itemStyle: { color: '#409eff', borderRadius: [0, 4, 4, 0] }
    }]
  }
})

const sentimentOption = computed(() => {
  const data = dashboard.value?.sentiment_timeline || []
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, data: ['紧急', '负面', '中性', ' hopeful'] },
    grid: { left: '8%', right: '5%', top: '5%', bottom: '15%' },
    xAxis: { type: 'category', data: data.map(d => d.timestamp) },
    yAxis: { type: 'value' },
    series: [
      { name: '紧急', type: 'line', data: data.map(d => d.urgent), smooth: true, itemStyle: { color: '#f56c6c' } },
      { name: '负面', type: 'line', data: data.map(d => d.negative), smooth: true, itemStyle: { color: '#e6a23c' } },
      { name: '中性', type: 'line', data: data.map(d => d.neutral), smooth: true, itemStyle: { color: '#909399' } },
      { name: ' hopeful', type: 'line', data: data.map(d => d.hopeful), smooth: true, itemStyle: { color: '#67c23a' } },
    ]
  }
})

function damageTypeColor(type) {
  const map = { '人员伤亡': 'danger', '房屋倒塌': 'danger', '次生灾害': 'warning', '道路中断': 'warning', '救援进展': 'success', '震感反馈': 'info' }
  return map[type] || 'info'
}

function sentimentColor(s) {
  const map = { urgent: 'danger', negative: 'warning', neutral: 'info', hopeful: 'success' }
  return map[s] || 'info'
}

function sentimentLabel(s) {
  const map = { urgent: '紧急', negative: '负面', neutral: '中性', hopeful: ' hopeful' }
  return map[s] || s
}

async function loadDashboard() {
  try {
    const res = await getDashboard()
    dashboard.value = res.data
  } catch (e) { console.error(e) }
}

async function loadPosts() {
  try {
    const res = await getPosts({ page: page.value, page_size: 20, ...filter })
    posts.value = res.data.items
    total.value = res.data.total
  } catch (e) { console.error(e) }
}

watch(filter, () => { page.value = 1; loadPosts() })

onMounted(() => {
  loadDashboard()
  loadPosts()
})
</script>

<style scoped>
.social-dashboard { padding: 0; }
.stat-row { margin-bottom: 16px; }
.chart { height: 300px; }
</style>
