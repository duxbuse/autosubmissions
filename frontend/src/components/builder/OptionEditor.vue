
<template>
  <div class="option-block">
    <input :value="option.text" @input="updateOption('text', $event.target.value)" placeholder="Option text" />
    <label>
      Triggers questions:
      <select multiple :value="option.triggers_question" @change="updateOption('triggers_question', Array.from($event.target.selectedOptions).map(o => o.value))" style="min-width: 120px;">
        <option v-for="q in filteredQuestions" :key="q.id" :value="q.id">
          {{ q.text }}
        </option>
      </select>
    </label>
    <button @click="$emit('remove')">Delete Option</button>
    <span v-if="validationError" class="error">{{ validationError }}</span>
  </div>
</template>

<script setup>
  import { computed } from 'vue';

  const props = defineProps(['option', 'questions', 'questionIndex', 'optionIndex', 'validationError']);
  const emit = defineEmits(['update:option', 'remove']);

  const updateOption = (key, value) => {
    emit('update:option', { ...props.option, [key]: value });
  };

  const filteredQuestions = computed(() => {
    return props.questions.filter((q, index) => index !== props.questionIndex);
  });
</script>
