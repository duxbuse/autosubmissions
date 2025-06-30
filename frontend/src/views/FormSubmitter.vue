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
          :is="getInputComponent(question)"
          v-model="answers[question.id]"
          :question="question"
          :options="question.options"
          :id="'q_' + question.id"
        />
      </div>
      <button type="submit">Submit</button>
      <span v-if="submitSuccess" class="success">Submitted!</span>
      <span v-if="submitError" class="error">Error submitting form.</span>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
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

const fetchForm = async () => {
  loading.value = true;
  try {
    const res = await axios.get(`${API_BASE}/api/forms/${formId}/`);
    form.value = res.data;
    questions.value = res.data.questions || [];
    // Initialize answers for visible questions
    for (const q of questions.value) {
      answers[q.id] = '';
    }
  } catch (e) {
    form.value = null;
  } finally {
    loading.value = false;
  }
};

onMounted(fetchForm);

// Show only questions that are not hidden or are triggered (basic: just not hidden for now)
const visibleQuestions = computed(() => {
  return questions.value.filter(q => !q.hidden);
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

<script>
// Input components for each question type
export default {
  components: {
    'input-text': {
      props: ['modelValue', 'id'],
      emits: ['update:modelValue'],
      template: `<input :id="id" type="text" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" />`,
    },
    'input-paragraph': {
      props: ['modelValue', 'id'],
      emits: ['update:modelValue'],
      template: `<textarea :id="id" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)"></textarea>`,
    },
    'input-mc': {
      props: ['modelValue', 'options', 'id'],
      emits: ['update:modelValue'],
      template: `<div><label v-for="opt in options" :key="opt.id"><input type="radio" :name="id" :value="opt.text" :checked="modelValue === opt.text" @change="$emit('update:modelValue', opt.text)" /> {{ opt.text }}</label></div>`,
    },
    'input-check': {
      props: ['modelValue', 'options', 'id'],
      emits: ['update:modelValue'],
      template: `<div><label v-for="opt in options" :key="opt.id"><input type="checkbox" :value="opt.text" :checked="modelValue && modelValue.includes(opt.text)" @change="onChange($event, opt.text)" /> {{ opt.text }}</label></div>`,
      methods: {
        onChange(e, val) {
          let arr = Array.isArray(this.modelValue) ? [...this.modelValue] : [];
          if (e.target.checked) arr.push(val);
          else arr = arr.filter(v => v !== val);
          this.$emit('update:modelValue', arr);
        },
      },
    },
    'input-drop': {
      props: ['modelValue', 'options', 'id'],
      emits: ['update:modelValue'],
      template: `<select :id="id" :value="modelValue" @change="$emit('update:modelValue', $event.target.value)"><option value="">-- Select --</option><option v-for="opt in options" :key="opt.id" :value="opt.text">{{ opt.text }}</option></select>`,
    },
  },
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

