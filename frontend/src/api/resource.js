import request from './request'

export const getResources = (params) => request.get('/resources/', { params })
export const createResource = (data) => request.post('/resources/', data)
export const getResource = (id) => request.get(`/resources/${id}`)
export const updateResource = (id, data) => request.put(`/resources/${id}`, data)
export const dispatchResource = (id, data) => request.patch(`/resources/${id}/dispatch`, data)
export const deleteResource = (id) => request.delete(`/resources/${id}`)
export const getResourceStatistics = () => request.get('/resources/statistics')
