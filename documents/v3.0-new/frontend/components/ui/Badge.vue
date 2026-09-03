<template>
  <span :class="['badge', `badge-${variant}`, { 'badge-dot': dot }]">
    <slot v-if="!dot"></slot>
  </span>
</template>

<script setup>
const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'success', 'warning', 'danger', 'info'].includes(value)
  },
  dot: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.badge {
  @apply inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-xs font-bold text-white;
}

.badge-dot {
  @apply w-2.5 h-2.5 min-w-0 p-0;
}

/* Variants */
.badge-primary {
  @apply bg-primary;
}

.badge-success {
  @apply bg-severity-minimal;
}

.badge-warning {
  @apply bg-severity-medium;
}

.badge-danger {
  @apply bg-severity-critical;
}

.badge-info {
  @apply bg-neutral-500;
}
</style>
