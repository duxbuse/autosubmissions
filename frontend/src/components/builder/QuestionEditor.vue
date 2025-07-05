
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
        <label>
          Triggers question for any selection:
          <select :value="question.any_option_triggers_question" @change="updateQuestion('any_option_triggers_question', $event.target.value)">
            <option :value="null">None</option>
            <option v-for="q in questions" :key="q.id || q.order" :value="Number(q.id)">{{ q.text }}</option>
          </select>
        </label>
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
        <label>Triggers Questions:
          <select multiple :value="question.triggers_question || []" @change="onTriggersChange($event)" style="min-width: 200px;">
            <option v-for="q in questions" :key="q.id || q.order" :value="q.id">{{ q.text }}</option>
          </select>
        </label>
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
import InputDate from '@/components/form/input/InputDate.vue';

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
watch(() => props.question.triggers_question, (val) => {
  showTriggers.value = Array.isArray(val) && val.length > 0;
});

const onTriggersChange = (e) => {
  const selected = Array.from(e.target.selectedOptions).map(opt => Number(opt.value));
  updateQuestion('triggers_question', selected);
};
</script>
