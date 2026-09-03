import { computed, unref } from 'vue'

/**
 * SLA 倒计时 composable（纯函数式，无内部定时器）。
 * 由调用方的响应式心跳驱动（如 store.tick()），多处复用。
 *
 * @param {import('vue').Ref<number>|()=>number} remainRef 剩余秒数（响应式）
 * @param {number} total 总窗口秒数，用于计算紧急阈值（<20%）
 */
export function useCountdown(remainRef, total) {
  const remain = computed(() => Math.max(0, Math.floor(unref(remainRef))))

  const text = computed(() => {
    const s = remain.value
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  })

  const urgent = computed(() => {
    const totalVal = unref(total)
    return totalVal > 0 && remain.value < totalVal * 0.2
  })
  const expired = computed(() => remain.value <= 0)

  return { remain, text, urgent, expired }
}
