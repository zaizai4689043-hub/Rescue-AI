<template>
  <div class="brief-center">
    <el-row :gutter="16">
      <!-- 左侧：简报配置 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span><el-icon><Document /></el-icon> 简报生成</span></template>
          <el-form label-width="100px" label-position="top">
            <el-form-item label="简报版本">
              <el-select v-model="version" placeholder="选择版本" clearable>
                <el-option
                  v-for="(v, k) in versions"
                  :key="k"
                  :label="v.label"
                  :value="k"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="发震时间">
              <el-date-picker
                v-model="quakeTime"
                type="datetime"
                placeholder="选择发震时间"
                value-format="YYYY-MM-DDTHH:mm:ss"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="generate" :loading="loading" style="width: 100%">
                <el-icon><MagicStick /></el-icon> 生成简报
              </el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <div class="calibration-info">
            <h4>口径红线</h4>
            <el-alert
              v-for="(val, key) in calibrations"
              :key="key"
              :title="val"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 8px"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：简报内容 -->
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>
                <el-icon><Memo /></el-icon> 灾情简报
                <el-tag v-if="currentBrief" size="small" style="margin-left: 8px">
                  {{ versions[version]?.label || '实时' }}
                </el-tag>
                <el-tag v-if="currentBrief" :type="currentBrief.ai_powered ? 'success' : 'info'" size="small" style="margin-left: 4px">
                  {{ currentBrief.ai_powered ? 'AI 生成' : '模板降级' }}
                </el-tag>
              </span>
              <el-button size="small" @click="copyBrief" v-if="currentBrief">
                <el-icon><CopyDocument /></el-icon> 复制
              </el-button>
            </div>
          </template>

          <div v-if="loading" class="brief-loading">
            <el-skeleton :rows="8" animated />
          </div>

          <div v-else-if="currentBrief" class="brief-content">
            <pre class="brief-text">{{ currentBrief.content }}</pre>

            <el-divider />

            <div class="brief-snapshot">
              <h4>态势快照</h4>
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="总帖文数">{{ currentBrief.situation_snapshot?.total_posts || 0 }}</el-descriptions-item>
                <el-descriptions-item label="呼救信号">{{ currentBrief.situation_snapshot?.distress_signals || 0 }}</el-descriptions-item>
                <el-descriptions-item label="简报时间">{{ currentBrief.generated_at?.slice(0, 19) }}</el-descriptions-item>
              </el-descriptions>

              <div v-if="currentBrief.situation_snapshot?.top_areas?.length" style="margin-top: 12px">
                <h4>重点关切区域</h4>
                <el-table :data="currentBrief.situation_snapshot.top_areas" size="small" stripe>
                  <el-table-column prop="name" label="区域" />
                  <el-table-column prop="post_count" label="帖文数" width="80" />
                  <el-table-column prop="distress_count" label="呼救" width="80" />
                  <el-table-column prop="priority" label="优先级" width="80" />
                </el-table>
              </div>

              <div v-if="currentBrief.changes_from_previous" style="margin-top: 12px">
                <el-alert :title="currentBrief.changes_from_previous" type="info" :closable="false" show-icon />
              </div>
            </div>
          </div>

          <el-empty v-else description="点击「生成简报」按钮生成灾情简报" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Document, Memo, MagicStick, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { generateBrief, getBriefVersions, previewBrief } from '../api/brief'

const version = ref('T+1h')
const versions = ref({})
const quakeTime = ref('2025-03-28T14:20:52')
const loading = ref(false)
const currentBrief = ref(null)

const calibrations = {
  first_post: '首条涉震微博早于主震发震时刻1分46秒',
  magnitude: '震级双口径：CENC 7.9 / USGS Mw7.7',
  time: '主震发震时刻 2025-03-28 14:20:52',
  casualty: '死亡人数标注「持续更新中」'
}

async function loadVersions() {
  try {
    const res = await getBriefVersions()
    versions.value = res.data
  } catch (e) { console.error(e) }
}

async function generate() {
  loading.value = true
  try {
    const situationData = { quake_time: quakeTime.value }
    const res = await generateBrief(situationData, version.value)
    currentBrief.value = {
      content: res.data.content,
      generated_at: res.data.generated_at,
      situation_snapshot: res.data.situation_snapshot,
      changes_from_previous: res.data.changes_from_previous,
      ai_powered: !res.data.content?.includes('社媒感知数据自动生成'),
    }
    ElMessage.success('简报已生成')
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    loading.value = false
  }
}

function copyBrief() {
  if (!currentBrief.value?.content) return
  navigator.clipboard.writeText(currentBrief.value.content)
  ElMessage.success('已复制到剪贴板')
}

onMounted(() => {
  loadVersions()
})
</script>

<style scoped>
.brief-content { min-height: 400px; }
.brief-text {
  white-space: pre-wrap;
  font-family: 'SimSun', 'Songti SC', serif;
  font-size: 15px;
  line-height: 1.8;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}
.brief-loading { padding: 20px; }
.calibration-info h4 { margin-bottom: 8px; color: #e6a23c; }
.brief-snapshot h4 { margin: 8px 0; }
</style>
