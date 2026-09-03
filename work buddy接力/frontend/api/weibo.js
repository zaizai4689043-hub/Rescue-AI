/**
 * 微博数据 API
 * 对应愿景 2
 */
import request from './request'

// 导入单条微博
export function ingestPost(data) {
  return request.post('/weibo/ingest', data)
}

// 批量导入微博
export function batchIngest(posts, epicenter = [95.94, 22.01]) {
  return request.post('/weibo/batch-ingest', { posts, epicenter })
}

// 查询微博列表
export function getPosts(params) {
  return request.get('/weibo/posts', { params })
}

// 数据漏斗统计
export function getFunnel() {
  return request.get('/weibo/funnel')
}

// 重建灾情热点
export function rebuildHotspots() {
  return request.post('/weibo/rebuild-hotspots')
}

// 刷新优先级
export function refreshPriority(generateReasons = true) {
  return request.post('/weibo/refresh-priority', null, {
    params: { generate_reasons: generateReasons }
  })
}
