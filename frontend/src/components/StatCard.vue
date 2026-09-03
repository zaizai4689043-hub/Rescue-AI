<template>
  <div class="stat-card deck-rise" :style="{ '--accent': color }">
    <div class="stat-card-inner">
      <div class="stat-left">
        <div class="stat-value deck-numeric">{{ value }}</div>
        <div class="stat-title">{{ title }}</div>
      </div>
      <div class="stat-icon">
        <el-icon :size="26">
          <component :is="icon" />
        </el-icon>
      </div>
    </div>
    <div class="stat-glow"></div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  icon: { type: String, default: 'DataLine' },
  color: { type: String, default: '#38E1FF' }
})
</script>

<style scoped>
.stat-card {
  position: relative;
  padding: 18px 20px;
  border-radius: 14px;
  background: var(--deck-panel);
  border: 1px solid var(--deck-border);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  overflow: hidden;
  transition: transform 0.3s, border-color 0.3s, box-shadow 0.3s;
  cursor: default;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 14%; right: 14%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(56, 225, 255, 0.35), transparent);
}
.stat-card:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--accent) 45%, transparent);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), 0 0 24px color-mix(in srgb, var(--accent) 18%, transparent);
}
.stat-card-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}
.stat-value {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--accent);
  text-shadow: 0 0 18px color-mix(in srgb, var(--accent) 45%, transparent);
}
.stat-title {
  font-size: 13px;
  color: var(--deck-text-2);
  margin-top: 6px;
  letter-spacing: 0.04em;
}
.stat-icon {
  width: 52px; height: 52px;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 13%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  box-shadow: inset 0 0 16px color-mix(in srgb, var(--accent) 12%, transparent);
}
.stat-glow {
  position: absolute;
  right: -30px; bottom: -40px;
  width: 120px; height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 16%, transparent), transparent 70%);
  pointer-events: none;
}
</style>
