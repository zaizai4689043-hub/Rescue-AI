import request from './request'

export const getVolunteers = (params) => request.get('/volunteers/', { params })
export const createVolunteer = (data) => request.post('/volunteers/', data)
export const getVolunteer = (id) => request.get(`/volunteers/${id}`)
export const updateVolunteer = (id, data) => request.put(`/volunteers/${id}`, data)
export const assignVolunteer = (id, data) => request.patch(`/volunteers/${id}/assign`, data)
export const deleteVolunteer = (id) => request.delete(`/volunteers/${id}`)
export const matchVolunteers = (skills) => request.get('/volunteers/match', { params: { skills } })
export const getVolunteerStatistics = () => request.get('/volunteers/statistics')
