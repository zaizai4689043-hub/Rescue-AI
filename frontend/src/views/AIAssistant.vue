<template>
  <div class="ai-page">
    <div class="ai-header deck-rise">
      <div class="ai-orb-wrap">
        <div class="ai-orb">
          <div class="orb-ring"></div>
          <div class="orb-ring r2"></div>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
            <path d="M12 2l1.9 5.7L20 9.5l-5.6 2.3L12 18l-2.4-6.2L4 9.5l6.1-1.8L12 2z" fill="url(#aig)"/>
            <defs>
              <linearGradient id="aig" x1="4" y1="2" x2="20" y2="18">
                <stop stop-color="#A78BFA"/><stop offset="1" stop-color="#38E1FF"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>
      <div class="ai-header-text">
        <h2>AI 救援决策助手</h2>
        <div class="ai-status">
          <span class="deck-live-dot"></span>
          <span class="ai-status-text">{{ sending ? '正在推理…' : '在线 · 多源数据已接入' }}</span>
        </div>
      </div>
      <div class="ai-caps deck-mono">
        <span class="cap">灾情分析</span>
        <span class="cap">资源调度</span>
        <span class="cap">路线规划</span>
      </div>
    </div>

    <div class="chat-container deck-panel deck-rise deck-rise-1">
      <!-- 消息列表 -->
      <div class="message-list" ref="messageList">
        <div v-for="(msg, idx) in messages" :key="idx" :class="['message-row', msg.role]">
          <div class="avatar">
            <div v-if="msg.role === 'ai'" class="ai-avatar">
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none">
                <path d="M12 2l1.9 5.7L20 9.5l-5.6 2.3L12 18l-2.4-6.2L4 9.5l6.1-1.8L12 2z" fill="#fff"/>
              </svg>
            </div>
            <span v-else class="user-avatar">{{ (userName || '我')[0] }}</span>
          </div>
          <div :class="['bubble', msg.role]">
            <AdvisoryCard v-if="msg.kind === 'advisory'" :advisory="msg.advisory" />
            <div v-else v-html="formatMessage(msg.content)"></div>
            <div class="msg-time deck-mono">{{ formatTime(msg.timestamp) }}</div>
          </div>
        </div>

        <div v-if="sending" class="message-row ai">
          <div class="avatar">
            <div class="ai-avatar">
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none">
                <path d="M12 2l1.9 5.7L20 9.5l-5.6 2.3L12 18l-2.4-6.2L4 9.5l6.1-1.8L12 2z" fill="#fff"/>
              </svg>
            </div>
          </div>
          <div class="bubble ai thinking">
            <span class="think-dot"></span>
            <span class="think-dot"></span>
            <span class="think-dot"></span>
          </div>
        </div>
      </div>

      <!-- 快捷问题 -->
      <div class="quick-actions">
        <button
          v-for="q in quickQuestions"
          :key="q"
          class="quick-chip"
          @click="sendQuick(q)"
        >{{ q }}</button>
      </div>

      <!-- 输入区 -->
      <div class="input-bar">
        <el-input
          v-model="inputText"
          placeholder="输入指令，例如：哪里最需要救援？"
          :maxlength="200"
          @keyup.enter="handleSend"
        />
        <button class="send-btn" :disabled="sending" @click="handleSend">
          <svg v-if="!sending" viewBox="0 0 24 24" width="15" height="15" fill="none">
            <path d="M3 11l18-8-8 18-2-8-8-2z" fill="currentColor"/>
          </svg>
          <span v-else class="send-spinner"></span>
          {{ sending ? '推理中' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { chatWithAi, getAiAdvisory } from '../api/ai'
import { getSocialPosts } from '../api/social'
import { useUserStore } from '../stores/user'
import AdvisoryCard from '../components/AdvisoryCard.vue'

const userStore = useUserStore()
const userName = computed(() => userStore.username || '我')

const messages = ref([
  {
    role: 'ai',
    content: '您好！我是AI地震救援助手，已接入灾情、资源与人员数据流。可以回答关于**灾情分析、资源调度、救援路线**等问题。请问有什么可以帮到您？',
    timestamp: new Date().toISOString(),
  },
])
const inputText = ref('')
const sending = ref(false)
const messageList = ref(null)

// 参谋研判指令：触发社情帖 → /ai-advisory → 双方案卡片
const ADVISORY_CMD = '研判最新高危社情'

const quickQuestions = [
  '哪里最需要救援？',
  '最近医疗点在哪？',
  '资源调度建议',
  '余震风险如何？',
  ADVISORY_CMD,
]

function formatTime(t) {
  return t ? new Date(t).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''
}

function formatMessage(text) {
  const keywords = ['优先救援', '优先派遣', '立即搜救', '全面疏散', '部分疏散', '注意安全防护']
  let result = text
  keywords.forEach(kw => {
    result = result.replace(new RegExp(kw, 'g'), `<span style="color:#FB4B6B;font-weight:700">${kw}</span>`)
  })
  result = result.replace(/\*\*(.+?)\*\*/g, '<strong style="color:#38E1FF">$1</strong>')
  return result
}

function scrollToBottom() {
  nextTick(() => {
    if (messageList.value) {
      messageList.value.scrollTop = messageList.value.scrollHeight
    }
  })
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', content: text, timestamp: new Date().toISOString() })
  inputText.value = ''
  sending.value = true
  scrollToBottom()

  if (text === ADVISORY_CMD) {
    await runAdvisory()
    return
  }

  try {
    const res = await chatWithAi(text)
    const data = res.data
    messages.value.push({
      role: 'ai',
      content: data.reply,
      timestamp: data.timestamp || new Date().toISOString(),
    })
  } catch {
    messages.value.push({
      role: 'ai',
      content: '抱歉，服务暂时不可用，请稍后重试。',
      timestamp: new Date().toISOString(),
    })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

/** 参谋研判：取最高危社情帖 → /ai-advisory → 双方案卡片 */
async function runAdvisory() {
  try {
    const postsRes = await getSocialPosts({ urgency_hint: 'high', page_size: 1 })
    const post = postsRes.data.items?.[0]
    if (!post) {
      messages.value.push({ role: 'ai', content: '当前暂无高危社情信号，无需研判。', timestamp: new Date().toISOString() })
      return
    }
    const advRes = await getAiAdvisory({
      text: post.text,
      signal_type: post.signal_type,
      geo_name: post.geo_name,
      latitude: post.latitude,
      longitude: post.longitude,
      confidence: post.confidence,
      urgency_hint: post.urgency_hint,
      sentiment: post.sentiment,
    })
    messages.value.push({
      role: 'ai',
      kind: 'advisory',
      advisory: advRes.data,
      content: '',
      timestamp: new Date().toISOString(),
    })
  } catch {
    messages.value.push({ role: 'ai', content: '研判服务暂时不可用，请稍后重试。', timestamp: new Date().toISOString() })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function sendQuick(q) {
  inputText.value = q
  handleSend()
}

onMounted(() => scrollToBottom())
</script>

<style scoped>
.ai-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 110px);
  position: relative;
  z-index: 1;
  gap: 16px;
}

/* ============ 头部：AI 核心 ============ */
.ai-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 20px;
  border-radius: 14px;
  background: linear-gradient(90deg, rgba(167, 139, 250, 0.1), rgba(56, 225, 255, 0.04));
  border: 1px solid rgba(167, 139, 250, 0.24);
  backdrop-filter: blur(14px);
}
.ai-orb-wrap { position: relative; }
.ai-orb {
  position: relative;
  width: 48px; height: 48px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, rgba(167, 139, 250, 0.5), rgba(56, 225, 255, 0.12) 70%);
  box-shadow: 0 0 26px rgba(167, 139, 250, 0.45), inset 0 0 14px rgba(167, 139, 250, 0.3);
}
.orb-ring {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 1px solid rgba(167, 139, 250, 0.4);
  animation: orbSpin 6s linear infinite;
}
.orb-ring::before {
  content: '';
  position: absolute;
  top: -2.5px; left: 50%;
  width: 5px; height: 5px;
  border-radius: 50%;
  background: #A78BFA;
  box-shadow: 0 0 8px #A78BFA;
}
.orb-ring.r2 {
  inset: -11px;
  border-color: rgba(56, 225, 255, 0.22);
  animation-duration: 9s;
  animation-direction: reverse;
}
.orb-ring.r2::before { background: #38E1FF; box-shadow: 0 0 8px #38E1FF; }
@keyframes orbSpin { to { transform: rotate(360deg); } }

.ai-header-text h2 {
  margin: 0;
  font-size: 19px;
  font-weight: 700;
  color: var(--deck-text);
  letter-spacing: 0.03em;
}
.ai-status {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 4px;
}
.ai-status-text { font-size: 12px; color: var(--deck-text-3); letter-spacing: 0.05em; }
.ai-caps { display: flex; gap: 8px; margin-left: auto; }
.cap {
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--deck-violet);
  border: 1px solid rgba(167, 139, 250, 0.3);
  background: rgba(167, 139, 250, 0.08);
  padding: 4px 10px;
  border-radius: 999px;
}

/* ============ 聊天容器 ============ */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 22px;
}
.message-row {
  display: flex;
  margin-bottom: 18px;
  gap: 12px;
  animation: deckRise 0.35s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.message-row.user { flex-direction: row-reverse; }
.avatar { flex-shrink: 0; }
.ai-avatar {
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #A78BFA, #38E1FF);
  box-shadow: 0 0 16px rgba(167, 139, 250, 0.5);
}
.user-avatar {
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--deck-font-display);
  font-weight: 700;
  font-size: 14px;
  color: #06121F;
  background: linear-gradient(135deg, #7CB8FF, #38E1FF);
  box-shadow: 0 0 14px rgba(56, 225, 255, 0.35);
}
.bubble {
  max-width: 65%;
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}
.bubble.ai {
  background: rgba(167, 139, 250, 0.07);
  color: var(--deck-text);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-top-left-radius: 4px;
}
.bubble.user {
  background: linear-gradient(135deg, rgba(56, 225, 255, 0.18), rgba(56, 225, 255, 0.08));
  color: #D9F6FF;
  border: 1px solid rgba(56, 225, 255, 0.3);
  border-top-right-radius: 4px;
}
.msg-time {
  font-size: 10px;
  color: var(--deck-text-3);
  margin-top: 6px;
  text-align: right;
}

/* 思考动画 */
.bubble.thinking {
  display: flex;
  gap: 5px;
  padding: 15px 18px;
}
.think-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--deck-violet);
  animation: thinkBlink 1.2s ease-in-out infinite;
}
.think-dot:nth-child(2) { animation-delay: 0.18s; }
.think-dot:nth-child(3) { animation-delay: 0.36s; }
@keyframes thinkBlink {
  0%, 100% { opacity: 0.25; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-3px); }
}

/* ============ 快捷问题 ============ */
.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 12px 20px;
  border-top: 1px solid var(--deck-border);
}
.quick-chip {
  font-size: 12.5px;
  color: var(--deck-text-2);
  background: rgba(120, 190, 255, 0.06);
  border: 1px solid var(--deck-border);
  border-radius: 999px;
  padding: 6px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.quick-chip:hover {
  color: var(--deck-violet);
  border-color: rgba(167, 139, 250, 0.5);
  background: rgba(167, 139, 250, 0.1);
  box-shadow: 0 0 14px rgba(167, 139, 250, 0.18);
  transform: translateY(-1px);
}

/* ============ 输入区 ============ */
.input-bar {
  display: flex;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--deck-border);
}
.input-bar :deep(.el-input__wrapper) {
  border-radius: 11px;
  padding: 4px 14px;
}
.send-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 22px;
  border: none;
  border-radius: 11px;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: #0A0714;
  background: linear-gradient(135deg, #A78BFA, #38E1FF);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 0 18px rgba(167, 139, 250, 0.35);
}
.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 24px rgba(167, 139, 250, 0.5);
}
.send-btn:disabled { opacity: 0.7; cursor: wait; }
.send-spinner {
  width: 13px; height: 13px;
  border-radius: 50%;
  border: 2px solid rgba(10, 7, 20, 0.3);
  border-top-color: #0A0714;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
