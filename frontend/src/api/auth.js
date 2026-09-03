import request from './request'

export const login = (username, password) => request.post('/login', { username, password })
export const register = (data) => request.post('/register', data)
export const getMe = () => request.get('/me')
