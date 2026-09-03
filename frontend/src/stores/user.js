import { defineStore } from 'pinia'
import { login as loginApi, register as registerApi, getMe } from '../api/auth'
import router from '../router'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.userInfo?.username || '',
    userRole: (state) => state.userInfo?.role || ''
  },

  actions: {
    async login(username, password) {
      const res = await loginApi(username, password)
      this.token = res.data.access_token
      localStorage.setItem('token', this.token)
    },

    async register(data) {
      await registerApi(data)
    },

    async fetchUserInfo() {
      const res = await getMe()
      this.userInfo = res.data
    },

    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
      router.push('/login')
    }
  }
})
