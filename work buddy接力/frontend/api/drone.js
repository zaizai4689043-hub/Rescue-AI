/**
 * 无人机模块 API 封装
 * 对应无人机空中救援模块：机队管理 / 遥测 / 任务 / 巡逻仿真 / 物资投送 / 空中侦察
 */
import axios from 'axios'

const API = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// ---- 机队管理 ----

export const droneApi = {
  // 机队列表
  getFleet: () => API.get('/drone/fleet').then(r => r.data),

  // 机队状态汇总
  getFleetStatus: () => API.get('/drone/fleet/status').then(r => r.data),

  // 注册无人机
  register: (data) => API.post('/drone/fleet/register', data).then(r => r.data),

  // 初始化仿真机队
  initSimFleet: () => API.post('/drone/fleet/init-sim').then(r => r.data),

  // 遥测
  getTelemetry: (droneId) => API.get(`/drone/telemetry/${droneId}`).then(r => r.data),
  sendTelemetry: (frame) => API.post('/drone/telemetry', frame).then(r => r.data),

  // 任务
  assignMission: (droneId, data) => API.post('/drone/mission/assign', data, { params: { drone_id_str: droneId } }).then(r => r.data),
  getActiveMissions: () => API.get('/drone/missions').then(r => r.data),
  completeMission: (missionId, result) => API.post(`/drone/mission/${missionId}/complete`, result).then(r => r.data),
  abortMission: (missionId, reason) => API.post(`/drone/mission/${missionId}/abort`, null, { params: { reason } }).then(r => r.data),

  // 巡逻仿真
  createPatrol: (data) => API.post('/drone/patrol/create', data).then(r => r.data),
  startPatrol: (sim) => API.post('/drone/patrol/start', sim).then(r => r.data),
  stopPatrol: (sim) => API.post('/drone/patrol/stop', sim).then(r => r.data),
  stepPatrol: (data) => API.post('/drone/patrol/step', data).then(r => r.data),
}

// ---- 物资投送 ----

export const supplyApi = {
  createRequest: (hotspotId, customManifest) => API.post('/drone/supply/request', { hotspot_id: hotspotId, custom_manifest: customManifest }).then(r => r.data),
  planDelivery: (deliveryId, droneIdStr) => API.post('/drone/supply/plan', { delivery_id: deliveryId, drone_id_str: droneIdStr }).then(r => r.data),
  getQueue: () => API.get('/drone/supply/queue').then(r => r.data),
  getStats: () => API.get('/drone/supply/stats').then(r => r.data),
  getPackages: () => API.get('/drone/supply/packages').then(r => r.data),
  confirmDelivery: (deliveryId, data) => API.post(`/drone/supply/${deliveryId}/confirm`, data).then(r => r.data),
  aiPlan: (hotspotData, drones) => API.post('/drone/supply/ai-plan', hotspotData, { params: { available_drones: drones } }).then(r => r.data),
}

// ---- 空中侦察 ----

export const reconApi = {
  create: (data) => API.post('/drone/recon/create', data).then(r => r.data),
  getList: (areaName) => API.get('/drone/recon/list', { params: { area_name: areaName } }).then(r => r.data),
  getDetail: (reconId) => API.get(`/drone/recon/${reconId}`).then(r => r.data),
  uploadImage: (reconId, data) => API.post(`/drone/recon/${reconId}/upload`, data).then(r => r.data),
  analyzeRoute: (reconId, data) => API.post(`/drone/recon/${reconId}/analyze`, data).then(r => r.data),
  getRouteSummary: () => API.get('/drone/recon/routes/summary').then(r => r.data),
}
