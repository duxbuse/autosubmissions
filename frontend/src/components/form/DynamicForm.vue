<template>
  <div v-for="question in filteredQuestions" :key="question.id" class="form-question">
    <label :for="question.id">{{ question.label }}</label>
    <input
      :id="question.id"
      v-model="formData[question.id]"
      @input="updateModelValue"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  questions: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(['update:modelValue']);

const formData = ref({ ...props.modelValue });

watch(() => props.modelValue, (newValue) => {
  formData.value = { ...newValue };
}, { deep: true });

const filteredQuestions = computed(() => {
  console.log('Re-evaluating filteredQuestions...');
  const visibleQuestions = props.questions.filter(question => {
    if (!question.showIf) {
      console.log(`Question '${question.label}' is visible by default.`);
      return true;
    }
    const dependency = question.showIf;
    const dependentValue = formData.value[dependency.questionId];
    const isVisible = dependentValue === dependency.value;
    console.log(`Checking dependency for '${question.label}': depends on '${dependency.questionId}' to be '${dependency.value}'. Current value: '${dependentValue}'. Visible: ${isVisible}`);
    return isVisible;
  });
  console.log('Visible questions:', visibleQuestions.map(q => q.label));
  return visibleQuestions;
});

const updateModelValue = () => {
  emit('update:modelValue', { ...formData.value });
};
</script>

<style scoped>
.form-question {
  margin-bottom: 1rem;
}
</style>