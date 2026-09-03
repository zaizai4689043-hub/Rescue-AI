<template>
  <div class="page-container">
    <h2 class="page-title">志愿者管理</h2>

    <!-- 顶部统计 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6">
        <StatCard title="总人数" :value="stats.total" icon="User" color="#38E1FF" />
      </el-col>
      <el-col :span="6">
        <StatCard title="待命" :value="stats.available" icon="CircleCheck" color="#2DD4BF" />
      </el-col>
      <el-col :span="6">
        <StatCard title="任务中" :value="stats.on_mission" icon="Loading" color="#FFB020" />
      </el-col>
      <el-col :span="6">
        <StatCard title="已分配" :value="stats.assigned" icon="Position" color="#A78BFA" />
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <el-form :inline="true">
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 130px">
            <el-option v-for="s in VOLUNTEER_STATUS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="技能">
          <el-select v-model="filters.skills" clearable multiple collapse-tags placeholder="选择技能" style="width: 240px">
            <el-option v-for="sk in VOLUNTEER_SKILLS" :key="sk.value" :label="sk.label" :value="sk.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">搜索</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
          <el-button type="success" :icon="Plus" @click="openCreate">新增志愿者</el-button>
          <el-button type="info" :icon="Opportunity" @click="matchVisible = true">技能匹配</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="skills" label="技能" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="sk in (row.skills || [])" :key="sk" size="small" style="margin-right: 4px; margin-bottom: 2px">{{ skillLabel(sk) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="experience_years" label="经验(年)" width="90" align="center" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_location" label="当前位置" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.current_location || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="warning" link @click="openAssign(row)" :disabled="row.status === 'on_mission'">分配任务</el-button>
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除该志愿者?" @confirm="handleDelete(row.id)">
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

    <!-- 分配任务弹窗 -->
    <el-dialog v-model="assignVisible" title="分配任务" width="500px">
      <el-form :model="assignForm" label-width="100px">
        <el-form-item label="志愿者">{{ assignForm.name }}</el-form-item>
        <el-form-item label="任务描述" required>
          <el-input v-model="assignForm.task_description" type="textarea" :rows="3" placeholder="请输入任务描述" />
        </el-form-item>
        <el-form-item label="任务地点" required>
          <el-input v-model="assignForm.location" placeholder="请输入任务地点" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :loading="assigning" @click="handleAssign">确认分配</el-button>
      </template>
    </el-dialog>

    <!-- 技能匹配弹窗 -->
    <el-dialog v-model="matchVisible" title="技能匹配" width="600px">
      <el-form :inline="true" style="margin-bottom: 16px">
        <el-form-item label="所需技能">
          <el-select v-model="matchSkills" multiple collapse-tags placeholder="选择需要的技能" style="width: 320px">
            <el-option v-for="sk in VOLUNTEER_SKILLS" :key="sk.value" :label="sk.label" :value="sk.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleMatch" :loading="matching">匹配</el-button>
        </el-form-item>
      </el-form>
      <el-table :data="matchedVolunteers" stripe v-loading="matching" style="width: 100%">
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="skills" label="技能">
          <template #default="{ row }">
            <el-tag v-for="sk in (row.skills || [])" :key="sk" size="small" style="margin-right: 4px">{{ skillLabel(sk) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="experience_years" label="经验(年)" width="90" align="center" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 新增/编辑抽屉 -->
    <el-drawer v-model="formVisible" :title="isEdit ? '编辑志愿者' : '新增志愿者'" size="480px" direction="rtl">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入电话" />
        </el-form-item>
        <el-form-item label="关联用户ID" prop="user_id" v-if="!isEdit">
          <el-input-number v-model="form.user_id" :min="1" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="技能" prop="skills">
          <el-select v-model="form.skills" multiple placeholder="选择技能" style="width: 100%">
            <el-option v-for="sk in VOLUNTEER_SKILLS" :key="sk.value" :label="sk.label" :value="sk.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="经验年限">
          <el-input-number v-model="form.experience_years" :min="0" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="当前位置">
          <el-input v-model="form.current_location" placeholder="请输入当前位置" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="备注信息" />
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
import { Search, Refresh, Plus, Opportunity } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getVolunteers, createVolunteer, updateVolunteer, assignVolunteer, deleteVolunteer, matchVolunteers, getVolunteerStatistics } from '../api/volunteer'
import { VOLUNTEER_STATUS, VOLUNTEER_SKILLS, VOLUNTEER_STATUS_MAP, VOLUNTEER_SKILL_MAP } from '../utils/constants'
import StatCard from '../components/StatCard.vue'

const loading = ref(false)
const saving = ref(false)
const assigning = ref(false)
const matching = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filters = reactive({ status: '', skills: [] })
const stats = reactive({ total: 0, available: 0, on_mission: 0, assigned: 0 })

const statusLabel = (v) => VOLUNTEER_STATUS_MAP[v] || v
const statusType = (v) => VOLUNTEER_STATUS.find(s => s.value === v)?.type || ''
const skillLabel = (v) => VOLUNTEER_SKILL_MAP[v] || v

// 分配任务
const assignVisible = ref(false)
const assignForm = reactive({ id: null, name: '', task_description: '', location: '' })

// 技能匹配
const matchVisible = ref(false)
const matchSkills = ref([])
const matchedVolunteers = ref([])

// 新增/编辑抽屉
const formVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
let editId = null
const form = reactive({ user_id: null, name: '', phone: '', skills: [], experience_years: 0, current_location: '', notes: '' })
const formRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入电话', trigger: 'blur' }],
  user_id: [{ required: true, message: '请输入关联用户ID', trigger: 'blur' }],
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.status) params.status = filters.status
    if (filters.skills.length) params.skills = filters.skills.join(',')
    const res = await getVolunteers(params)
    const d = res.data
    tableData.value = d.items || []
    total.value = d.total ?? 0
  } catch (e) { /* handled */ } finally { loading.value = false }
}

const loadStats = async () => {
  try {
    const res = await getVolunteerStatistics()
    const d = res.data
    stats.total = d.total_count ?? 0
    stats.available = d.by_status?.available ?? 0
    stats.on_mission = d.by_status?.on_mission ?? 0
    stats.assigned = d.by_status?.assigned ?? 0
  } catch (e) { /* handled */ }
}

const resetFilters = () => {
  filters.status = ''
  filters.skills = []
  page.value = 1
  loadData()
}

const openCreate = () => {
  isEdit.value = false
  editId = null
  Object.assign(form, { user_id: null, name: '', phone: '', skills: [], experience_years: 0, current_location: '', notes: '' })
  formVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  editId = row.id
  Object.assign(form, {
    user_id: row.user_id,
    name: row.name,
    phone: row.phone,
    skills: row.skills || [],
    experience_years: row.experience_years,
    current_location: row.current_location || '',
    notes: row.notes || '',
  })
  formVisible.value = true
}

const handleSave = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      const { user_id, ...data } = form
      await updateVolunteer(editId, data)
    } else {
      await createVolunteer(form)
    }
    ElMessage.success(isEdit.value ? '保存成功' : '创建成功')
    formVisible.value = false
    loadData()
    loadStats()
  } catch (e) { /* handled */ } finally { saving.value = false }
}

const handleDelete = async (id) => {
  try {
    await deleteVolunteer(id)
    ElMessage.success('删除成功')
    loadData()
    loadStats()
  } catch (e) { /* handled */ }
}

const openAssign = (row) => {
  Object.assign(assignForm, { id: row.id, name: row.name, task_description: '', location: '' })
  assignVisible.value = true
}

const handleAssign = async () => {
  if (!assignForm.task_description || !assignForm.location) {
    ElMessage.warning('请填写完整的任务信息')
    return
  }
  assigning.value = true
  try {
    await assignVolunteer(assignForm.id, {
      task_description: assignForm.task_description,
      location: assignForm.location,
    })
    ElMessage.success('分配成功')
    assignVisible.value = false
    loadData()
    loadStats()
  } catch (e) { /* handled */ } finally { assigning.value = false }
}

const handleMatch = async () => {
  if (!matchSkills.value.length) {
    ElMessage.warning('请选择至少一项技能')
    return
  }
  matching.value = true
  try {
    const res = await matchVolunteers(matchSkills.value.join(','))
    matchedVolunteers.value = res.data || []
    if (!matchedVolunteers.value.length) {
      ElMessage.info('未找到匹配的志愿者')
    }
  } catch (e) { /* handled */ } finally { matching.value = false }
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
