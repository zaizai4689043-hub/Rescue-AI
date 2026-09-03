import request from './request'

export const getDisasters = (params) => request.get('/disasters/', { params })
export const createDisaster = (data) => request.post('/disasters/', data)
export const getDisaster = (id) => request.get(`/disasters/${id}`)
export const updateDisaster = (id, data) => request.put(`/disasters/${id}`, data)
export const updateDisasterStatus = (id, status) => request.patch(`/disasters/${id}/status`, { status })
export const deleteDisaster = (id) => request.delete(`/disasters/${id}`)
export const getDisasterStatistics = () => request.get('/disasters/statistics')
