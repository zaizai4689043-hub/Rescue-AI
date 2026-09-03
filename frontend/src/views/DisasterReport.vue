<template>
  <div class="page-container">
    <h2 class="page-title">灾情上报</h2>
    <el-card style="margin-top: 20px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" label-position="right">
        <el-form-item label="灾情标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入灾情标题" />
        </el-form-item>
        <el-form-item label="灾情类型" prop="disaster_type">
          <el-select v-model="form.disaster_type" placeholder="请选择灾情类型" style="width: 100%">
            <el-option v-for="t in DISASTER_TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="灾情等级">
          <el-select v-model="form.disaster_level" clearable placeholder="请选择灾情等级" style="width: 100%">
            <el-option v-for="l in DISASTER_LEVELS" :key="l.value" :label="l.label" :value="l.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度" prop="severity">
          <el-rate v-model="form.severity" :max="5" show-text :texts="['轻微','一般','较重','严重','极其严重']" />
        </el-form-item>
        <el-form-item label="预估被困人数">
          <el-input-number v-model="form.estimated_people_trapped" :min="0" placeholder="预估被困人数" style="width: 100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="预估经济损失">
          <el-input-number v-model="form.estimated_economic_loss" :min="0" :precision="2" placeholder="万元" style="width: 100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="救援请求">
          <el-select v-model="form.is_rescue_requested" style="width: 100%">
            <el-option v-for="opt in RESCUE_REQUEST_OPTIONS" :key="String(opt.value)" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="详细描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请详细描述灾情情况" />
        </el-form-item>
        <el-form-item label="位置信息">
          <el-row :gutter="20" style="width: 100%">
            <el-col :span="12">
              <el-input-number v-model="form.latitude" :min="-90" :max="90" :step="0.0001" :precision="4" placeholder="纬度" style="width: 100%" controls-position="right" />
              <div style="font-size: 12px; color: var(--deck-text-3); margin-top: 4px">纬度 (-90 ~ 90)</div>
            </el-col>
            <el-col :span="12">
              <el-input-number v-model="form.longitude" :min="-180" :max="180" :step="0.0001" :precision="4" placeholder="经度" style="width: 100%" controls-position="right" />
              <div style="font-size: 12px; color: var(--deck-text-3); margin-top: 4px">经度 (-180 ~ 180)</div>
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="地址描述">
          <el-input v-model="form.address" placeholder="请输入详细地址" />
        </el-form-item>
        <el-form-item label="图片上传">
          <el-upload action="#" :auto-upload="false" list-type="picture-card" :on-change="handleFileChange">
            <el-icon :size="24"><Plus /></el-icon>
          </el-upload>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">提 交</el-button>
          <el-button @click="handleReset">重 置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createDisaster } from '../api/disaster'
import { DISASTER_TYPES, DISASTER_LEVELS, RESCUE_REQUEST_OPTIONS } from '../utils/constants'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)

const form = reactive({
  title: '', disaster_type: '', severity: 0, disaster_level: '',
  is_rescue_requested: false,
  estimated_people_trapped: null, estimated_economic_loss: null,
  description: '',
  latitude: null, longitude: null, address: '', images: []
})

const rules = {
  title: [{ required: true, message: '请输入灾情标题', trigger: 'blur' }],
  disaster_type: [{ required: true, message: '请选择灾情类型', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }],
  description: [{ required: true, message: '请输入详细描述', trigger: 'blur' }]
}

const handleFileChange = (file, fileList) => { form.images = fileList }

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    await createDisaster({
      title: form.title,
      disaster_type: form.disaster_type,
      severity: form.severity,
      disaster_level: form.disaster_level || undefined,
      estimated_people_trapped: form.estimated_people_trapped ?? undefined,
      estimated_economic_loss: form.estimated_economic_loss ?? undefined,
      is_rescue_requested: form.is_rescue_requested,
      description: form.description,
      latitude: form.latitude,
      longitude: form.longitude,
      address: form.address
    })
    ElMessage.success('灾情上报成功')
    router.push('/disaster-list')
  } catch (e) {
    // handled by interceptor
  } finally {
    submitting.value = false
  }
}

const handleReset = () => { formRef.value?.resetFields() }
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
