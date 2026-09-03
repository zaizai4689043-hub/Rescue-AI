<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="48" color="#38E1FF"><MapLocation /></el-icon>
        <h1 class="login-title">AI地震救援平台</h1>
        <p class="login-subtitle">智能地震灾害应急救援指挥系统</p>
      </div>

      <el-tabs v-model="activeTab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" size="large">
            <el-form-item prop="username">
              <el-input v-model="loginForm.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" style="width: 100%" :loading="loading" @click="handleLogin">登 录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" size="large">
            <el-form-item prop="username">
              <el-input v-model="registerForm.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="registerForm.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" :prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item prop="real_name">
              <el-input v-model="registerForm.real_name" placeholder="姓名" />
            </el-form-item>
            <el-form-item prop="phone">
              <el-input v-model="registerForm.phone" placeholder="手机号" />
            </el-form-item>
            <el-form-item prop="role">
              <el-select v-model="registerForm.role" placeholder="选择角色" style="width: 100%">
                <el-option v-for="r in USER_ROLES" :key="r.value" :label="r.label" :value="r.value" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-input v-model="registerForm.organization" placeholder="所属组织（可选）" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" style="width: 100%" :loading="loading" @click="handleRegister">注 册</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { USER_ROLES } from '../utils/constants'

const router = useRouter()
const userStore = useUserStore()
const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref(null)
const registerFormRef = ref(null)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({
  username: '', password: '', confirmPassword: '', real_name: '', phone: '', role: '', organization: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) callback(new Error('两次输入密码不一致'))
  else callback()
}

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 3, message: '用户名至少3个字符', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少6个字符', trigger: 'blur' }]
}

const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 3, message: '用户名至少3个字符', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少6个字符', trigger: 'blur' }],
  confirmPassword: [{ required: true, message: '请确认密码', trigger: 'blur' }, { validator: validateConfirmPassword, trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }, { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const handleLogin = async () => {
  await loginFormRef.value?.validate()
  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/command-center')
  } catch (e) {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  await registerFormRef.value?.validate()
  loading.value = true
  try {
    const { confirmPassword, ...registerData } = registerForm
    await userStore.register(registerData)
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
  } catch (e) {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background:
    radial-gradient(900px 500px at 80% -10%, rgba(56, 225, 255, 0.10), transparent 60%),
    radial-gradient(800px 600px at 10% 110%, rgba(167, 139, 250, 0.10), transparent 60%),
    var(--deck-bg);
}
.login-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(94, 160, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(94, 160, 255, 0.05) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse at 50% 40%, black 30%, transparent 78%);
  pointer-events: none;
}
.login-card {
  position: relative;
  width: 420px;
  background: var(--deck-panel);
  border: 1px solid var(--deck-border-strong);
  border-radius: 18px;
  padding: 40px 36px 24px;
  backdrop-filter: blur(18px);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.5), 0 0 40px rgba(56, 225, 255, 0.06);
}
.login-card::before {
  content: '';
  position: absolute;
  top: 0; left: 15%; right: 15%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(56, 225, 255, 0.5), transparent);
}
.login-header { text-align: center; margin-bottom: 24px; }
.login-title {
  margin: 12px 0 6px;
  font-size: 24px;
  font-family: var(--deck-font-display);
  letter-spacing: 0.08em;
  color: var(--deck-text);
}
.login-subtitle { font-size: 13px; color: var(--deck-text-3); margin: 0; letter-spacing: 0.1em; }
.login-page :deep(.el-tabs__item) {
  color: var(--deck-text-3);
  font-size: 15px;
}
.login-page :deep(.el-tabs__item.is-active) { color: var(--deck-cyan); }
.login-page :deep(.el-tabs__active-bar) { background-color: var(--deck-cyan); }
</style>
