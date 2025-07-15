<template>
  <div class="form-meta">
    <label>
      <span>Form Name:</span>
      <input v-model="localForm.name" @input="emitUpdate" placeholder="Form name" />
    </label>
    <span v-if="validationErrors.form.name" class="error">{{ validationErrors.form.name }}</span>

    <label>
      <span>Description:</span>
      <textarea v-model="localForm.description" @input="emitUpdate" placeholder="Form description"></textarea>
    </label>

    <label>
      <span>Template Type:</span>
      <select v-model="localForm.template_type" @change="emitUpdate">
        <option value="plea_of_guilty">Plea of Guilty</option>
        <option value="bail_application">Bail Application</option>
      </select>
    </label>
    <span v-if="validationErrors.form.template_type" class="error">{{ validationErrors.form.template_type }}</span>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';
const props = defineProps(['form', 'validationErrors']);
const emit = defineEmits(['update:form']);

const localForm = reactive({
  name: props.form.name ?? '',
  description: props.form.description ?? '',
  template_type: props.form.template_type ?? 'plea_of_guilty'
});

watch(() => props.form, (newForm) => {
  localForm.name = newForm.name ?? '';
  localForm.description = newForm.description ?? '';
  localForm.template_type = newForm.template_type ?? 'plea_of_guilty';
}, { deep: true });

function emitUpdate() {
  emit('update:form', { ...localForm });
}
</script>

<style scoped>
.form-meta {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

span {
  font-weight: 500;
}

input, textarea, select {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

textarea {
  min-height: 100px;
  resize: vertical;
}

.error {
  color: red;
  font-size: 0.875rem;
}
</style>
