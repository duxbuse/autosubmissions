<template>
  <input :id="id" type="date" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" />
</template>

<script setup>
  defineProps(['modelValue', 'id']);
  defineEmits(['update:modelValue']);
</script>
