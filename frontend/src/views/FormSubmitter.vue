<template>
  <div class="form-submitter">
    <h1>Submit: {{ form?.name || '...' }}</h1>
    <div v-if="loading">Loading form...</div>
    <div v-else-if="!form">
      <p>Form not found.</p>
    </div>
    <form v-else @submit.prevent="submitForm">
      <div v-for="(question, qIdx) in visibleQuestions" :key="question.id || qIdx" class="question-block">
        <label :for="'q_' + question.id">{{ question.text }}</label>
        <component
          :is="components[getInputComponent(question)]"
          v-model="answers[question.id]"
          :options="question.options"
          :id="'q_' + question.id"
        ></component>
      </div>
      <button type="submit">Submit</button>
      <span v-if="submitSuccess" class="success">Submitted!</span>
      <span v-if="submitError" class="error">Error submitting form.</span>
    </form>
  </div>
</template>


<script setup>
import { ref, reactive, computed, onMounted, defineAsyncComponent } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const route = useRoute();
const formId = route.params.id;
const loading = ref(true);
const form = ref(null);
const questions = ref([]);
const answers = reactive({});
const submitSuccess = ref(false);
const submitError = ref(false);


// Input components as SFCs for runtime-only Vue (no template option)
import { h } from 'vue';

const inputText = {
  props: ['modelValue', 'id'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('input', {
      id: props.id,
      type: 'text',
      value: props.modelValue,
      onInput: e => emit('update:modelValue', e.target.value)
    });
  }
};

const inputParagraph = {
  props: ['modelValue', 'id'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('textarea', {
      id: props.id,
      value: props.modelValue,
      onInput: e => emit('update:modelValue', e.target.value)
    });
  }
};

const inputMc = {
  props: ['modelValue', 'options', 'id'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('div', {},
      props.options?.map(opt =>
        h('label', { key: opt.id }, [
          h('input', {
            type: 'radio',
            name: props.id,
            value: opt.text,
            checked: props.modelValue === opt.text,
            onChange: () => emit('update:modelValue', opt.text)
          }),
          ' ',
          opt.text
        ])
      )
    );
  }
};

const inputCheck = {
  props: ['modelValue', 'options', 'id'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const onChange = (e, val) => {
      let arr = Array.isArray(props.modelValue) ? [...props.modelValue] : [];
      if (e.target.checked && !arr.includes(val)) arr.push(val);
      else if (!e.target.checked) arr = arr.filter(v => v !== val);
      emit('update:modelValue', arr);
    };
    return () => h('div', {},
      props.options?.map(opt =>
        h('label', { key: opt.id }, [
          h('input', {
            type: 'checkbox',
            value: opt.text,
            checked: props.modelValue && props.modelValue.includes(opt.text),
            onChange: e => onChange(e, opt.text)
          }),
          ' ',
          opt.text
        ])
      )
    );
  }
};

const inputDrop = {
  props: ['modelValue', 'options', 'id'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('select', {
      id: props.id,
      value: props.modelValue,
      onChange: e => emit('update:modelValue', e.target.value)
    }, [
      h('option', { value: '' }, '-- Select --'),
      ...(props.options?.map(opt =>
        h('option', { key: opt.id, value: opt.text }, opt.text)
      ) || [])
    ]);
  }
};

const components = {
  'input-text': inputText,
  'input-paragraph': inputParagraph,
  'input-mc': inputMc,
  'input-check': inputCheck,
  'input-drop': inputDrop
};

const fetchForm = async () => {
  loading.value = true;
  try {
    const res = await axios.get(`${API_BASE}/api/forms/${formId}/`);
    form.value = res.data;
    questions.value = res.data.questions || [];
    // Initialize answers for visible questions
    for (const q of questions.value) {
      answers[q.id] = q.question_type === 'CHECK' ? [] : '';
    }
  } catch (e) {
    form.value = null;
  } finally {
    loading.value = false;
  }
};

onMounted(fetchForm);


// Show questions that are not hidden, or are triggered by answers to previous questions
const visibleQuestions = computed(() => {
  // Map question id to index for fast lookup
  const idToIdx = {};
  questions.value.forEach((q, i) => { idToIdx[q.id] = i; });

  // Track which questions are visible
  const visible = [];
  for (let i = 0; i < questions.value.length; ++i) {
    const q = questions.value[i];
    // Always show if not hidden
    if (!q.hidden) {
      visible.push(q);
      continue;
    }
    // If hidden, check if triggered by any previous answer
    let triggered = false;
    // Check if any option in any previous question triggers this question
    for (let j = 0; j < i; ++j) {
      const prevQ = questions.value[j];
      if (prevQ.options && prevQ.options.length) {
        for (const opt of prevQ.options) {
          if (opt.triggers_question == q.id) {
            // For MC, DROP: check if answer matches option
            if ((prevQ.question_type === 'MC' || prevQ.question_type === 'DROP') && answers[prevQ.id] === opt.text) {
              triggered = true;
            }
            // For CHECK: check if answer array includes option
            if (prevQ.question_type === 'CHECK' && Array.isArray(answers[prevQ.id]) && answers[prevQ.id].includes(opt.text)) {
              triggered = true;
            }
          }
        }
      }
      // For DROP: any_option_triggers_question
      if (prevQ.question_type === 'DROP' && prevQ.any_option_triggers_question == q.id && answers[prevQ.id]) {
        triggered = true;
      }
    }
    if (triggered) visible.push(q);
  }
  return visible;
});

const getInputComponent = (question) => {
  switch (question.question_type) {
    case 'TEXT':
      return 'input-text';
    case 'PARAGRAPH':
      return 'input-paragraph';
    case 'MC':
      return 'input-mc';
    case 'CHECK':
      return 'input-check';
    case 'DROP':
      return 'input-drop';
    default:
      return 'input-text';
  }
};

const submitForm = async () => {
  submitSuccess.value = false;
  submitError.value = false;
  try {
    const payload = {
      form: formId,
      answers: Object.entries(answers).map(([question, value]) => ({
        question,
        value: Array.isArray(value) ? JSON.stringify(value) : value,
      })),
    };
    await axios.post(`${API_BASE}/api/submissions/`, payload);
    submitSuccess.value = true;
    setTimeout(() => (submitSuccess.value = false), 2000);
  } catch (e) {
    submitError.value = true;
  }
};
</script>



<style scoped>
.form-submitter {
  max-width: 700px;
  margin: 0 auto;
  padding: 2rem;
}
.question-block {
  border: 1px solid #ccc;
  padding: 1rem;
  margin-bottom: 1.5rem;
  border-radius: 6px;
  background: #fafbfc;
}
.success {
  color: green;
  margin-left: 1rem;
}
.error {
  color: red;
  margin-left: 1rem;
}
</style>

