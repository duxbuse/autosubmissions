
<template>
  <div v-if="!question.hidden || (question.hidden && isTriggered)" class="question-block">
    <label :for="'q_' + question.id">{{ question.text }}</label>
    <component
      :is="inputComponent"
      v-model="answer"
      :options="question.options"
      :id="'q_' + question.id"
    ></component>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import InputText from './input/InputText.vue';
import InputParagraph from './input/InputParagraph.vue';
import InputMc from './input/InputMc.vue';
import InputCheck from './input/InputCheck.vue';
import InputDrop from './input/InputDrop.vue';

const props = defineProps(['question', 'modelValue', 'isTriggered']);
const emit = defineEmits(['update:modelValue']);

const answer = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const components = {
  'input-text': InputText,
  'input-paragraph': InputParagraph,
  'input-mc': InputMc,
  'input-check': InputCheck,
  'input-drop': InputDrop,
};

const inputComponent = computed(() => {
  switch (props.question.question_type) {
    case 'TEXT':
      return components['input-text'];
    case 'PARAGRAPH':
      return components['input-paragraph'];
    case 'MC':
      return components['input-mc'];
    case 'CHECK':
      return components['input-check'];
    case 'DROP':
      return components['input-drop'];
    default:
      return components['input-text'];
  }
});

</script>
