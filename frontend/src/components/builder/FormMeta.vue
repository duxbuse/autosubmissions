<template>
  <div class="form-meta">
    <label>
      <span>Form Name:</span>
      <input :value="localForm.name" @input="onNameInput" placeholder="Form name" />
    </label>
    <span v-if="validationErrors.form.name" class="error">{{ validationErrors.form.name }}</span>
    <label>
      <span>Description:</span>
      <textarea :value="localForm.description" @input="onDescriptionInput" placeholder="Form description"></textarea>
    </label>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';
const props = defineProps(['form', 'validationErrors']);
const emit = defineEmits(['update:form']);

const localForm = reactive({
  name: props.form.name,
  description: props.form.description
});

watch(() => props.form, (newForm) => {
  localForm.name = newForm.name;
  localForm.description = newForm.description;
});

function onNameInput(e) {
  localForm.name = e.target.value;
  emit('update:form', { ...localForm });
}
function onDescriptionInput(e) {
  localForm.description = e.target.value;
  emit('update:form', { ...localForm });
}
</script>
