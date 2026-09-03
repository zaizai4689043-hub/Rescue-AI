<template>
  <div :class="['card', cardType, { 'card-hover': hover }]">
    <!-- AI Card Decoration Bar -->
    <div v-if="type === 'ai'" class="card-decoration"></div>

    <!-- Stat Card Left Border -->
    <div v-if="type === 'stat'" :class="['card-border', `border-${borderColor}`]"></div>

    <div class="card-content">
      <!-- Header -->
      <div v-if="title || $slots.header" class="card-header">
        <slot name="header">
          <div class="card-title-wrapper">
            <el-icon v-if="icon" :size="20" :color="iconColor"><component :is="icon" /></el-icon>
            <h3 class="card-title">{{ title }}</h3>
          </div>
          <div v-if="$slots.actions" class="card-actions">
            <slot name="actions"></slot>
          </div>
        </slot>
      </div>

      <!-- Body -->
      <div class="card-body">
        <slot></slot>
      </div>

      <!-- Footer -->
      <div v-if="$slots.footer" class="card-footer">
        <slot name="footer"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'stat', 'ai'].includes(value)
  },
  title: {
    type: String,
    default: ''
  },
  icon: {
    type: [String, Object],
    default: null
  },
  iconColor: {
    type: String,
    default: '#2563EB'
  },
  borderColor: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'accent', 'critical', 'high', 'medium', 'low', 'minimal'].includes(value)
  },
  hover: {
    type: Boolean,
    default: true
  }
})

const cardType = computed(() => {
  return `card-${props.type}`
})
</script>

<style scoped>
.card {
  @apply bg-white rounded-lg relative overflow-hidden;
  box-shadow: var(--shadow-card);
  transition: all var(--transition-base);
}

.card-hover:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

/* Default Card */
.card-default {
  @apply p-5;
}

/* Stat Card */
.card-stat {
  @apply pl-7 pr-5 py-5;
}

.card-border {
  @apply absolute left-0 top-0 bottom-0 w-1;
}

.border-primary { @apply bg-primary; }
.border-secondary { @apply bg-secondary; }
.border-accent { @apply bg-accent; }
.border-critical { @apply bg-severity-critical; }
.border-high { @apply bg-severity-high; }
.border-medium { @apply bg-severity-medium; }
.border-low { @apply bg-severity-low; }
.border-minimal { @apply bg-severity-minimal; }

/* AI Card */
.card-ai {
  @apply p-5;
  background: linear-gradient(135deg, #FFFFFF 0%, #EDE9FE 100%);
}

.card-decoration {
  @apply absolute top-0 left-0 right-0 h-1;
  background: linear-gradient(90deg, #7C3AED 0%, #2563EB 100%);
}

/* Content Structure */
.card-content {
  @apply h-full flex flex-col;
}

.card-header {
  @apply flex items-start justify-between mb-4;
}

.card-title-wrapper {
  @apply flex items-center gap-3;
}

.card-title {
  @apply text-lg font-semibold text-neutral-800 m-0;
}

.card-actions {
  @apply flex items-center gap-2;
}

.card-body {
  @apply flex-1;
}

.card-footer {
  @apply mt-4 pt-4 border-t border-neutral-200;
}

/* Dark Mode Support */
.dark .card {
  @apply bg-neutral-800;
}

.dark .card-title {
  @apply text-neutral-100;
}

.dark .card-ai {
  background: linear-gradient(135deg, #1F2937 0%, #312E81 100%);
}
</style>
