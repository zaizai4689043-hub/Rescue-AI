import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  // 指挥大屏：顶层路由，绕过 MainLayout（自带 chrome），鉴权守卫自动生效
  {
    path: '/command-screen',
    name: 'CommandScreen',
    component: () => import('../views/CommandScreen.vue'),
    meta: { title: '指挥大屏' }
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/command-center',
    children: [
      // 🚨 应急指挥模块 (Command Center)
      {
        path: 'command-center',
        name: 'CommandCenter',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '指挥大屏', module: 'command' }
      },
      {
        path: 'disaster-report',
        name: 'DisasterReport',
        component: () => import('../views/DisasterReport.vue'),
        meta: { title: '灾情上报', module: 'command', parent: 'CommandCenter' }
      },
      {
        path: 'disaster-list',
        name: 'DisasterList',
        component: () => import('../views/DisasterList.vue'),
        meta: { title: '灾情管理', module: 'command', parent: 'CommandCenter' }
      },
      {
        path: 'assessment-report',
        name: 'AssessmentReport',
        component: () => import('../views/AssessmentReport.vue'),
        meta: { title: '数据分析', module: 'command', parent: 'CommandCenter' }
      },
      {
        path: 'user-manage',
        name: 'UserManage',
        component: () => import('../views/UserManage.vue'),
        meta: { title: '系统设置', module: 'command', parent: 'CommandCenter' }
      },

      // 🗺️ 态势地图模块 (Situation Map)
      {
        path: 'situation-map',
        name: 'SituationMap',
        component: () => import('../views/DisasterMap.vue'),
        meta: { title: '态势地图', module: 'map' }
      },

      // 📦 资源中心模块 (Resource Center)
      {
        path: 'resource-center',
        name: 'ResourceCenter',
        component: () => import('../views/ResourceCenter.vue'),
        meta: { title: '资源中心', module: 'resource' }
      },

      // 👥 人员管理模块 (Personnel Management)
      {
        path: 'personnel',
        name: 'PersonnelManagement',
        redirect: '/personnel/trapped',
        meta: { title: '人员管理', module: 'personnel' }
      },
      {
        path: 'personnel/trapped',
        name: 'TrappedPersons',
        component: () => import('../views/TrackedPersons.vue'),
        meta: { title: '受困者追踪', module: 'personnel', parent: 'PersonnelManagement' }
      },
      {
        path: 'personnel/volunteers',
        name: 'VolunteerManage',
        component: () => import('../views/VolunteerManage.vue'),
        meta: { title: '志愿者管理', module: 'personnel', parent: 'PersonnelManagement' }
      },

      // 🤖 AI助手模块 (AI Assistant)
      {
        path: 'ai-assistant',
        name: 'AIAssistant',
        component: () => import('../views/AIAssistant.vue'),
        meta: { title: 'AI助手', module: 'ai' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path === '/login') {
    token ? next('/command-center') : next()
  } else if (to.meta.requiresAuth === false) {
    next()
  } else {
    token ? next() : next('/login')
  }
})

export default router
