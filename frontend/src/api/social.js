import request from './request'

/** 获取社情帖列表（分页 + 过滤） */
export const getSocialPosts = (params) =>
  request.get('/social/posts', { params })

/** 社情地理热力聚合 */
export const getSocialHeatmap = (params) =>
  request.get('/social/heatmap', { params })
