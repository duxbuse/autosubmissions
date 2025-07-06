
<template>
  <div class="question-block" :data-question-idx="questionIndex">
    <div class="question-header">
      <span>Q{{ questionIndex + 1 }}</span>
      <button @click="$emit('remove')">Delete</button>
      <button @click="$emit('move', -1)" :disabled="questionIndex === 0">↑</button>
      <button @click="$emit('move', 1)" :disabled="questionIndex === questions.length - 1">↓</button>
    </div>
    <div style="display: flex; align-items: center; gap: 1rem;">
      <input :value="question.text" @input="updateQuestion('text', $event.target.value)" placeholder="Question text" style="flex:1;" />
      <label style="white-space:nowrap;">
        <input type="checkbox" :checked="question.hidden" @change="updateQuestion('hidden', $event.target.checked)" /> Hidden by default
      </label>
    </div>
    <span v-if="validationError && validationError.text" class="error">{{ validationError.text }}</span>
    <span v-if="validationError && validationError.hidden" class="error">{{ validationError.hidden }}</span>
    <select :value="question.question_type" @change="updateQuestion('question_type', $event.target.value)">
      <option value="TEXT">Text</option>
      <option value="DATE">Date</option>
      <option value="MC">Multiple Choice</option>
      <option value="CHECK">Checkboxes</option>
      <option value="DROP">Dropdown</option>
    </select>

    <label>
      <span>Output Template:</span>
      <textarea :value="question.output_template" @input="updateQuestion('output_template', $event.target.value)" placeholder="e.g. 'The answer is {{answer}}.'"></textarea>
    </label>

    <div v-if="['MC','CHECK','DROP'].includes(question.question_type)">
      <h4>Options</h4>
      <span v-if="validationError && validationError.options" class="error">{{ validationError.options }}</span>
      <div v-if="question.question_type === 'DROP'" class="option-block">
      </div>
      <OptionEditor
        v-for="(option, oIdx) in question.options"
        :key="option.id || oIdx"
        :option="option"
        :questions="questions"
        :questionIndex="questionIndex"
        :optionIndex="oIdx"
        :validationError="validationError && validationError.optionsDetail && validationError.optionsDetail[oIdx]"
        @update:option="updateOption(oIdx, $event)"
        @remove="removeOption(oIdx)"
      />
      <button @click="addOption">Add Option</button>
    </div>
    <div style="margin-top: 0.5em;">
      <label>
        <input type="checkbox" v-model="showTriggers" /> Enable triggers for this question
      </label>
      <div v-if="showTriggers" style="margin-top: 0.5em;">
        <label>Triggers Questions:</label>
        <div class="checkbox-group">
          <label v-for="q in questions.filter(q => q.id !== question.id)" :key="q.id || q.order">
            <input
              type="checkbox"
              :checked="question.triggers_question && question.triggers_question.includes(q.id)"
              @change="toggleTriggerQuestion(q.id)"
            />
            {{ q.text || 'Untitled Question' }}
          </label>
        </div>
      </div>
    </div>
    <div style="margin-top: 0.5em;">
      <label>Section:
        <select :value="question.section_id" @change="updateQuestion('section_id', $event.target.value)">
          <option v-for="sec in sections" :key="sec.id" :value="sec.id">{{ sec.name }}</option>
        </select>
      </label>
    </div>
  </div>
</template>


<script setup>
import OptionEditor from './OptionEditor.vue';

const props = defineProps(['question', 'questions', 'sections', 'questionIndex', 'validationError']);
const emit = defineEmits(['update:question', 'remove', 'move']);

const updateQuestion = (key, value) => {
  emit('update:question', { ...props.question, [key]: value });
};

const addOption = () => {
  const options = [...(props.question.options || [])];
  options.push({ text: '', triggers_question: [] });
  updateQuestion('options', options);
};

const removeOption = (oIdx) => {
  const options = [...props.question.options];
  options.splice(oIdx, 1);
  updateQuestion('options', options);
};

const updateOption = (oIdx, option) => {
  const options = [...props.question.options];
  options[oIdx] = option;
  updateQuestion('options', options);
};


import { ref, watch } from 'vue';

const showTriggers = ref(Array.isArray(props.question.triggers_question) && props.question.triggers_question.length > 0);

watch(showTriggers, (newValue) => {
  if (!newValue) {
    updateQuestion('triggers_question', []);
  }
});

const toggleTriggerQuestion = (questionId) => {
  const currentTriggers = props.question.triggers_question || [];
  const newTriggers = [...currentTriggers];
  const index = newTriggers.indexOf(questionId);
  if (index > -1) {
    newTriggers.splice(index, 1);
  } else {
    newTriggers.push(questionId);
  }
  updateQuestion('triggers_question', newTriggers);
};
</script>

<style scoped>
.checkbox-group {
  max-height: 150px;
  overflow-y: auto;
  border: 1px solid #ccc;
  padding: 0.5em;
  border-radius: 4px;
}
.checkbox-group label {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
