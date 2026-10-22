<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  title: string;
  status: 'active' | 'idle' | 'warning';
}>();

const emit = defineEmits<{
  (e: 'refresh'): void;
}>();

const isExpanded = ref(false);
</script>

<template>
  <article class="vue-card">
    <header class="card-header">
      <h3>{{ title }}</h3>
      <span :class="['badge', status]">{{ status }}</span>
    </header>
    <button type="button" class="btn" @click="emit('refresh')">
      Refresh Node
    </button>
  </article>
</template>

<style scoped>
.vue-card {
  background: var(--card, #1e293b);
  border: 1px solid var(--border, #334155);
  border-radius: var(--radius-md, 8px);
  padding: 1.5rem;
  color: var(--foreground, #f8fafc);
}
.badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}
.active { background: #16a34a; color: #fff; }
.btn {
  margin-top: 1rem;
  min-height: 44px;
  background: var(--primary, #6366f1);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
</style>
