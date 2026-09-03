/**
 * 分析仪表盘 API
 * 对应愿景 4
 */
import request from './request'

// 多维分析仪表盘
export function getDashboard() {
  return request.get('/analytics/dashboard')
}

// 损毁类型分布
export function getDamageTypes() {
  return request.get('/analytics/damage-types')
}

// 关键词频率排行
export function getKeywords(topN = 20) {
  return request.get('/analytics/keywords', { params: { top_n: topN } })
}

// 情感时间线
export function getSentimentTimeline(intervalMinutes = 30) {
  return request.get('/analytics/sentiment-timeline', {
    params: { interval_minutes: intervalMinutes }
  })
}

// 新兴关键词检测
export function getEmergingKeywords(threshold = 5) {
  return request.get('/analytics/emerging-keywords', {
    params: { threshold }
  })
}

// 呼救区域排行
export function getDistressAreas(topN = 10) {
  return request.get('/analytics/distress-areas', {
    params: { top_n: topN }
  })
}
