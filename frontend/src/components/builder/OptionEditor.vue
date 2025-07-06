
<template>
  <div class="option-block">
    <input :value="option.text" @input="updateOption('text', $event.target.value)" placeholder="Option text" />
    <div class="triggers-section">
      <label>Triggers questions:</label>
      <div class="checkbox-group">
        <label v-for="q in filteredQuestions" :key="q.id" :value="q.id">
          <input
            type="checkbox"
            :checked="option.triggers_question && option.triggers_question.includes(q.id)"
            @change="toggleTrigger(q.id)"
          />
          {{ q.text || 'Untitled Question' }}
        </label>
      </div>
    </div>
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

  const toggleTrigger = (questionId) => {
    const currentTriggers = props.option.triggers_question || [];
    const newTriggers = [...currentTriggers];
    const index = newTriggers.indexOf(questionId);

    if (index > -1) {
      newTriggers.splice(index, 1);
    } else {
      newTriggers.push(questionId);
    }
    updateOption('triggers_question', newTriggers);
  };

  const filteredQuestions = computed(() => {
    return props.questions.filter((q, index) => index !== props.questionIndex);
  });
</script>

<style scoped>
.checkbox-group {
  max-height: 100px;
  overflow-y: auto;
  border: 1px solid #ccc;
  padding: 0.5em;
  border-radius: 4px;
  margin-top: 0.5em;
}
.checkbox-group label {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.triggers-section {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}
</style>
