<template>
  <div class="user-manage-page">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
    </div>

    <el-card class="table-card" shadow="never">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="username" label="用户名" width="130" />
        <el-table-column prop="real_name" label="姓名" width="110" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="role" label="角色" width="120" align="center">
          <template #default="{ row }">
            <span class="role-tag" :style="{ background: roleColor(row.role) + '15', color: roleColor(row.role), borderColor: roleColor(row.role) + '40' }">
              {{ roleLabel(row.role) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="organization" label="组织" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.organization || '-' }}</template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="handleToggleActive(row)"
              :loading="row._toggling"
              inline-prompt
              active-text="启"
              inactive-text="禁"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="openRoleDialog(row)">修改角色</el-button>
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

    <!-- 修改角色弹窗 -->
    <el-dialog v-model="roleDialogVisible" title="修改用户角色" width="420px" destroy-on-close>
      <div class="role-dialog-body" v-if="currentUser">
        <div class="user-info-row">
          <span class="user-avatar">{{ (currentUser.real_name || currentUser.username)?.[0] }}</span>
          <div>
            <div class="user-name">{{ currentUser.real_name }} <span class="user-username">@{{ currentUser.username }}</span></div>
            <div class="user-org">{{ currentUser.organization || '未设置组织' }}</div>
          </div>
        </div>
        <el-form label-width="80px" style="margin-top: 20px">
          <el-form-item label="当前角色">
            <span class="role-tag" :style="{ background: roleColor(currentUser.role) + '15', color: roleColor(currentUser.role) }">
              {{ roleLabel(currentUser.role) }}
            </span>
          </el-form-item>
          <el-form-item label="新角色">
            <el-select v-model="newRole" style="width: 100%">
              <el-option v-for="r in USER_ROLES" :key="r.value" :label="r.label" :value="r.value" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="roleSaving" @click="handleSaveRole">确 认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, updateUserRole, toggleUserActive } from '../api/user'
import { USER_ROLES } from '../utils/constants'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const roleDialogVisible = ref(false)
const roleSaving = ref(false)
const currentUser = ref(null)
const newRole = ref('')

const roleLabel = (v) => USER_ROLES.find(r => r.value === v)?.label || v
const roleColor = (v) => {
  const colors = { admin: '#FB4B6B', commander: '#FFB020', rescuer: '#38E1FF', medic: '#2DD4BF' }
  return colors[v] || '#5A6B8A'
}
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const openRoleDialog = (row) => {
  currentUser.value = row
  newRole.value = row.role
  roleDialogVisible.value = true
}

const handleSaveRole = async () => {
  if (!currentUser.value || newRole.value === currentUser.value.role) {
    roleDialogVisible.value = false
    return
  }
  roleSaving.value = true
  try {
    await updateUserRole(currentUser.value.id, newRole.value)
    ElMessage.success('角色修改成功')
    roleDialogVisible.value = false
    loadData()
  } catch (e) { /* handled */ } finally { roleSaving.value = false }
}

const handleToggleActive = async (row) => {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确认${action}用户 "${row.real_name}"？`, `${action}用户`, {
      type: row.is_active ? 'warning' : 'info',
      confirmButtonText: `确认${action}`,
      cancelButtonText: '取消',
    })
    row._toggling = true
    await toggleUserActive(row.id)
    ElMessage.success(`已${action}`)
    loadData()
  } catch (e) { /* cancelled or error */ } finally { row._toggling = false }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getUsers({ page: page.value, page_size: pageSize.value })
    const data = res.data
    tableData.value = (Array.isArray(data) ? data : data.items || []).map(u => ({ ...u, _toggling: false }))
    total.value = data.total ?? tableData.value.length
  } catch (e) { tableData.value = [] } finally { loading.value = false }
}

onMounted(() => loadData())
</script>

<style scoped>
.user-manage-page { position: relative; z-index: 1; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--deck-text);
  font-family: var(--deck-font-display);
  letter-spacing: 0.04em;
  margin: 0;
}

.table-card { }
.role-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}

.role-dialog-body { }
.user-info-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: rgba(120, 190, 255, 0.06);
  border: 1px solid var(--deck-border);
  border-radius: 10px;
}
.user-avatar {
  width: 44px; height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #38E1FF, #A78BFA);
  color: #06121F;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 0 18px rgba(56, 225, 255, 0.35);
}
.user-name { font-size: 15px; font-weight: 600; color: var(--deck-text); }
.user-username { font-size: 13px; color: var(--deck-text-3); font-weight: 400; }
.user-org { font-size: 12px; color: var(--deck-text-2); margin-top: 2px; }
</style>
