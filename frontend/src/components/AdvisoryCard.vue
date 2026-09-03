<script setup>
/**
 * 参谋研判卡片：渲染 /ai-assistant/advisory 返回的 {plans, credibility, provider}。
 * DecisionDesk 与 AIAssistant 共用。
 */
defineProps({
  advisory: { type: Object, required: true },
  compact: { type: Boolean, default: false },
})

const credBars = (credibility) => [
  { label: '时效性', value: credibility?.timeliness ?? 0, color: '#38E1FF' },
  { label: '定位精度', value: credibility?.location_accuracy ?? 0, color: '#A78BFA' },
  { label: '交叉验证', value: credibility?.cross_validation ?? 0, color: '#FFB020' },
]
</script>

<template>
  <div class="advisory-card">
    <div class="advisory-head">
      <span class="advisory-title">🧠 参谋研判</span>
      <span class="advisory-provider" :class="advisory.provider">
        {{ advisory.provider === 'qwen' ? '● Qwen实时' : '● 规则引擎' }}
      </span>
    </div>

    <div class="advisory-plans">
      <div
        v-for="plan in advisory.plans"
        :key="plan.label"
        class="plan-box"
        :class="{ recommended: plan.recommended }"
      >
        <div class="plan-title">
          {{ plan.label }}
          <span v-if="plan.recommended" class="rec-tag">推荐</span>
        </div>
        <div class="plan-name">{{ plan.title }}</div>
        <div class="plan-evidence">
          <div v-for="(ev, i) in plan.evidence" :key="i">• {{ ev }}</div>
        </div>
      </div>
    </div>

    <div class="advisory-cred">
      <div class="cred-title">可信度拆解</div>
      <div v-for="bar in credBars(advisory.credibility)" :key="bar.label" class="cred-row">
        <span class="cred-label">{{ bar.label }}</span>
        <div class="cred-bg">
          <div class="cred-fill" :style="{ width: bar.value + '%', background: bar.color }"></div>
        </div>
        <span class="cred-val deck-mono">{{ bar.value }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.advisory-card {
  background: var(--deck-bg-2);
  border: 1px solid var(--deck-border);
  border-radius: 8px;
  padding: 14px;
}
.advisory-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.advisory-title { font-weight: 600; color: var(--deck-text); font-size: 14px; }
.advisory-provider { font-size: 11px; font-weight: 600; }
.advisory-provider.qwen { color: var(--deck-teal); }
.advisory-provider.rules { color: var(--deck-amber); }
.advisory-provider.fallback { color: var(--deck-text-3); }
.advisory-plans { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }
.plan-box {
  background: var(--deck-panel-solid);
  border: 1px solid var(--deck-border);
  border-radius: 6px;
  padding: 10px;
}
.plan-box.recommended { border-color: rgba(45, 212, 191, 0.35); }
.plan-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--deck-text);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.rec-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 2px;
  background: rgba(45, 212, 191, 0.15);
  color: var(--deck-teal);
}
.plan-name { font-size: 13px; color: var(--deck-cyan); margin-bottom: 6px; }
.plan-evidence {
  font-size: 11px;
  color: var(--deck-text-3);
  line-height: 1.6;
  padding-left: 10px;
  border-left: 2px solid var(--deck-border);
}
.cred-title { font-size: 11px; color: var(--deck-text-3); letter-spacing: 1px; margin-bottom: 8px; }
.cred-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.cred-label { font-size: 11px; color: var(--deck-text-3); width: 60px; text-align: right; }
.cred-bg { flex: 1; height: 6px; background: var(--deck-panel-solid); border-radius: 3px; overflow: hidden; }
.cred-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }
.cred-val { font-size: 11px; color: var(--deck-text-2); width: 26px; }
</style>
