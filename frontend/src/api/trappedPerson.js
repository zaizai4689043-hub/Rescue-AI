import request from './request'

export const getTrappedPersons = (params) => request.get('/trapped-persons/', { params })
export const createTrappedPerson = (data) => request.post('/trapped-persons/', data)
export const getTrappedPerson = (id) => request.get(`/trapped-persons/${id}`)
export const updateTrappedPerson = (id, data) => request.put(`/trapped-persons/${id}`, data)
export const rescueTrappedPerson = (id) => request.patch(`/trapped-persons/${id}/rescue`)
export const deleteTrappedPerson = (id) => request.delete(`/trapped-persons/${id}`)
export const getTrappedPersonStatistics = (params) => request.get('/trapped-persons/statistics', { params })
