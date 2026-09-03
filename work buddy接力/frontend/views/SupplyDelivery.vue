<template>
  <div class="supply-delivery">
    <!-- 顶部统计 -->
    <el-row :gutter="12" style="margin-bottom: 12px">
      <el-col :span="5" v-for="(card, i) in statCards" :key="i">
        <div class="stat-card">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
      </el-col>
      <el-col :span="4">
        <el-button type="primary" @click="loadData" :loading="loading" style="margin-top:8px">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 左：投送队列 -->
      <el-col :span="14">
        <el-card shadow="hover">
          <template #header>
            <span><el-icon><Box /></el-icon> 物资投送队列</span>
          </template>
          <el-table :data="queue" stripe size="small" v-loading="loading">
            <el-table-column prop="priority" label="优先级" width="70">
              <template #default="{ row }">
                <el-tag :type="priorityType(row.priority)" effect="dark" size="small">{{ row.priority }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="target_location" label="投送目标" width="120" />
            <el-table-column prop="drone_id_str" label="无人机" width="100" />
            <el-table-column label="物资" min-width="200">
              <template #default="{ row }">
                <div v-for="(item, i) in row.manifest" :key="i" class="manifest-item">
                  {{ item.item }} ×{{ item.qty }}
                  <span class="weight">({{ (item.weight_kg * item.qty).toFixed(1) }}kg)</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="total_weight_kg" label="总重" width="70">
              <template #default="{ row }">{{ row.total_weight_kg }}kg</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="deliveryStatusType(row.status)" size="small">{{ deliveryStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button v-if="row.status === 'pending'" size="small" type="primary" @click="planDelivery(row)">
                  规划航线
                </el-button>
                <el-button v-if="row.status === 'en_route' || row.status === 'loading'" size="small" type="success" @click="openConfirm(row)">
                  确认收到
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!queue.length && !loading" description="暂无投送任务" />
        </el-card>
      </el-col>

      <!-- 右：标准物资包 + AI 规划 -->
      <el-col :span="10">
        <el-card shadow="hover" style="margin-bottom: 12px">
          <template #header><span><el-icon><Files /></el-icon> 标准物资包</span></template>
          <el-collapse v-model="activePackages">
            <el-collapse-item v-for="(pkg, key) in packages" :key="key" :name="key" :title="`${key} - ${pkg.name}`">
              <div v-for="(item, i) in pkg.items" :key="i" class="pkg-item">
                <span>{{ item.item }} ×{{ item.qty }}</span>
                <span class="weight">{{ (item.weight_kg * item.qty).toFixed(1) }}kg · {{ item.category }}</span>
              </div>
              <div class="pkg-total">总重: {{ pkgTotal(pkg.items) }}kg</div>
            </el-collapse-item>
          </el-collapse>
        </el-card>

        <el-card shadow="hover">
          <template #header><span><el-icon><MagicStick /></el-icon> AI 物资规划</span></template>
          <el-input v-model="aiHotspotInput" type="textarea" :rows="3" placeholder="输入灾情热点信息（JSON 格式）" />
          <el-button type="primary" size="small" style="margin-top:8px" @click="aiPlan" :loading="aiLoading">
            AI 推荐方案
          </el-button>
          <div v-if="aiResult" class="ai-result">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="推荐物资包">{{ aiResult.recommended_package }}</el-descriptions-item>
              <el-descriptions-item label="推荐无人机">{{ aiResult.drone_assignment }}</el-descriptions-item>
              <el-descriptions-item label="总重量">{{ aiResult.total_weight_kg }}kg</el-descriptions-item>
              <el-descriptions-item label="投送方式">{{ aiResult.drop_method }} / {{ aiResult.drop_altitude_m }}m</el-descriptions-item>
              <el-descriptions-item label="方案理由">{{ aiResult.rationale }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 确认收货弹窗 -->
    <el-dialog v-model="confirmDialog" title="确认物资收到" width="400px">
      <div v-if="confirmTarget" style="margin-bottom: 12px">
        <p>目标: {{ confirmTarget.target_location }} | 物资: {{ confirmTarget.total_items }} 件 / {{ confirmTarget.total_weight_kg }}kg</p>
      </div>
      <el-form label-width="80px">
        <el-form-item label="实收数量">
          <el-input-number v-model="confirmForm.received_count" :min="0" :max="confirmTarget?.total_items || 100" />
        </el-form-item>
        <el-form-item label="受领人">
          <el-input v-model="confirmForm.received_by" placeholder="受领人/单位" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="confirmForm.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="confirmDialog = false">取消</el-button>
        <el-button type="primary" @click="submitConfirm">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { supplyApi } from '../api/drone'

const loading = ref(false)
const queue = ref([])
const stats = ref({})
const packages = ref({})
const activePackages = ref(['P0'])
const aiLoading = ref(false)
const aiHotspotInput = ref('')
const aiResult = ref(null)

// 确认弹窗
const confirmDialog = ref(false)
const confirmTarget = ref(null)
const confirmForm = ref({ received_count: 0, received_by: '', note: '' })

const statCards = computed(() => [
  { label: '投送总数', value: stats.value.total || 0, color: '#409eff' },
  { label: '待处理', value: stats.value.pending || 0, color: '#909399' },
  { label: '运输中', value: stats.value.in_transit || 0, color: '#e6a23c' },
  { label: '已投送', value: stats.value.delivered || 0, color: '#67c23a' },
  { label: '总重量', value: (stats.value.total_weight_kg || 0) + 'kg', color: '#f56c6c' },
])

function priorityType(p) {
  return { P0: 'danger', P1: 'danger', P2: 'warning', P3: 'info' }[p] || 'info'
}
function deliveryStatusType(s) {
  return { pending: 'info', loading: 'warning', en_route: 'warning', delivered: 'success', confirmed: 'success', failed: 'danger' }[s] || 'info'
}
function deliveryStatusLabel(s) {
  return { pending: '待处理', loading: '装载中', en_route: '运输中', delivered: '已投送', confirmed: '已确认', failed: '失败' }[s] || s
}
function pkgTotal(items) {
  return items.reduce((s, i) => s + i.weight_kg * i.qty, 0).toFixed(1)
}

async function loadData() {
  loading.value = true
  try {
    const [q, s, p] = await Promise.all([
      supplyApi.getQueue(),
      supplyApi.getStats(),
      supplyApi.getPackages(),
    ])
    queue.value = q
    stats.value = s
    packages.value = p
  } catch (e) {
    // 降级
  } finally {
    loading.value = false
  }
}

async function planDelivery(row) {
  try {
    const result = await supplyApi.planDelivery(row.id)
    ElMessage.success(`航线已规划 · ${result.drone_id} · 单程${result.flight_time.one_way_min}分钟`)
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '规划失败')
  }
}

function openConfirm(row) {
  confirmTarget.value = row
  confirmForm.value = { received_count: row.total_items, received_by: '', note: '' }
  confirmDialog.value = true
}

async function submitConfirm() {
  if (!confirmTarget.value) return
  try {
    await supplyApi.confirmDelivery(confirmTarget.value.id, confirmForm.value)
    ElMessage.success('确认成功')
    confirmDialog.value = false
    loadData()
  } catch (e) {
    ElMessage.error('确认失败')
  }
}

async function aiPlan() {
  aiLoading.value = true
  try {
    const hotspotData = JSON.parse(aiHotspotInput.value || '{}')
    const result = await supplyApi.aiPlan(hotspotData, [])
    aiResult.value = result
  } catch (e) {
    ElMessage.error('请输入有效 JSON')
  } finally {
    aiLoading.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.supply-delivery { padding: 4px; }
.stat-card {
  background: #fff; border: 1px solid #e4e7ed; border-radius: 8px;
  padding: 12px; text-align: center;
}
.stat-value { font-size: 22px; font-weight: 700; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.manifest-item { font-size: 12px; color: #606266; }
.manifest-item .weight { color: #c0c4cc; margin-left: 4px; }
.pkg-item {
  display: flex; justify-content: space-between;
  padding: 3px 0; font-size: 13px; color: #606266;
}
.pkg-item .weight { color: #c0c4cc; font-size: 11px; }
.pkg-total { margin-top: 4px; font-weight: 600; color: #303133; }
.ai-result { margin-top: 12px; }
</style>
