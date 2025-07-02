
<template>
  <div>
    <label v-for="opt in options" :key="opt.id">
      <input
        type="radio"
        :name="id"
        :value="opt.text"
        :checked="modelValue === opt.text"
        @change="$emit('update:modelValue', opt.text)"
      />
      {{ opt.text }}
    </label>
  </div>
</template>

<script setup>
  defineProps(['modelValue', 'options', 'id']);
  defineEmits(['update:modelValue']);
</script>
