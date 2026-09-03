<template>
  <div class="page-container">
    <h2 class="page-title">资源调度中心</h2>

    <!-- 顶部统计 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6">
        <StatCard title="总资源数" :value="stats.total" icon="Box" color="#38E1FF" />
      </el-col>
      <el-col :span="6">
        <StatCard title="可用" :value="stats.available" icon="CircleCheck" color="#2DD4BF" />
      </el-col>
      <el-col :span="6">
        <StatCard title="调度中" :value="stats.dispatched" icon="Van" color="#FFB020" />
      </el-col>
      <el-col :span="6">
        <StatCard title="已消耗" :value="stats.consumed" icon="Finished" color="#93A6C4" />
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 左侧列表 -->
      <el-col :span="16">
        <el-card>
          <el-form :inline="true">
            <el-form-item label="类型">
              <el-select v-model="filters.resource_type" clearable placeholder="全部类型" style="width: 130px">
                <el-option v-for="t in RESOURCE_TYPES" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 130px">
                <el-option v-for="s in RESOURCE_STATUS" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="loadData">搜索</el-button>
              <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
              <el-button type="success" :icon="Plus" @click="openCreate">新增资源</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
            <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip />
            <el-table-column prop="resource_type" label="类型" width="90">
              <template #default="{ row }">{{ typeLabel(row.resource_type) }}</template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" align="right" />
            <el-table-column prop="unit" label="单位" width="70" />
            <el-table-column prop="location" label="位置" min-width="120" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button type="warning" link @click="openDispatch(row)" :disabled="row.status !== 'available'">调度</el-button>
                <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
                <el-popconfirm title="确认删除该资源?" @confirm="handleDelete(row.id)">
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
      </el-col>

      <!-- 右侧图表 -->
      <el-col :span="8">
        <el-card style="margin-bottom: 20px">
          <template #header><span style="font-weight:600">资源类型分布</span></template>
          <v-chart class="chart" :option="pieOption" autoresize style="height: 240px" />
        </el-card>
        <el-card>
          <template #header><span style="font-weight:600">资源状态分布</span></template>
          <v-chart class="chart" :option="barOption" autoresize style="height: 240px" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 调度弹窗 -->
    <el-dialog v-model="dispatchVisible" title="调度资源" width="480px">
      <el-form :model="dispatchForm" label-width="100px">
        <el-form-item label="资源名称">{{ dispatchForm.name }}</el-form-item>
        <el-form-item label="当前数量">{{ dispatchForm.quantity }} {{ dispatchForm.unit }}</el-form-item>
        <el-form-item label="目标位置" required>
          <el-input v-model="dispatchForm.target_location" placeholder="请输入目标位置" />
        </el-form-item>
        <el-form-item label="调度数量">
          <el-input-number v-model="dispatchForm.dispatch_quantity" :min="1" :max="dispatchForm.quantity" controls-position="right" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dispatchVisible = false">取消</el-button>
        <el-button type="primary" :loading="dispatching" @click="handleDispatch">确认调度</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑抽屉 -->
    <el-drawer v-model="formVisible" :title="isEdit ? '编辑资源' : '新增资源'" size="480px" direction="rtl">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入资源名称" />
        </el-form-item>
        <el-form-item label="类型" prop="resource_type">
          <el-select v-model="form.resource_type" placeholder="请选择类型" style="width: 100%">
            <el-option v-for="t in RESOURCE_TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="form.quantity" :min="0" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-input v-model="form.unit" placeholder="如：个、箱、辆、顶" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="form.location" placeholder="请输入存放位置" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="可选描述" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保 存</el-button>
          <el-button @click="formVisible = false">取 消</el-button>
        </el-form-item>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { getResources, createResource, updateResource, dispatchResource, deleteResource, getResourceStatistics } from '../api/resource'
import { RESOURCE_TYPES, RESOURCE_STATUS, RESOURCE_TYPE_MAP, RESOURCE_STATUS_MAP } from '../utils/constants'
import StatCard from '../components/StatCard.vue'

use([CanvasRenderer, PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const loading = ref(false)
const saving = ref(false)
const dispatching = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filters = reactive({ resource_type: '', status: '' })
const stats = reactive({ total: 0, available: 0, dispatched: 0, consumed: 0 })

const typeLabel = (v) => RESOURCE_TYPE_MAP[v] || v
const statusLabel = (v) => RESOURCE_STATUS_MAP[v] || v
const statusType = (v) => RESOURCE_STATUS.find(s => s.value === v)?.type || ''

// 图表配置
const darkTooltip = { backgroundColor: '#0F1A30', borderColor: 'rgba(120,190,255,0.22)', textStyle: { color: '#E8F1FF' } }
const pieOption = ref({
  tooltip: { trigger: 'item', ...darkTooltip },
  legend: { bottom: 0, textStyle: { color: '#93A6C4', fontSize: 11 } },
  color: ['#38E1FF', '#FFB020', '#FB4B6B', '#A78BFA', '#2DD4BF', '#7CB8FF'],
  series: [{
    type: 'pie', radius: ['35%', '65%'], data: [],
    label: { show: true, color: '#B8C8E2', fontSize: 11 },
    itemStyle: { borderColor: '#0D1629', borderWidth: 2 },
  }]
})
const barOption = ref({
  tooltip: { trigger: 'axis', ...darkTooltip },
  xAxis: {
    type: 'category', data: [],
    axisLine: { lineStyle: { color: 'rgba(120,190,255,0.2)' } },
    axisLabel: { color: '#93A6C4', fontSize: 11 },
  },
  yAxis: {
    type: 'value', minInterval: 1,
    axisLine: { show: false },
    splitLine: { lineStyle: { color: 'rgba(120,190,255,0.08)' } },
    axisLabel: { color: '#5A6B8A' },
  },
  series: [{
    type: 'bar', data: [], barWidth: 18,
    itemStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#38E1FF' }, { offset: 1, color: 'rgba(56,225,255,0.15)' }] },
      borderRadius: [4, 4, 0, 0],
    },
  }],
  grid: { left: 40, right: 20, top: 20, bottom: 30 }
})

// 调度弹窗
const dispatchVisible = ref(false)
const dispatchForm = reactive({ id: null, name: '', quantity: 0, unit: '', target_location: '', dispatch_quantity: 1 })

// 新增/编辑抽屉
const formVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
let editId = null
const form = reactive({ name: '', resource_type: '', quantity: 0, unit: '', location: '', description: '' })
const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  resource_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  unit: [{ required: true, message: '请输入单位', trigger: 'blur' }],
  location: [{ required: true, message: '请输入位置', trigger: 'blur' }],
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.resource_type) params.resource_type = filters.resource_type
    if (filters.status) params.status = filters.status
    const res = await getResources(params)
    const d = res.data
    tableData.value = d.items || []
    total.value = d.total ?? 0
  } catch (e) { /* handled */ } finally { loading.value = false }
}

const loadStats = async () => {
  try {
    const res = await getResourceStatistics()
    const d = res.data
    stats.total = d.total_count ?? 0
    stats.available = d.by_status?.available ?? 0
    stats.dispatched = d.by_status?.dispatched ?? 0
    stats.consumed = d.by_status?.consumed ?? 0

    // 饼图 - 类型分布
    if (d.by_type) {
      pieOption.value.series[0].data = Object.entries(d.by_type).map(([k, v]) => ({ name: typeLabel(k), value: v }))
    }
    // 柱状图 - 状态分布
    if (d.by_status) {
      const entries = RESOURCE_STATUS.map(s => ({ name: s.label, value: d.by_status[s.value] ?? 0 }))
      barOption.value.xAxis.data = entries.map(e => e.name)
      barOption.value.series[0].data = entries.map(e => e.value)
    }
  } catch (e) { /* handled */ }
}

const resetFilters = () => {
  filters.resource_type = ''
  filters.status = ''
  page.value = 1
  loadData()
}

const openCreate = () => {
  isEdit.value = false
  editId = null
  Object.assign(form, { name: '', resource_type: '', quantity: 0, unit: '', location: '', description: '' })
  formVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  editId = row.id
  Object.assign(form, {
    name: row.name,
    resource_type: row.resource_type,
    quantity: row.quantity,
    unit: row.unit,
    location: row.location,
    description: row.description || '',
  })
  formVisible.value = true
}

const handleSave = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      await updateResource(editId, form)
    } else {
      await createResource(form)
    }
    ElMessage.success(isEdit.value ? '保存成功' : '创建成功')
    formVisible.value = false
    loadData()
    loadStats()
  } catch (e) { /* handled */ } finally { saving.value = false }
}

const handleDelete = async (id) => {
  try {
    await deleteResource(id)
    ElMessage.success('删除成功')
    loadData()
    loadStats()
  } catch (e) { /* handled */ }
}

const openDispatch = (row) => {
  Object.assign(dispatchForm, {
    id: row.id,
    name: row.name,
    quantity: row.quantity,
    unit: row.unit,
    target_location: '',
    dispatch_quantity: row.quantity,
  })
  dispatchVisible.value = true
}

const handleDispatch = async () => {
  if (!dispatchForm.target_location) {
    ElMessage.warning('请输入目标位置')
    return
  }
  dispatching.value = true
  try {
    await dispatchResource(dispatchForm.id, {
      target_location: dispatchForm.target_location,
      quantity: dispatchForm.dispatch_quantity < dispatchForm.quantity ? dispatchForm.dispatch_quantity : undefined,
    })
    ElMessage.success('调度成功')
    dispatchVisible.value = false
    loadData()
    loadStats()
  } catch (e) { /* handled */ } finally { dispatching.value = false }
}

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--deck-text);
  font-family: var(--deck-font-display);
  letter-spacing: 0.04em;
  margin: 0;
}
</style>
