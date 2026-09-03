<template>
  <button
    :class="[
      'btn',
      `btn-${variant}`,
      `btn-${size}`,
      { 'btn-loading': loading, 'btn-disabled': disabled }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <span v-if="loading" class="btn-spinner"></span>
    <el-icon v-if="icon && !loading" :size="iconSize"><component :is="icon" /></el-icon>
    <span v-if="$slots.default" class="btn-text">
      <slot></slot>
    </span>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'danger', 'ghost', 'icon'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(value)
  },
  icon: {
    type: [String, Object],
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const iconSize = computed(() => {
  const sizes = { xs: 12, sm: 14, md: 16, lg: 18, xl: 20 }
  return sizes[props.size]
})

const handleClick = (event) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>

<style scoped>
.btn {
  @apply inline-flex items-center justify-center gap-2 font-medium transition-all duration-base rounded-md;
  white-space: nowrap;
  user-select: none;
}

/* Sizes */
.btn-xs {
  @apply px-2 py-1 text-xs;
}

.btn-sm {
  @apply px-3 py-1.5 text-sm;
}

.btn-md {
  @apply px-4 py-2 text-sm;
}

.btn-lg {
  @apply px-5 py-2.5 text-base;
}

.btn-xl {
  @apply px-6 py-3 text-base;
}

/* Variants */
.btn-primary {
  @apply bg-primary text-white hover:bg-primary-hover active:bg-primary-active;
  box-shadow: var(--shadow-card);
}

.btn-primary:hover:not(:disabled) {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-1px);
}

.btn-secondary {
  @apply bg-white text-neutral-700 border border-neutral-300 hover:bg-neutral-50 hover:border-neutral-400;
}

.btn-danger {
  @apply bg-severity-critical text-white hover:bg-red-700 active:bg-red-800;
}

.btn-ghost {
  @apply bg-transparent text-neutral-600 hover:bg-neutral-100;
}

.btn-icon {
  @apply p-2 rounded-full;
  width: 40px;
  height: 40px;
}

/* States */
.btn-disabled {
  @apply opacity-50 cursor-not-allowed;
}

.btn-loading {
  @apply cursor-wait;
}

.btn-spinner {
  @apply w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin;
}

/* Icon spacing */
.btn :deep(.el-icon) {
  flex-shrink: 0;
}
</style>
