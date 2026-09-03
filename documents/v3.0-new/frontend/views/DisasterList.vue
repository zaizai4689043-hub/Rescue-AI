<template>
  <div class="page-container">
    <h2 class="page-title">灾情列表</h2>

    <el-card style="margin-top: 20px">
      <el-form :inline="true">
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 140px">
            <el-option v-for="s in DISASTER_STATUS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">搜索</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="140" show-overflow-tooltip />
        <el-table-column prop="disaster_type" label="类型" width="120">
          <template #default="{ row }">{{ typeLabel(row.disaster_type) }}</template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <span :style="{ color: SEVERITY_COLORS[row.severity], fontWeight: 600 }">{{ SEVERITY_LABELS[row.severity] || row.severity }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reporter_name" label="上报人" width="100" />
        <el-table-column prop="is_rescue_requested" label="救援请求" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_rescue_requested ? 'danger' : 'info'" size="small">{{ row.is_rescue_requested ? '需要' : '无需' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上报时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDetail(row)">查看</el-button>
            <el-button type="warning" link @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除该灾情?" @confirm="handleDelete(row.id)">
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
    <el-dialog v-model="detailVisible" title="灾情详情" width="600px">
      <el-descriptions :column="2" border v-if="currentRow">
        <el-descriptions-item label="标题" :span="2">{{ currentRow.title }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ typeLabel(currentRow.disaster_type) }}</el-descriptions-item>
        <el-descriptions-item label="严重程度">
          <span :style="{ color: SEVERITY_COLORS[currentRow.severity] }">{{ SEVERITY_LABELS[currentRow.severity] }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(currentRow.status)" size="small">{{ statusLabel(currentRow.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="上报人">{{ currentRow.reporter_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="救援请求">
          <el-tag :type="currentRow.is_rescue_requested ? 'danger' : 'info'" size="small">{{ currentRow.is_rescue_requested ? '需要救援' : '无需救援' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="灾情等级">{{ currentRow.disaster_level || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预估被困">{{ currentRow.estimated_people_trapped ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="经济损失">{{ currentRow.estimated_economic_loss ? currentRow.estimated_economic_loss + ' 万元' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentRow.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="纬度">{{ currentRow.latitude ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="经度">{{ currentRow.longitude ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="地址" :span="2">{{ currentRow.address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="上报时间" :span="2">{{ formatTime(currentRow.created_at) }}</el-descriptions-item>
      </el-descriptions>

      <!-- AI分析面板 -->
      <div class="ai-panel" v-if="currentRow" style="margin-top: 20px">
        <h4 style="margin:0 0 12px;font-size:15px;font-weight:600;color:var(--deck-text);font-family:var(--deck-font-display);letter-spacing:0.04em;">AI建筑损毁分析</h4>
        <template v-if="aiResult">
          <div class="ai-grid">
            <div class="ai-item">
              <span class="ai-label">损毁等级</span>
              <span class="ai-value" :style="{ color: damageColor(aiResult.damage_level), fontWeight: 700, fontSize: '16px' }">{{ aiResult.damage_level }}</span>
            </div>
            <div class="ai-item">
              <span class="ai-label">置信度</span>
              <span class="ai-value">{{ (aiResult.confidence * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <div style="margin:10px 0">
            <span class="ai-label">损毁程度</span>
            <el-progress :percentage="aiResult.damage_percentage" :color="damageColor(aiResult.damage_level)" style="margin-top:4px" />
          </div>
          <div style="margin:10px 0">
            <span class="ai-label">建筑风险评分 ({{ aiResult.building_risk_score }}/100)</span>
            <el-progress :percentage="aiResult.building_risk_score" :color="'#FB4B6B'" style="margin-top:4px" />
          </div>
          <div style="margin:10px 0">
            <span class="ai-label">人员风险星级</span>
            <div style="margin-top:4px">
              <span v-for="i in 5" :key="i" :style="{ color: i <= aiResult.personnel_risk_stars ? '#FFB020' : 'rgba(90,107,138,0.5)', fontSize: '18px' }">★</span>
            </div>
          </div>
          <div style="margin:10px 0">
            <span class="ai-label">建议操作</span>
            <el-tag type="danger" effect="dark" style="margin-left:8px">{{ aiResult.suggested_action }}</el-tag>
          </div>
          <div style="margin:10px 0">
            <span class="ai-label">检测特征</span>
            <div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:6px">
              <el-tag v-for="f in aiResult.detected_features" :key="f" size="small">{{ f }}</el-tag>
            </div>
          </div>
          <div style="font-size:11px;color:var(--deck-text-3);margin-top:10px">
            模型: {{ aiResult.model_version }} | 分析时间: {{ formatTime(aiResult.analysis_time) }}
          </div>
        </template>
        <template v-else>
          <el-empty description="暂无AI分析结果" :image-size="60" />
          <el-button type="primary" :loading="aiTriggering" @click="triggerAi">触发AI分析</el-button>
        </template>
      </div>
    </el-dialog>

    <!-- 编辑抽屉 -->
    <el-drawer v-model="editVisible" title="编辑灾情" size="500px" direction="rtl">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="类型" prop="disaster_type">
          <el-select v-model="editForm.disaster_type" style="width: 100%">
            <el-option v-for="t in DISASTER_TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="灾情等级">
          <el-select v-model="editForm.disaster_level" clearable style="width: 100%">
            <el-option v-for="l in DISASTER_LEVELS" :key="l.value" :label="l.label" :value="l.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度" prop="severity">
          <el-rate v-model="editForm.severity" :max="5" show-text :texts="['轻微','一般','较重','严重','极其严重']" />
        </el-form-item>
        <el-form-item label="预估被困">
          <el-input-number v-model="editForm.estimated_people_trapped" :min="0" style="width: 100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="经济损失">
          <el-input-number v-model="editForm.estimated_economic_loss" :min="0" :precision="2" placeholder="万元" style="width: 100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option v-for="s in DISASTER_STATUS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="救援请求">
          <el-select v-model="editForm.is_rescue_requested" style="width: 100%">
            <el-option v-for="opt in RESCUE_REQUEST_OPTIONS" :key="String(opt.value)" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="editForm.address" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSaveEdit">保 存</el-button>
          <el-button @click="editVisible = false">取 消</el-button>
        </el-form-item>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getDisasters, getDisaster, updateDisaster, deleteDisaster } from '../api/disaster'
import { analyzeDisaster, getAiAnalysis } from '../api/ai'
import { DISASTER_TYPES, DISASTER_STATUS, DISASTER_TYPE_MAP, DISASTER_LEVELS, RESCUE_REQUEST_OPTIONS, SEVERITY_LABELS, SEVERITY_COLORS } from '../utils/constants'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filters = reactive({ status: '' })

const detailVisible = ref(false)
const editVisible = ref(false)
const currentRow = ref(null)
const aiResult = ref(null)
const aiLoading = ref(false)
const aiTriggering = ref(false)
const editFormRef = ref(null)
const editForm = reactive({ title: '', disaster_type: '', severity: 1, disaster_level: '', is_rescue_requested: false, estimated_people_trapped: null, estimated_economic_loss: null, status: '', description: '', address: '' })
let editId = null

const editRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const typeLabel = (v) => DISASTER_TYPE_MAP[v] || v
const statusLabel = (v) => DISASTER_STATUS.find(s => s.value === v)?.label || v
const statusType = (v) => DISASTER_STATUS.find(s => s.value === v)?.type || ''
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.status) params.status = filters.status
    const res = await getDisasters(params)
    const d = res.data
    tableData.value = d.items || d || []
    total.value = d.total ?? tableData.value.length
  } catch (e) { /* handled */ } finally { loading.value = false }
}

const resetFilters = () => {
  filters.status = ''
  page.value = 1
  loadData()
}

const showDetail = async (row) => {
  try {
    const res = await getDisaster(row.id)
    currentRow.value = res.data
  } catch { currentRow.value = row }
  // 加载AI分析结果
  aiResult.value = currentRow.value?.ai_analysis_result || null
  if (!aiResult.value && currentRow.value?.id) {
    try {
      const r = await getAiAnalysis(currentRow.value.id)
      aiResult.value = r.data
    } catch { aiResult.value = null }
  }
  detailVisible.value = true
}

const triggerAi = async () => {
  if (!currentRow.value?.id) return
  aiTriggering.value = true
  try {
    const res = await analyzeDisaster(currentRow.value.id)
    aiResult.value = res.data
    // 刷新列表以更新 ai_analysis_result
    await loadData()
  } catch { /* handled */ } finally { aiTriggering.value = false }
}

const damageColor = (level) => {
  const map = { '轻微': '#2DD4BF', '中度': '#FFB020', '严重': '#FB4B6B', '完全倒塌': '#DC143C' }
  return map[level] || '#5A6B8A'
}

const openEdit = (row) => {
  editId = row.id
  Object.assign(editForm, {
    title: row.title,
    disaster_type: row.disaster_type,
    severity: row.severity,
    disaster_level: row.disaster_level || '',
    is_rescue_requested: row.is_rescue_requested ?? false,
    estimated_people_trapped: row.estimated_people_trapped ?? null,
    estimated_economic_loss: row.estimated_economic_loss ?? null,
    status: row.status,
    description: row.description || '', address: row.address || ''
  })
  editVisible.value = true
}

const handleSaveEdit = async () => {
  await editFormRef.value?.validate()
  saving.value = true
  try {
    await updateDisaster(editId, editForm)
    ElMessage.success('保存成功')
    editVisible.value = false
    loadData()
  } catch (e) { /* handled */ } finally { saving.value = false }
}

const handleDelete = async (id) => {
  try {
    await deleteDisaster(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) { /* handled */ }
}

onMounted(() => loadData())
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
.ai-panel { border-top: 1px solid var(--deck-border); padding-top: 16px; }
.ai-grid { display: flex; gap: 30px; }
.ai-item { display: flex; flex-direction: column; gap: 4px; }
.ai-label { font-size: 12px; color: var(--deck-text-3); }
.ai-value { font-size: 14px; color: var(--deck-text); font-weight: 500; }
</style>
