
<template>
  <select :id="id" :value="modelValue" @change="$emit('update:modelValue', $event.target.value)">
    <option value="">-- Select --</option>
    <option v-for="opt in options" :key="opt.id" :value="opt.text">{{ opt.text }}</option>
  </select>
</template>

<script setup>
  defineProps(['modelValue', 'options', 'id']);
  defineEmits(['update:modelValue']);
</script>
