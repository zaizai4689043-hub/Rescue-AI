<template>
  <span :class="['tag', `tag-${variant}`, { 'tag-closable': closable }]">
    <el-icon v-if="icon" :size="12"><component :is="icon" /></el-icon>
    <span class="tag-text"><slot></slot></span>
    <el-icon v-if="closable" class="tag-close" @click.stop="handleClose"><Close /></el-icon>
  </span>
</template>

<script setup>
import { Close } from '@element-plus/icons-vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'primary', 'success', 'warning', 'danger', 'info', 'critical', 'high', 'medium', 'low', 'minimal'].includes(value)
  },
  icon: {
    type: [String, Object],
    default: null
  },
  closable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
.tag {
  @apply inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium;
  white-space: nowrap;
}

/* Variants */
.tag-default {
  @apply bg-neutral-100 text-neutral-700;
}

.tag-primary {
  @apply bg-blue-100 text-primary;
}

.tag-success {
  @apply bg-green-100 text-severity-minimal;
}

.tag-warning {
  @apply bg-yellow-100 text-severity-medium;
}

.tag-danger {
  @apply bg-red-100 text-severity-critical;
}

.tag-info {
  @apply bg-neutral-100 text-neutral-600;
}

/* Severity Tags */
.tag-critical {
  @apply bg-red-100 text-severity-critical;
}

.tag-high {
  @apply bg-orange-100 text-severity-high;
}

.tag-medium {
  @apply bg-yellow-100 text-severity-medium;
}

.tag-low {
  @apply bg-blue-100 text-severity-low;
}

.tag-minimal {
  @apply bg-green-100 text-severity-minimal;
}

/* Closable */
.tag-closable {
  @apply pr-1;
}

.tag-close {
  @apply cursor-pointer hover:bg-black/10 rounded-full p-0.5 transition-colors;
}

/* Icon */
.tag :deep(.el-icon) {
  flex-shrink: 0;
}
</style>
