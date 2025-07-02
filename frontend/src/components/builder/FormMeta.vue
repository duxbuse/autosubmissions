
<template>
  <div class="form-meta">
    <label>
      <span>Form Name:</span>
      <input :value="form.name" @input="$emit('update:form', { ...form, name: $event.target.value })" placeholder="Form name" />
    </label>
    <span v-if="validationErrors.form.name" class="error">{{ validationErrors.form.name }}</span>
    <label>
      <span>Description:</span>
      <textarea :value="form.description" @input="$emit('update:form', { ...form, description: $event.target.value })" placeholder="Form description"></textarea>
    </label>
  </div>
</template>

<script setup>
  defineProps(['form', 'validationErrors']);
  defineEmits(['update:form']);
</script>
