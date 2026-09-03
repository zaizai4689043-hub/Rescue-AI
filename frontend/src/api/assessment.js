import request from './request'

export const getAssessments = (params) => request.get('/assessments/', { params })
export const createAssessment = (data) => request.post('/assessments/', data)
export const getAssessment = (id) => request.get(`/assessments/${id}`)
export const updateAssessment = (id, data) => request.put(`/assessments/${id}`, data)
export const deleteAssessment = (id) => request.delete(`/assessments/${id}`)
