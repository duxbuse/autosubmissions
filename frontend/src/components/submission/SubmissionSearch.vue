
<template>
  <div style="width: 320px; min-width: 220px; max-width: 400px;">
    <input
      :value="searchClient"
      @input="$emit('update:searchClient', $event.target.value)"
      @input.lazy="onSearchClient"
      placeholder="Search submissions by client name..."
      style="width: 100%; padding: 0.5rem; border-radius: 6px; border: 1px solid #ccc;"
    />
    <slot></slot>
  </div>
</template>

<script setup>
  defineProps(['searchClient', 'onSearchClient']);
  defineEmits(['update:searchClient']);
</script>
