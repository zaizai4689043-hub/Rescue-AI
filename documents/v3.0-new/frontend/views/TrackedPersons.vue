<template>
  <div class="trapped-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">受困者追踪</h2>
        <span class="title-badge" v-if="stats.total">{{ stats.total }} 人记录</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增记录</el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <div class="stat-box">
          <div class="stat-num deck-numeric" style="color: #38E1FF">{{ stats.total }}</div>
          <div class="stat-label">总人数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-box">
          <div class="stat-num deck-numeric" style="color: #FB4B6B">{{ stats.by_status?.waiting || 0 }}</div>
          <div class="stat-label">待搜救</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-box">
          <div class="stat-num deck-numeric" style="color: #FFB020">{{ stats.by_status?.searching || 0 }}</div>
          <div class="stat-label">搜救中</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-box">
          <div class="stat-num deck-numeric" style="color: #2DD4BF">{{ stats.by_status?.rescued || 0 }}</div>
          <div class="stat-sub">
            <div class="stat-label">已救出</div>
            <span class="rescue-rate">{{ stats.rescue_rate || 0 }}%</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- START 四色看板 -->
    <el-row :gutter="12" class="priority-board">
      <el-col :span="6" v-for="p in TRAPPED_PRIORITY" :key="p.value">
        <div class="priority-card" :style="{ borderTopColor: p.color }">
          <div class="priority-head">
            <span class="priority-dot" :style="{ background: p.color }"></span>
            <span class="priority-name">{{ p.label.split(' - ')[0] }}</span>
          </div>
          <div class="priority-count" :style="{ color: p.color }">{{ stats.by_priority?.[p.value] || 0 }}</div>
          <div class="priority-desc">{{ p.label.split(' - ')[1] }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="灾情">
          <el-select v-model="filters.disaster_id" clearable placeholder="全部灾情" style="width: 180px" filterable>
            <el-option v-for="d in disasterList" :key="d.id" :label="d.title" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 130px">
            <el-option v-for="s in TRAPPED_STATUS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" clearable placeholder="全部优先级" style="width: 150px">
            <el-option v-for="p in TRAPPED_PRIORITY" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="姓名" width="100">
          <template #default="{ row }">{{ row.name || '未知' }}</template>
        </el-table-column>
        <el-table-column prop="age" label="年龄" width="70" align="center">
          <template #default="{ row }">{{ row.age || '-' }}</template>
        </el-table-column>
        <el-table-column prop="gender" label="性别" width="70" align="center">
          <template #default="{ row }">{{ genderLabel(row.gender) }}</template>
        </el-table-column>
        <el-table-column prop="location" label="位置" min-width="160" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="plain">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="130" align="center">
          <template #default="{ row }">
            <span class="priority-tag" :style="{ background: priorityColor(row.priority) + '18', color: priorityColor(row.priority), borderColor: priorityColor(row.priority) + '50' }">
              <span class="priority-dot-sm" :style="{ background: priorityColor(row.priority) }"></span>
              {{ priorityLabel(row.priority) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="condition" label="伤情" width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.condition || '-' }}</template>
        </el-table-column>
        <el-table-column prop="reported_at" label="报告时间" width="170">
          <template #default="{ row }">{{ formatTime(row.reported_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-if="row.status !== 'rescued'" type="success" link @click="handleRescue(row)" :disabled="row.status === 'rescued'">救出</el-button>
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除该记录?" @confirm="handleDelete(row.id)">
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

    <!-- 新建/编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="editId ? '编辑记录' : '新增受困者'" size="520px" direction="rtl" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px" label-position="top">
        <el-form-item label="关联灾情" prop="disaster_id">
          <el-select v-model="form.disaster_id" placeholder="请选择灾情" filterable style="width: 100%" :disabled="!!editId">
            <el-option v-for="d in disasterList" :key="d.id" :label="d.title" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="姓名">
              <el-input v-model="form.name" placeholder="未知可留空" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="年龄">
              <el-input-number v-model="form.age" :min="0" :max="150" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="性别">
              <el-select v-model="form.gender" placeholder="未知" clearable style="width: 100%">
                <el-option value="male" label="男" />
                <el-option value="female" label="女" />
                <el-option value="unknown" label="未知" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="位置描述" prop="location">
          <el-input v-model="form.location" placeholder="例：XX小区3号楼2单元废墟" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="纬度">
              <el-input-number v-model="form.latitude" :precision="6" :step="0.001" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="经度">
              <el-input-number v-model="form.longitude" :precision="6" :step="0.001" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="优先级">
          <div class="priority-options">
            <div
              v-for="p in TRAPPED_PRIORITY" :key="p.value"
              class="priority-option"
              :class="{ active: form.priority === p.value }"
              :style="form.priority === p.value ? { borderColor: p.color, background: p.color + '12', color: p.color } : {}"
              @click="form.priority = p.value"
            >
              <span class="priority-dot" :style="{ background: p.color }"></span>
              {{ p.label }}
            </div>
          </div>
        </el-form-item>
        <el-form-item label="伤情描述">
          <el-input v-model="form.condition" type="textarea" :rows="2" placeholder="描述伤情和受困状况" />
        </el-form-item>
        <el-form-item label="报告人">
          <el-input v-model="form.reported_by" placeholder="报告人姓名" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="其他补充信息" />
        </el-form-item>
        <el-form-item style="margin-top: 12px">
          <el-button type="primary" :loading="saving" @click="handleSubmit" style="width: 120px">{{ editId ? '保存修改' : '提交记录' }}</el-button>
          <el-button @click="drawerVisible = false">取 消</el-button>
        </el-form-item>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTrappedPersons, createTrappedPerson, updateTrappedPerson, rescueTrappedPerson, deleteTrappedPerson, getTrappedPersonStatistics } from '../api/trappedPerson'
import { getDisasters } from '../api/disaster'
import { TRAPPED_STATUS, TRAPPED_PRIORITY } from '../utils/constants'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const disasterList = ref([])
const stats = reactive({ total: 0, by_status: {}, by_priority: {}, rescue_rate: 0 })

const filters = reactive({ disaster_id: null, status: '', priority: '' })

const drawerVisible = ref(false)
const formRef = ref(null)
const editId = ref(null)
const form = reactive({
  disaster_id: null, name: '', age: null, gender: '', location: '',
  latitude: null, longitude: null, priority: 'red',
  condition: '', reported_by: '', notes: '',
})

const formRules = {
  disaster_id: [{ required: true, message: '请选择关联灾情', trigger: 'change' }],
  location: [{ required: true, message: '请输入位置描述', trigger: 'blur' }],
}

const statusLabel = (v) => TRAPPED_STATUS.find(s => s.value === v)?.label || v
const statusType = (v) => TRAPPED_STATUS.find(s => s.value === v)?.type || ''
const priorityLabel = (v) => TRAPPED_PRIORITY.find(p => p.value === v)?.label?.split(' - ')[0] || v
const priorityColor = (v) => TRAPPED_PRIORITY.find(p => p.value === v)?.color || '#909399'
const genderLabel = (v) => ({ male: '男', female: '女', unknown: '未知' }[v] || '-')
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const resetForm = () => {
  editId.value = null
  Object.assign(form, {
    disaster_id: null, name: '', age: null, gender: '', location: '',
    latitude: null, longitude: null, priority: 'red',
    condition: '', reported_by: '', notes: '',
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
    name: row.name || '',
    age: row.age,
    gender: row.gender || '',
    location: row.location,
    latitude: row.latitude,
    longitude: row.longitude,
    priority: row.priority,
    condition: row.condition || '',
    reported_by: row.reported_by || '',
    notes: row.notes || '',
  })
  drawerVisible.value = true
}

const handleRescue = async (row) => {
  try {
    await ElMessageBox.confirm(`确认将 "${row.name || '未知'}" 标记为已救出？`, '标记救出', { type: 'success', confirmButtonText: '确认救出', cancelButtonText: '取消' })
    await rescueTrappedPerson(row.id)
    ElMessage.success('已标记救出')
    loadData()
    loadStats()
  } catch (e) { /* cancelled or error */ }
}

const handleDelete = async (id) => {
  try {
    await deleteTrappedPerson(id)
    ElMessage.success('删除成功')
    loadData()
    loadStats()
  } catch (e) { /* handled */ }
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.name) delete payload.name
    if (!payload.condition) delete payload.condition
    if (!payload.reported_by) delete payload.reported_by
    if (!payload.notes) delete payload.notes
    if (!payload.gender) delete payload.gender
    if (editId.value) {
      await updateTrappedPerson(editId.value, payload)
      ElMessage.success('保存成功')
    } else {
      await createTrappedPerson(payload)
      ElMessage.success('创建成功')
    }
    drawerVisible.value = false
    loadData()
    loadStats()
  } catch (e) { /* handled */ } finally { saving.value = false }
}

const handleSearch = () => {
  page.value = 1
  loadData()
}

const resetFilters = () => {
  filters.disaster_id = null
  filters.status = ''
  filters.priority = ''
  page.value = 1
  loadData()
}

const loadDisasterList = async () => {
  try {
    const res = await getDisasters({ page: 1, page_size: 200 })
    disasterList.value = res.data.items || res.data || []
  } catch { disasterList.value = [] }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.disaster_id) params.disaster_id = filters.disaster_id
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    const res = await getTrappedPersons(params)
    const d = res.data
    tableData.value = d.items || d || []
    total.value = d.total ?? tableData.value.length
  } catch (e) { /* handled */ } finally { loading.value = false }
}

const loadStats = async () => {
  try {
    const params = {}
    if (filters.disaster_id) params.disaster_id = filters.disaster_id
    const res = await getTrappedPersonStatistics(params)
    Object.assign(stats, res.data)
  } catch (e) { /* handled */ }
}

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
.trapped-page { position: relative; z-index: 1; }
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

.stat-row { margin-bottom: 16px; }
.stat-box {
  position: relative;
  background: var(--deck-panel);
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid var(--deck-border);
  backdrop-filter: blur(14px);
  overflow: hidden;
}
.stat-box::before {
  content: '';
  position: absolute;
  top: 0; left: 16%; right: 16%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(56, 225, 255, 0.3), transparent);
}
.stat-num {
  font-size: 30px;
  font-weight: 700;
  line-height: 1;
  text-shadow: 0 0 18px currentColor;
  opacity: 0.95;
}
.stat-label { font-size: 13px; color: var(--deck-text-2); margin-top: 2px; }
.stat-sub { display: flex; align-items: center; gap: 8px; }
.rescue-rate {
  font-size: 12px; color: var(--deck-teal);
  background: rgba(45, 212, 191, 0.12);
  border: 1px solid rgba(45, 212, 191, 0.3);
  padding: 2px 8px; border-radius: 10px;
  font-weight: 600;
}

.priority-board { margin-bottom: 16px; }
.priority-card {
  position: relative;
  background: var(--deck-panel);
  border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid var(--deck-border);
  border-top: 3px solid #5A6B8A;
  backdrop-filter: blur(14px);
  transition: transform 0.25s, box-shadow 0.25s;
}
.priority-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
}
.priority-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.priority-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
  box-shadow: 0 0 10px currentColor;
}
.priority-dot-sm { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.priority-name { font-size: 13px; color: var(--deck-text-2); font-weight: 500; }
.priority-count {
  font-size: 28px; font-weight: 700; line-height: 1.2;
  font-family: var(--deck-font-display);
  text-shadow: 0 0 16px currentColor;
}
.priority-desc { font-size: 11px; color: var(--deck-text-3); margin-top: 2px; }

.filter-card { margin-bottom: 16px; }
.filter-form { display: flex; flex-wrap: wrap; align-items: flex-end; }

.table-card { }
.priority-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid;
}

.priority-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}
.priority-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1.5px solid rgba(120, 190, 255, 0.16);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  background: rgba(6, 12, 24, 0.5);
  color: var(--deck-text-2);
}
.priority-option:hover { border-color: rgba(56, 225, 255, 0.45); }
.priority-option.active { font-weight: 600; }
</style>
