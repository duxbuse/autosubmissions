
<template>
  <textarea :id="id" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)"></textarea>
</template>

<script setup>
  defineProps(['modelValue', 'id']);
  defineEmits(['update:modelValue']);
</script>
