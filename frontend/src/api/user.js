import request from './request'

export const getUsers = (params) => request.get('/users/', { params })
export const updateUserRole = (id, role) => request.put(`/users/${id}/role`, { role })
export const toggleUserActive = (id) => request.patch(`/users/${id}/toggle-active`)
