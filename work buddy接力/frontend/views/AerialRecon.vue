<template>
  <div class="aerial-recon">
    <!-- 顶部：创建侦察任务 -->
    <el-card shadow="hover" style="margin-bottom: 12px">
      <template #header>
        <span><el-icon><Camera /></el-icon> 空中侦察 — 灾情侦察 / 路线研判</span>
      </template>
      <el-form :inline="true" size="small">
        <el-form-item label="区域名称">
          <el-input v-model="newRecon.area_name" placeholder="如实皆村" style="width: 160px" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number v-model="newRecon.center_lng" :precision="4" :step="0.01" style="width: 120px" />
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number v-model="newRecon.center_lat" :precision="4" :step="0.01" style="width: 120px" />
        </el-form-item>
        <el-form-item label="无人机">
          <el-select v-model="newRecon.drone_id_str" placeholder="自动分配" clearable style="width: 140px">
            <el-option v-for="d in fleet" :key="d.drone_id_str" :label="d.drone_id_str" :value="d.drone_id_str" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="createRecon" :loading="creating">创建侦察任务</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16">
      <!-- 左：侦察记录列表 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span><el-icon><List /></el-icon> 侦察记录</span></template>
          <div v-for="r in recons" :key="r.id" class="recon-item" :class="{ active: selectedRecon?.id === r.id }" @click="selectRecon(r)">
            <div class="recon-header">
              <span class="recon-area">{{ r.area_name }}</span>
              <el-tag size="small" :type="reconStatusType(r.status)">{{ reconStatusLabel(r.status) }}</el-tag>
            </div>
            <div class="recon-meta">
              {{ r.drone_id_str }} · {{ r.images?.length || 0 }} 张图片 ·
              {{ r.lidar_point_count?.toLocaleString() }} 点云
            </div>
            <div class="recon-analysis" v-if="r.route_analysis">{{ r.route_analysis.substring(0, 60) }}...</div>
          </div>
          <el-empty v-if="!recons.length" description="暂无侦察记录" :image-size="60" />
        </el-card>
      </el-col>

      <!-- 右：侦察详情 -->
      <el-col :span="16">
        <template v-if="selectedRecon">
          <!-- 图片画廊 -->
          <el-card shadow="hover" style="margin-bottom: 12px">
            <template #header>
              <div style="display:flex; justify-content:space-between; align-items:center">
                <span><el-icon><Picture /></el-icon> 航拍素材 ({{ selectedRecon.images?.length || 0 }})</span>
                <el-upload :show-file-list="false" :before-upload="uploadImage" accept="image/*">
                  <el-button size="small" type="primary"><el-icon><Upload /></el-icon> 上传图片</el-button>
                </el-upload>
              </div>
            </template>
            <div class="image-gallery" v-if="selectedRecon.images?.length">
              <div v-for="(img, i) in selectedRecon.images" :key="i" class="image-card">
                <img :src="img.url || placeholderImg" :alt="img.note || `航拍图${i+1}`" />
                <div class="img-meta">{{ img.alt || 0 }}m · {{ img.note || '' }}</div>
              </div>
            </div>
            <el-empty v-else description="暂无航拍图片" :image-size="60" />
          </el-card>

          <!-- AI 路线分析 -->
          <el-card shadow="hover" style="margin-bottom: 12px">
            <template #header>
              <div style="display:flex; justify-content:space-between; align-items:center">
                <span><el-icon><Position /></el-icon> AI 路线研判</span>
                <div>
                  <el-tag v-if="selectedRecon.analyzed_by" size="small" type="info">{{ selectedRecon.analyzed_by }}</el-tag>
                  <el-button size="small" type="primary" style="margin-left:8px" @click="analyzeRoute" :loading="analyzing">
                    {{ selectedRecon.status === 'analyzed' ? '重新分析' : 'AI 分析' }}
                  </el-button>
                </div>
              </div>
            </template>

            <div v-if="selectedRecon.route_assessment">
              <!-- 总体评估 -->
              <el-alert :title="selectedRecon.route_analysis" type="info" :closable="false" style="margin-bottom: 12px" />

              <!-- 可通行路线 -->
              <div v-if="selectedRecon.route_assessment.accessible_routes?.length" style="margin-bottom: 12px">
                <h4 style="color:#67c23a"><el-icon><CircleCheck /></el-icon> 可通行路线</h4>
                <el-table :data="selectedRecon.route_assessment.accessible_routes" size="small" stripe>
                  <el-table-column prop="from" label="起点" width="80" />
                  <el-table-column prop="to" label="终点" width="80" />
                  <el-table-column prop="via" label="路线" min-width="100" />
                  <el-table-column prop="estimated_time_min" label="预计" width="60">
                    <template #default="{ row }">{{ row.estimated_time_min }}min</template>
                  </el-table-column>
                  <el-table-column prop="notes" label="备注" min-width="100" />
                </el-table>
              </div>

              <!-- 阻断路线 -->
              <div v-if="selectedRecon.route_assessment.blocked_routes?.length" style="margin-bottom: 12px">
                <h4 style="color:#f56c6c"><el-icon><CircleClose /></el-icon> 阻断路线</h4>
                <el-table :data="selectedRecon.route_assessment.blocked_routes" size="small" stripe>
                  <el-table-column prop="from" label="起点" width="80" />
                  <el-table-column prop="to" label="终点" width="80" />
                  <el-table-column prop="block_type" label="阻断类型" width="100" />
                  <el-table-column prop="block_location" label="位置" width="80" />
                  <el-table-column prop="detour" label="绕行方案" min-width="120" />
                </el-table>
              </div>

              <!-- 危险区域 -->
              <div v-if="selectedRecon.route_assessment.hazard_zones?.length" style="margin-bottom: 12px">
                <h4 style="color:#e6a23c"><el-icon><Warning /></el-icon> 危险区域</h4>
                <el-table :data="selectedRecon.route_assessment.hazard_zones" size="small" stripe>
                  <el-table-column prop="location" label="位置" width="100" />
                  <el-table-column prop="hazard_type" label="类型" width="100" />
                  <el-table-column prop="severity" label="严重度" width="80">
                    <template #default="{ row }">
                      <el-tag :type="row.severity === 'high' ? 'danger' : row.severity === 'medium' ? 'warning' : 'info'" size="small">
                        {{ row.severity }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="advice" label="建议" min-width="120" />
                </el-table>
              </div>

              <!-- 推荐路线 -->
              <div v-if="selectedRecon.route_assessment.recommended_routes?.length">
                <h4 style="color:#409eff"><el-icon><Promotion /></el-icon> 推荐路线</h4>
                <div v-for="(r, i) in selectedRecon.route_assessment.recommended_routes" :key="i" class="rec-route">
                  <el-tag type="primary" size="small">优先级 {{ r.priority }}</el-tag>
                  <span class="route-name">{{ r.route }}</span>
                  <span class="route-reason">{{ r.reason }}</span>
                </div>
              </div>
            </div>

            <el-empty v-else description="点击 AI 分析生成路线研判" :image-size="60" />
          </el-card>

          <!-- 发现的灾情要素 -->
          <el-card shadow="hover" v-if="selectedRecon.discovered_elements?.length">
            <template #header><span><el-icon><Discover /></el-icon> 发现的灾情要素</span></template>
            <el-tag v-for="(el, i) in selectedRecon.discovered_elements" :key="i"
              :type="el.severity === 'high' ? 'danger' : el.severity === 'medium' ? 'warning' : 'info'"
              size="small" style="margin: 4px">
              {{ el.type }} ×{{ el.count || 1 }}
            </el-tag>
          </el-card>
        </template>

        <el-empty v-else description="选择一条侦察记录查看详情" />
      </el-col>
    </el-row>

    <!-- 路线研判汇总 -->
    <el-card shadow="hover" style="margin-top: 12px" v-if="routeSummary.total_recons">
      <template #header><span><el-icon><MapLocation /></el-icon> 全域路线研判汇总</span></template>
      <el-row :gutter="16">
        <el-col :span="8">
          <div class="summary-card green">
            <div class="summary-count">{{ routeSummary.accessible_routes?.length || 0 }}</div>
            <div class="summary-label">可通行路线</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="summary-card red">
            <div class="summary-count">{{ routeSummary.blocked_routes?.length || 0 }}</div>
            <div class="summary-label">阻断路线</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="summary-card orange">
            <div class="summary-count">{{ routeSummary.hazard_zones?.length || 0 }}</div>
            <div class="summary-label">危险区域</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { reconApi, droneApi } from '../api/drone'

const recons = ref([])
const fleet = ref([])
const selectedRecon = ref(null)
const routeSummary = ref({})
const creating = ref(false)
const analyzing = ref(false)

const newRecon = ref({
  area_name: '',
  center_lng: 95.95,
  center_lat: 21.20,
  drone_id_str: '',
})

const placeholderImg = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iIzQwNTM1OCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmaWxsPSIjOTA5Mzk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+5qCP5L2c6LS15aSWPC90ZXh0Pjwvc3ZnPg=='

function reconStatusType(s) {
  return { pending: 'info', in_progress: 'warning', analyzed: 'success', completed: 'success' }[s] || 'info'
}
function reconStatusLabel(s) {
  return { pending: '待侦察', in_progress: '侦察中', analyzed: '已分析', completed: '已完成' }[s] || s
}

async function loadData() {
  try {
    const [r, f, rs] = await Promise.all([
      reconApi.getList(),
      droneApi.getFleet(),
      reconApi.getRouteSummary(),
    ])
    recons.value = r
    fleet.value = f
    routeSummary.value = rs
  } catch (e) {
    // 降级
  }
}

function selectRecon(r) {
  selectedRecon.value = r
}

async function createRecon() {
  if (!newRecon.value.area_name) {
    ElMessage.warning('请输入区域名称')
    return
  }
  creating.value = true
  try {
    const result = await reconApi.create(newRecon.value)
    ElMessage.success(`侦察任务已创建 · ${result.drone_id}`)
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function uploadImage(file) {
  if (!selectedRecon.value) return false
  try {
    const url = URL.createObjectURL(file)
    await reconApi.uploadImage(selectedRecon.value.id, {
      url,
      taken_at: new Date().toISOString(),
      note: file.name,
    })
    ElMessage.success('图片已上传')
    loadData()
  } catch (e) {
    ElMessage.error('上传失败')
  }
  return false
}

async function analyzeRoute() {
  if (!selectedRecon.value) return
  analyzing.value = true
  try {
    const result = await reconApi.analyzeRoute(selectedRecon.value.id, {
      image_b64: null,
      context_data: { area: selectedRecon.value.area_name },
    })
    selectedRecon.value = result
    ElMessage.success('路线分析完成')
    loadData()
  } catch (e) {
    ElMessage.error('分析失败')
  } finally {
    analyzing.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.aerial-recon { padding: 4px; }
.recon-item {
  padding: 10px; border-radius: 6px; cursor: pointer;
  border: 1px solid transparent; margin-bottom: 6px;
  transition: all 0.2s;
}
.recon-item:hover { background: #f5f7fa; }
.recon-item.active { background: #ecf5ff; border-color: #409eff; }
.recon-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 4px;
}
.recon-area { font-weight: 600; font-size: 14px; }
.recon-meta { font-size: 12px; color: #909399; }
.recon-analysis { font-size: 12px; color: #606266; margin-top: 4px; }
.image-gallery {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
}
.image-card {
  border-radius: 6px; overflow: hidden; border: 1px solid #e4e7ed;
}
.image-card img { width: 100%; height: 100px; object-fit: cover; display: block; }
.img-meta { font-size: 11px; color: #909399; padding: 2px 4px; }
.rec-route {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 0; border-bottom: 1px solid #f0f0f0;
}
.route-name { font-weight: 600; }
.route-reason { color: #606266; font-size: 13px; }
.summary-card {
  border-radius: 8px; padding: 16px; text-align: center;
}
.summary-card.green { background: #f0f9eb; }
.summary-card.red { background: #fef0f0; }
.summary-card.orange { background: #fdf6ec; }
.summary-count { font-size: 28px; font-weight: 700; }
.summary-card.green .summary-count { color: #67c23a; }
.summary-card.red .summary-count { color: #f56c6c; }
.summary-card.orange .summary-count { color: #e6a23c; }
.summary-label { font-size: 13px; color: #606266; margin-top: 4px; }
</style>
