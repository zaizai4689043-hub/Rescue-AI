<template>
  <div class="assessment-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">灾情评估报告</h2>
        <span class="title-badge">{{ total }} 份评估</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建评估</el-button>
    </div>

    <!-- 统计图表区 -->
    <el-card class="chart-card" shadow="never">
      <div class="chart-header">
        <span class="chart-title">损毁等级分布</span>
      </div>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="disaster" label="关联灾情" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.disaster?.title || '-' }}</template>
        </el-table-column>
        <el-table-column prop="damage_level" label="损毁等级" width="130" align="center">
          <template #default="{ row }">
            <span class="damage-tag" :style="{ background: damageColor(row.damage_level) + '18', color: damageColor(row.damage_level), borderColor: damageColor(row.damage_level) + '40' }">
              {{ damageLabel(row.damage_level) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="building_count_affected" label="建筑影响" width="100" align="center">
          <template #default="{ row }">{{ row.building_count_affected || 0 }}</template>
        </el-table-column>
        <el-table-column prop="casualty_estimate" label="伤亡估计" width="100" align="center">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.casualty_estimate > 0 }">{{ row.casualty_estimate || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="injured_estimate" label="受伤估计" width="100" align="center">
          <template #default="{ row }">{{ row.injured_estimate || 0 }}</template>
        </el-table-column>
        <el-table-column prop="area_affected" label="影响面积" width="110" align="center">
          <template #default="{ row }">{{ row.area_affected ? row.area_affected + ' km²' : '0 km²' }}</template>
        </el-table-column>
        <el-table-column prop="assessor" label="评估人" width="100">
          <template #default="{ row }">{{ row.assessor?.real_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="评估时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDetail(row)">查看</el-button>
            <el-button type="warning" link @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除该评估记录?" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 20px; justify-content: flex-end; display: flex"
        @size-change="loadData"
        @current-change="loadData"
      />
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="评估详情" width="650px" destroy-on-close>
      <el-descriptions :column="2" border v-if="currentRow">
        <el-descriptions-item label="关联灾情" :span="2">{{ currentRow.disaster?.title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="损毁等级">
          <span class="damage-tag" :style="{ background: damageColor(currentRow.damage_level) + '18', color: damageColor(currentRow.damage_level), borderColor: damageColor(currentRow.damage_level) + '40' }">
            {{ damageLabel(currentRow.damage_level) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="评估人">{{ currentRow.assessor?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="建筑影响数">{{ currentRow.building_count_affected || 0 }} 栋</el-descriptions-item>
        <el-descriptions-item label="伤亡估计">
          <span :class="{ 'text-danger': currentRow.casualty_estimate > 0 }">{{ currentRow.casualty_estimate || 0 }} 人</span>
        </el-descriptions-item>
        <el-descriptions-item label="受伤估计">{{ currentRow.injured_estimate || 0 }} 人</el-descriptions-item>
        <el-descriptions-item label="影响面积">{{ currentRow.area_affected || 0 }} km²</el-descriptions-item>
        <el-descriptions-item label="基础设施损毁" :span="2">{{ currentRow.infrastructure_damage || '无描述' }}</el-descriptions-item>
        <el-descriptions-item label="建议" :span="2">{{ currentRow.recommendations || '无建议' }}</el-descriptions-item>
        <el-descriptions-item label="评估时间" :span="2">{{ formatTime(currentRow.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 新建/编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="editId ? '编辑评估' : '新建评估'" size="520px" direction="rtl" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="110px" label-position="top">
        <el-form-item label="关联灾情" prop="disaster_id">
          <el-select v-model="form.disaster_id" placeholder="请选择灾情" filterable style="width: 100%" :loading="disasterLoading">
            <el-option v-for="d in disasterList" :key="d.id" :label="d.title" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="损毁等级" prop="damage_level">
          <div class="damage-options">
            <div
              v-for="lv in DAMAGE_LEVELS" :key="lv.value"
              class="damage-option"
              :class="{ active: form.damage_level === lv.value }"
              :style="form.damage_level === lv.value ? { borderColor: lv.color, background: lv.color + '12', color: lv.color } : {}"
              @click="form.damage_level = lv.value"
            >
              <span class="damage-dot" :style="{ background: lv.color }"></span>
              {{ lv.label }}
            </div>
          </div>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="建筑影响数">
              <el-input-number v-model="form.building_count_affected" :min="0" controls-position="right" style="width: 100%" placeholder="栋" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="影响面积 (km²)">
              <el-input-number v-model="form.area_affected" :min="0" :precision="2" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="伤亡估计">
              <el-input-number v-model="form.casualty_estimate" :min="0" controls-position="right" style="width: 100%" placeholder="人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="受伤估计">
              <el-input-number v-model="form.injured_estimate" :min="0" controls-position="right" style="width: 100%" placeholder="人" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="基础设施损毁描述">
          <el-input v-model="form.infrastructure_damage" type="textarea" :rows="3" placeholder="描述道路、桥梁、供水、供电等基础设施损毁情况" />
        </el-form-item>
        <el-form-item label="救援建议">
          <el-input v-model="form.recommendations" type="textarea" :rows="3" placeholder="输入救援建议和优先级安排" />
        </el-form-item>
        <el-form-item style="margin-top: 12px">
          <el-button type="primary" :loading="saving" @click="handleSubmit" style="width: 120px">{{ editId ? '保存修改' : '提交评估' }}</el-button>
          <el-button @click="drawerVisible = false">取 消</el-button>
        </el-form-item>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getAssessments, createAssessment, getAssessment, updateAssessment, deleteAssessment } from '../api/assessment'
import { getDisasters } from '../api/disaster'
import { DAMAGE_LEVELS } from '../utils/constants'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const chartRef = ref(null)
let chartInstance = null

// 灾情列表(用于下拉)
const disasterList = ref([])
const disasterLoading = ref(false)

// 详情
const detailVisible = ref(false)
const currentRow = ref(null)

// 抽屉
const drawerVisible = ref(false)
const formRef = ref(null)
const editId = ref(null)
const form = reactive({
  disaster_id: null,
  damage_level: '',
  building_count_affected: 0,
  casualty_estimate: 0,
  injured_estimate: 0,
  area_affected: 0,
  infrastructure_damage: '',
  recommendations: '',
})

const formRules = {
  disaster_id: [{ required: true, message: '请选择关联灾情', trigger: 'change' }],
  damage_level: [{ required: true, message: '请选择损毁等级', trigger: 'change' }],
}

const damageLabel = (v) => DAMAGE_LEVELS.find(d => d.value === v)?.label || v
const damageColor = (v) => DAMAGE_LEVELS.find(d => d.value === v)?.color || '#909399'
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const resetForm = () => {
  editId.value = null
  Object.assign(form, {
    disaster_id: null, damage_level: '', building_count_affected: 0,
    casualty_estimate: 0, injured_estimate: 0, area_affected: 0,
    infrastructure_damage: '', recommendations: '',
  })
}

const openCreate = () => {
  resetForm()
  loadDisasterList()
  drawerVisible.value = true
}

const openEdit = (row) => {
  editId.value = row.id
  loadDisasterList()
  Object.assign(form, {
    disaster_id: row.disaster_id,
    damage_level: row.damage_level,
    building_count_affected: row.building_count_affected || 0,
    casualty_estimate: row.casualty_estimate || 0,
    injured_estimate: row.injured_estimate || 0,
    area_affected: row.area_affected || 0,
    infrastructure_damage: row.infrastructure_damage || '',
    recommendations: row.recommendations || '',
  })
  drawerVisible.value = true
}

const showDetail = async (row) => {
  try {
    const res = await getAssessment(row.id)
    currentRow.value = res.data
  } catch { currentRow.value = row }
  detailVisible.value = true
}

const handleDelete = async (id) => {
  try {
    await deleteAssessment(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) { /* handled */ }
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.infrastructure_damage) delete payload.infrastructure_damage
    if (!payload.recommendations) delete payload.recommendations
    if (editId.value) {
      await updateAssessment(editId.value, payload)
      ElMessage.success('保存成功')
    } else {
      await createAssessment(payload)
      ElMessage.success('创建成功')
    }
    drawerVisible.value = false
    loadData()
  } catch (e) { /* handled */ } finally { saving.value = false }
}

const loadDisasterList = async () => {
  disasterLoading.value = true
  try {
    const res = await getDisasters({ page: 1, page_size: 200 })
    disasterList.value = res.data.items || res.data || []
  } catch { disasterList.value = [] } finally { disasterLoading.value = false }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getAssessments({ page: page.value, page_size: pageSize.value })
    const d = res.data
    tableData.value = d.items || d || []
    total.value = d.total ?? tableData.value.length
    await nextTick()
    renderChart()
  } catch (e) { /* handled */ } finally { loading.value = false }
}

const renderChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  // 统计损毁等级分布
  const counts = {}
  DAMAGE_LEVELS.forEach(lv => { counts[lv.value] = 0 })
  tableData.value.forEach(item => {
    if (counts[item.damage_level] !== undefined) counts[item.damage_level]++
  })
  const option = {
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: '#0F1A30', borderColor: 'rgba(120,190,255,0.22)',
      textStyle: { color: '#E8F1FF' },
    },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: DAMAGE_LEVELS.map(lv => lv.label),
      axisLine: { lineStyle: { color: 'rgba(120,190,255,0.2)' } },
      axisLabel: { color: '#93A6C4', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(120,190,255,0.08)' } },
      axisLabel: { color: '#5A6B8A' },
    },
    series: [{
      type: 'bar',
      barWidth: 40,
      data: DAMAGE_LEVELS.map(lv => ({
        value: counts[lv.value],
        itemStyle: { color: lv.color, borderRadius: [4, 4, 0, 0], shadowBlur: 10, shadowColor: lv.color + '55' },
      })),
    }],
  }
  chartInstance.setOption(option)
}

watch(() => [page.value, pageSize.value], () => loadData())

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => chartInstance?.resize())
})
</script>

<style scoped>
.assessment-page { position: relative; z-index: 1; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--deck-text);
  font-family: var(--deck-font-display);
  letter-spacing: 0.04em;
  margin: 0;
}
.title-badge {
  font-size: 12px;
  background: var(--deck-cyan-soft);
  color: var(--deck-cyan);
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 500;
  border: 1px solid rgba(56, 225, 255, 0.25);
}

.chart-card { margin-bottom: 20px; }
.chart-header { margin-bottom: 8px; }
.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--deck-text);
  font-family: var(--deck-font-display);
  letter-spacing: 0.05em;
}
.chart-container { width: 100%; height: 220px; }

.table-card { }
.damage-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid;
}
.text-danger { color: var(--deck-rose); font-weight: 600; }

.damage-options {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  width: 100%;
}
.damage-option {
  flex: 1;
  min-width: 100px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1.5px solid rgba(120, 190, 255, 0.16);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  background: rgba(6, 12, 24, 0.5);
  color: var(--deck-text-2);
}
.damage-option:hover { border-color: rgba(56, 225, 255, 0.45); }
.damage-option.active { font-weight: 600; }
.damage-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 8px currentColor;
}
</style>
