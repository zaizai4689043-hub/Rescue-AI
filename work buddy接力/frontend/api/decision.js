/**
 * AI 决策助手 API
 * 对应愿景 6
 */
import request from './request'

// AI 决策分析
export function analyzeDecision(params) {
  return request.post('/decision/analyze', {
    situation_data: params.situationData || {},
    epicenter: params.epicenter || [95.94, 22.01],
    magnitude: params.magnitude || 7.7,
    depth_km: params.depthKm || 10.0
  })
}

// 获取案例知识库列表
export function getCases() {
  return request.get('/decision/cases')
}

// 获取案例详情
export function getCaseDetail(caseId) {
  return request.get(`/decision/cases/${caseId}`)
}

// 同步案例到数据库
export function syncCases() {
  return request.post('/decision/cases/sync')
}

// 案例匹配
export function matchCases(params) {
  return request.post('/decision/match', null, { params })
}
