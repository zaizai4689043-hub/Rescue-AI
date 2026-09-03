import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000
})

request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

request.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else {
      const data = error.response?.data
      let msg = '请求失败'
      if (data?.detail) {
        msg = typeof data.detail === 'string' ? data.detail : (Array.isArray(data.detail) ? data.detail.map(e => e.msg).join('; ') : '请求失败')
      } else if (error.message) {
        msg = error.message
      }
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default request
