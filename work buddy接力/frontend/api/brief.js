/**
 * 灾情简报 API
 * 对应愿景 5
 */
import request from './request'

// 生成灾情简报
export function generateBrief(situationData, version = null) {
  return request.post('/brief/generate', {
    situation_data: situationData,
    version
  })
}

// 获取简报版本列表
export function getBriefVersions() {
  return request.get('/brief/versions')
}

// 快速预览简报
export function previewBrief(version = null, quakeTime = '2025-03-28T14:20:52') {
  return request.get('/brief/preview', {
    params: { version, quake_time: quakeTime }
  })
}
