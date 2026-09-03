<template>
  <div class="decision-assistant">
    <!-- 顶部：触发分析 -->
    <el-card shadow="hover" style="margin-bottom: 16px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span><el-icon><Cpu /></el-icon> AI 决策助手 — 智能预测 + 案例匹配</span>
          <div>
            <el-input-number v-model="magnitude" :min="3" :max="10" :step="0.1" size="small" style="width: 100px; margin-right: 8px" />
            <el-input-number v-model="depthKm" :min="1" :max="100" :step="1" size="small" style="width: 100px; margin-right: 8px" />
            <el-button type="primary" @click="analyze" :loading="loading">
              <el-icon><MagicStick /></el-icon> 开始分析
            </el-button>
          </div>
        </div>
      </template>
      <div style="font-size: 13px; color: #909399">
        震级 {{ magnitude }} | 震源深度 {{ depthKm }}km | 震中 (95.94, 22.01)
        <el-tag v-if="result" :type="result.ai_powered ? 'success' : 'info'" size="small" style="margin-left: 8px">
          {{ result.ai_powered ? 'Qwen3.8-Max 智能研判' : '规则引擎降级' }}
        </el-tag>
      </div>
    </el-card>

    <div v-if="loading" class="loading-area">
      <el-skeleton :rows="12" animated />
    </div>

    <template v-if="result && !loading">
      <!-- 优先救援区域 -->
      <el-card shadow="hover" style="margin-bottom: 16px">
        <template #header>
          <span><el-icon><Aim /></el-icon> 最需要优先救援的区域</span>
        </template>
        <el-row :gutter="12">
          <el-col v-for="(area, i) in result.priority_areas" :key="i" :span="8">
            <div class="area-card">
              <div class="area-header">
                <el-tag type="danger" effect="dark" size="small">P{{ i }}</el-tag>
                <span class="area-name">{{ area.name }}</span>
              </div>
              <el-progress :percentage="Math.round((area.score || 0) * 100)" color="#f56c6c" :stroke-width="8" />
              <div class="area-reason">{{ area.reason }}</div>
              <div class="area-trapped">
                <el-icon><User /></el-icon> 预估被困: {{ area.estimated_trapped }} 人
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 行动方案 -->
      <el-card shadow="hover" style="margin-bottom: 16px">
        <template #header><span><el-icon><Promotion /></el-icon> 推荐行动方案</span></template>
        <div class="action-plan">{{ result.action_plan }}</div>
      </el-card>

      <el-row :gutter="16">
        <!-- 风险预警 -->
        <el-col :span="12">
          <el-card shadow="hover" style="margin-bottom: 16px">
            <template #header>
              <span><el-icon><WarnTriangleFilled /></el-icon> 风险预警</span>
            </template>
            <el-alert
              v-for="(warning, i) in result.risk_warnings"
              :key="i"
              :title="warning"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 8px"
            />
            <el-empty v-if="!result.risk_warnings?.length" description="暂无风险预警" :image-size="60" />
          </el-card>
        </el-col>

        <!-- 资源调配建议 -->
        <el-col :span="12">
          <el-card shadow="hover" style="margin-bottom: 16px">
            <template #header>
              <span><el-icon><Box /></el-icon> 资源调配建议</span>
            </template>
            <div v-for="(suggestion, i) in result.resource_suggestions" :key="i" class="suggestion-item">
              <el-icon color="#409eff"><CircleCheck /></el-icon>
              <span>{{ suggestion }}</span>
            </div>
            <el-empty v-if="!result.resource_suggestions?.length" description="暂无资源建议" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>

      <!-- 匹配的历史案例 -->
      <el-card shadow="hover">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span><el-icon><Files /></el-icon> 匹配的历史救援案例</span>
            <el-button text size="small" @click="showCaseLibrary = true">查看全部案例</el-button>
          </div>
        </template>
        <el-collapse>
          <el-collapse-item
            v-for="caseItem in result.matched_cases"
            :key="caseItem.case_id"
            :name="caseItem.case_id"
          >
            <template #title>
              <div class="case-header">
                <el-tag type="primary" size="small">{{ caseItem.case_id }}</el-tag>
                <span class="case-name">{{ caseItem.name }}</span>
                <el-tag type="success" size="small">相似度 {{ (caseItem.similarity_score * 100).toFixed(0) }}%</el-tag>
                <span class="case-meta">M{{ caseItem.magnitude }} | {{ caseItem.location }}</span>
              </div>
            </template>
            <div class="case-detail">
              <!-- 匹配维度 -->
              <div class="dim-scores">
                <span v-for="(score, dim) in caseItem.match_dimensions" :key="dim" class="dim-tag">
                  {{ dimLabels[dim] || dim }}: {{ (score * 100).toFixed(0) }}%
                </span>
              </div>

              <!-- 策略 -->
              <h4>关键救援策略</h4>
              <div v-for="s in caseItem.strategies" :key="s.strategy" class="strategy-item">
                <el-tag type="info" size="small">{{ s.strategy }}</el-tag>
                <span>{{ s.description }}</span>
              </div>

              <!-- 经验教训 -->
              <h4>经验教训</h4>
              <ul class="lessons-list">
                <li v-for="(lesson, i) in caseItem.lessons" :key="i">{{ lesson }}</li>
              </ul>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </template>

    <el-empty v-if="!result && !loading" description="点击「开始分析」获取 AI 决策建议" />

    <!-- 案例库弹窗 -->
    <el-dialog v-model="showCaseLibrary" title="救援案例知识库" width="70%">
      <el-table :data="caseList" stripe>
        <el-table-column prop="case_id" label="编号" width="80" />
        <el-table-column prop="name" label="案例名称" />
        <el-table-column prop="magnitude" label="震级" width="80" />
        <el-table-column prop="casualties" label="遇难/失踪" width="100" />
        <el-table-column prop="location" label="位置" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button text size="small" @click="viewCase(row.case_id)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  Cpu, MagicStick, Aim, Promotion, WarnTriangleFilled, Box,
  CircleCheck, Files, User
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { analyzeDecision, getCases } from '../api/decision'

const magnitude = ref(7.7)
const depthKm = ref(10)
const loading = ref(false)
const result = ref(null)
const showCaseLibrary = ref(false)
const caseList = ref([])

const dimLabels = {
  magnitude: '震级',
  depth_km: '深度',
  terrain: '地形',
  building_type: '建筑',
  population_density: '人口',
  season: '季节',
  infrastructure: '设施',
  secondary_hazard: '次生灾害',
  warning_capability: '预警',
  occurrence_time: '时段'
}

async function analyze() {
  loading.value = true
  result.value = null
  try {
    const res = await analyzeDecision({
      magnitude: magnitude.value,
      depthKm: depthKm.value,
      epicenter: [95.94, 22.01]
    })
    result.value = res.data
    ElMessage.success('分析完成')
  } catch (e) {
    ElMessage.error('分析失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadCases() {
  try {
    const res = await getCases()
    caseList.value = res.data.items
  } catch (e) { console.error(e) }
}

function viewCase(caseId) {
  // TODO: 跳转案例详情
  ElMessage.info(`案例 ${caseId} 详情待对接`)
}

onMounted(() => {
  loadCases()
})
</script>

<style scoped>
.loading-area { padding: 20px; }
.area-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  border-left: 4px solid #f56c6c;
}
.area-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.area-name { font-weight: 600; font-size: 15px; }
.area-reason { font-size: 13px; color: #606266; margin: 8px 0; line-height: 1.5; }
.area-trapped { font-size: 13px; color: #f56c6c; display: flex; align-items: center; gap: 4px; }
.action-plan {
  font-size: 15px;
  line-height: 1.8;
  padding: 16px;
  background: #f0f6ff;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}
.suggestion-item { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-size: 14px; }
.case-header { display: flex; align-items: center; gap: 8px; }
.case-name { font-weight: 600; }
.case-meta { color: #909399; font-size: 13px; margin-left: 8px; }
.case-detail { padding: 0 20px; }
.dim-scores { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.dim-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #f0f2f5;
  color: #606266;
}
.strategy-item { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px; font-size: 13px; }
.lessons-list { padding-left: 20px; font-size: 13px; color: #606266; }
.lessons-list li { margin-bottom: 4px; }
</style>
