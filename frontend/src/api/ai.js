import request from './request'

export const analyzeDisaster = (disasterId) =>
  request.post('/ai-analysis/analyze', { disaster_id: disasterId })

export const getAiAnalysis = (disasterId) =>
  request.get(`/ai-analysis/${disasterId}`)

export const chatWithAi = (message) =>
  request.post('/ai-assistant/chat', { message })

/** 参谋研判：双方案 + 三维可信度。DashScope 上游超时25s，显式放宽到35s避免前端先超时 */
export const getAiAdvisory = (payload) =>
  request.post('/ai-assistant/advisory', payload, { timeout: 35000 })

export const getMapData = (params) =>
  request.get('/map-data/', { params })

export const getMapHeatmap = () =>
  request.get('/map-data/heatmap')
