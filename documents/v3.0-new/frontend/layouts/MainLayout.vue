<template>
  <div class="deck-shell">
    <div class="deck-ambient"></div>

    <aside class="deck-sidebar" :class="{ collapsed: isCollapse }">
      <div class="sidebar-logo">
        <div class="logo-mark">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
            <path d="M2 12h4l2.5-6 3 12 2.5-8 1.5 2H22" stroke="url(#lg)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="lg" x1="2" y1="12" x2="22" y2="12">
                <stop stop-color="#38E1FF"/><stop offset="1" stop-color="#A78BFA"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <transition name="fade-slide">
          <div v-show="!isCollapse" class="logo-text">
            <span class="logo-name">RESCUE·AI</span>
            <span class="logo-sub">地震救援指挥中心</span>
          </div>
        </transition>
      </div>

      <el-menu
        :default-active="currentModule"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="deck-menu"
        background-color="transparent"
        text-color="#93A6C4"
        active-text-color="#38E1FF"
      >
        <el-sub-menu index="command">
          <template #title>
            <el-icon><Odometer /></el-icon>
            <span>应急指挥</span>
          </template>
          <el-menu-item index="/command-center">
            <el-icon><DataBoard /></el-icon><span>指挥大屏</span>
          </el-menu-item>
          <el-menu-item index="/disaster-report">
            <el-icon><EditPen /></el-icon><span>灾情上报</span>
          </el-menu-item>
          <el-menu-item index="/disaster-list">
            <el-icon><List /></el-icon><span>灾情管理</span>
          </el-menu-item>
          <el-menu-item index="/assessment-report">
            <el-icon><DataAnalysis /></el-icon><span>数据分析</span>
          </el-menu-item>
          <el-menu-item index="/user-manage">
            <el-icon><Setting /></el-icon><span>系统设置</span>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/situation-map">
          <el-icon><MapLocation /></el-icon>
          <template #title>态势地图</template>
        </el-menu-item>

        <el-menu-item index="/resource-center">
          <el-icon><Box /></el-icon>
          <template #title>资源中心</template>
        </el-menu-item>

        <el-sub-menu index="personnel">
          <template #title>
            <el-icon><UserFilled /></el-icon>
            <span>人员管理</span>
          </template>
          <el-menu-item index="/personnel/trapped">
            <el-icon><Position /></el-icon><span>受困者追踪</span>
          </el-menu-item>
          <el-menu-item index="/personnel/volunteers">
            <el-icon><User /></el-icon><span>志愿者管理</span>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/ai-assistant" class="menu-ai">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>AI助手</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <div class="ai-core" :class="{ mini: isCollapse }">
          <div class="ai-core-ring"></div>
          <span class="ai-core-label">AI CORE</span>
          <span class="deck-live-dot"></span>
        </div>
      </div>
    </aside>

    <div class="deck-body">
      <header class="deck-header">
        <div class="header-left">
          <button class="collapse-btn" @click="isCollapse = !isCollapse">
            <el-icon :size="18"><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
          </button>
          <div class="page-indicator">
            <span class="page-module">{{ currentModuleLabel }}</span>
            <span class="page-sep">/</span>
            <span class="page-name">{{ currentPageTitle }}</span>
          </div>
        </div>

        <div class="header-right">
          <div class="live-status">
            <span class="deck-live-dot"></span>
            <span>LIVE</span>
          </div>
          <div class="header-clock deck-numeric">{{ currentTime }}</div>
          <el-dropdown @command="handleCommand">
            <div class="operator">
              <div class="operator-avatar">{{ (userStore.username || 'U')[0].toUpperCase() }}</div>
              <span class="operator-name">{{ userStore.username || '用户' }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="deck-main">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'

const route = useRoute()
const userStore = useUserStore()
const isCollapse = ref(false)
const currentTime = ref('')

const MODULE_LABELS = {
  command: '应急指挥',
  map: '态势地图',
  resource: '资源中心',
  personnel: '人员管理',
  ai: 'AI助手'
}

const currentModule = computed(() => route.meta.module || 'command')
const currentModuleLabel = computed(() => MODULE_LABELS[currentModule.value] || '应急指挥')
const currentPageTitle = computed(() => route.meta.title || '指挥大屏')

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.getFullYear() + '-' +
    String(now.getMonth() + 1).padStart(2, '0') + '-' +
    String(now.getDate()).padStart(2, '0') + ' ' +
    String(now.getHours()).padStart(2, '0') + ':' +
    String(now.getMinutes()).padStart(2, '0') + ':' +
    String(now.getSeconds()).padStart(2, '0')
}
updateTime()
setInterval(updateTime, 1000)

const handleCommand = (command) => {
  if (command === 'logout') userStore.logout()
}

onMounted(() => {
  if (userStore.isLoggedIn && !userStore.userInfo) {
    userStore.fetchUserInfo().catch(() => {})
  }
})
</script>

<style scoped>
.deck-shell {
  display: flex;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

/* ============ 侧边栏 ============ */
.deck-sidebar {
  position: relative;
  z-index: 10;
  width: 236px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(10, 18, 36, 0.92), rgba(6, 11, 22, 0.96));
  border-right: 1px solid var(--deck-border);
  transition: width 0.28s cubic-bezier(0.22, 1, 0.36, 1);
  flex-shrink: 0;
}
.deck-sidebar.collapsed { width: 68px; }

.sidebar-logo {
  height: 68px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  border-bottom: 1px solid var(--deck-border);
  overflow: hidden;
}
.logo-mark {
  width: 40px; height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  background: linear-gradient(135deg, rgba(56, 225, 255, 0.14), rgba(167, 139, 250, 0.14));
  border: 1px solid rgba(56, 225, 255, 0.28);
  box-shadow: 0 0 18px rgba(56, 225, 255, 0.22), inset 0 0 12px rgba(56, 225, 255, 0.06);
}
.logo-text { display: flex; flex-direction: column; white-space: nowrap; }
.logo-name {
  font-family: var(--deck-font-display);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.14em;
  background: linear-gradient(90deg, #38E1FF, #A78BFA);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.logo-sub { font-size: 10.5px; color: var(--deck-text-3); letter-spacing: 0.18em; margin-top: 1px; }

/* ============ 菜单 ============ */
.deck-menu {
  flex: 1;
  border-right: none;
  padding: 10px 8px;
  overflow-y: auto;
  overflow-x: hidden;
}
.deck-menu :deep(.el-menu-item),
.deck-menu :deep(.el-sub-menu__title) {
  height: 46px;
  line-height: 46px;
  margin: 3px 0;
  border-radius: 10px;
  transition: all 0.2s ease;
  font-size: 14px;
}
.deck-menu :deep(.el-menu-item:hover),
.deck-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(56, 225, 255, 0.07) !important;
  color: #D6E8FF !important;
}
.deck-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(56, 225, 255, 0.16), rgba(56, 225, 255, 0.04)) !important;
  color: var(--deck-cyan) !important;
  box-shadow: inset 0 0 0 1px rgba(56, 225, 255, 0.22), 0 0 16px rgba(56, 225, 255, 0.08);
  position: relative;
}
.deck-menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0; top: 20%; bottom: 20%;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--deck-cyan);
  box-shadow: 0 0 10px var(--deck-cyan);
}
.deck-menu :deep(.el-sub-menu .el-menu-item) {
  min-width: auto;
  background: transparent !important;
}
.deck-menu :deep(.menu-ai.is-active) {
  background: linear-gradient(90deg, rgba(167, 139, 250, 0.2), rgba(167, 139, 250, 0.05)) !important;
  box-shadow: inset 0 0 0 1px rgba(167, 139, 250, 0.3), 0 0 16px rgba(167, 139, 250, 0.1);
}
.deck-menu :deep(.menu-ai.is-active::before) {
  background: var(--deck-violet);
  box-shadow: 0 0 10px var(--deck-violet);
}

/* ============ 底部AI核心 ============ */
.sidebar-footer { padding: 12px; border-top: 1px solid var(--deck-border); }
.ai-core {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 10px;
  background: linear-gradient(90deg, rgba(167, 139, 250, 0.12), rgba(56, 225, 255, 0.08));
  border: 1px solid rgba(167, 139, 250, 0.22);
  overflow: hidden;
}
.ai-core::after {
  content: '';
  position: absolute;
  top: 0; bottom: 0;
  width: 32%;
  background: linear-gradient(90deg, transparent, rgba(167, 139, 250, 0.18), transparent);
  animation: deckScan 3.2s linear infinite;
}
.ai-core-label {
  font-family: var(--deck-font-display);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.22em;
  color: var(--deck-violet);
}
.ai-core.mini { justify-content: center; padding: 9px 6px; }
.ai-core.mini .ai-core-label { display: none; }

/* ============ 主体区 ============ */
.deck-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 5;
  min-width: 0;
}

.deck-header {
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(8, 14, 28, 0.6);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--deck-border);
}
.header-left { display: flex; align-items: center; gap: 16px; }
.collapse-btn {
  width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center;
  background: transparent;
  border: 1px solid var(--deck-border);
  border-radius: 9px;
  color: var(--deck-text-2);
  cursor: pointer;
  transition: all 0.2s;
}
.collapse-btn:hover {
  color: var(--deck-cyan);
  border-color: rgba(56, 225, 255, 0.4);
  box-shadow: 0 0 12px rgba(56, 225, 255, 0.15);
}

.page-indicator { display: flex; align-items: baseline; gap: 10px; }
.page-module {
  font-family: var(--deck-font-display);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.22em;
  color: var(--deck-cyan);
  text-transform: uppercase;
}
.page-sep { color: var(--deck-text-3); }
.page-name { font-size: 17px; font-weight: 600; color: var(--deck-text); }

.header-right { display: flex; align-items: center; gap: 18px; }
.live-status {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid rgba(45, 212, 191, 0.3);
  background: rgba(45, 212, 191, 0.08);
  font-family: var(--deck-font-display);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.2em;
  color: var(--deck-teal);
}
.header-clock {
  font-size: 14px;
  color: var(--deck-text-2);
  letter-spacing: 0.06em;
}
.operator {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 10px 4px 4px;
  border-radius: 999px;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.operator:hover {
  border-color: var(--deck-border);
  background: rgba(120, 190, 255, 0.05);
}
.operator-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--deck-font-display);
  font-weight: 700;
  font-size: 15px;
  color: #06121F;
  background: linear-gradient(135deg, #38E1FF, #7CB8FF);
  box-shadow: 0 0 14px rgba(56, 225, 255, 0.4);
}
.operator-name { font-size: 13px; color: var(--deck-text-2); }

.deck-main {
  flex: 1;
  overflow-y: auto;
  padding: 22px 24px;
}

/* ============ 过渡 ============ */
.fade-slide-enter-active, .fade-slide-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity: 0; transform: translateX(-6px); }

.page-fade-enter-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.page-fade-leave-active { transition: opacity 0.15s ease; }
.page-fade-enter-from { opacity: 0; transform: translateY(10px); }
.page-fade-leave-to { opacity: 0; }

@media (max-width: 1024px) {
  .header-clock { display: none; }
}
</style>
