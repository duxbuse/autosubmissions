<template>
  <div class="form-builder">
    <h1>Form Builder</h1>
    <div v-if="!mode">
      <button @click="selectMode('new')">Create New Form</button>
      <button @click="selectMode('edit')">Edit Existing Form</button>
    </div>
    <div v-else-if="mode === 'edit' && !formId">
      <h2>Select a form to edit</h2>
      <div class="form-tiles">
        <div
          v-for="f in availableForms"
          :key="f.id"
          class="form-tile"
          @click="loadForm(f.id)"
        >
          <h3>{{ f.name }}</h3>
          <p>{{ f.description }}</p>
        </div>
      </div>
      <button style="margin-top:2rem" @click="mode = null">Back</button>
    </div>
    <div v-else>
      <div class="form-meta">
        <label>
          <span>Form Name:</span>
          <input v-model="form.name" placeholder="Form name" />
        </label>
        <label>
          <span>Description:</span>
          <textarea v-model="form.description" placeholder="Form description"></textarea>
        </label>
      </div>

      <h2>Questions</h2>
      <div v-for="(question, qIdx) in questions" :key="question.id || qIdx" class="question-block">
        <div class="question-header">
          <span>Q{{ qIdx + 1 }}</span>
          <button @click="removeQuestion(qIdx)">Delete</button>
          <button @click="moveQuestion(qIdx, -1)" :disabled="qIdx === 0">↑</button>
          <button @click="moveQuestion(qIdx, 1)" :disabled="qIdx === questions.length - 1">↓</button>
        </div>
        <div style="display: flex; align-items: center; gap: 1rem;">
          <input v-model="question.text" placeholder="Question text" style="flex:1;" />
          <label style="white-space:nowrap;">
            <input type="checkbox" v-model="question.hidden" /> Hidden by default
          </label>
        </div>
        <select v-model="question.question_type">
          <option value="TEXT">Text</option>
          <option value="PARAGRAPH">Paragraph</option>
          <option value="MC">Multiple Choice</option>
          <option value="CHECK">Checkboxes</option>
          <option value="DROP">Dropdown</option>
        </select>
        <label>
          <span>Output Template:</span>
          <textarea v-model="question.output_template" placeholder="e.g. 'The answer is {{answer}}.'"></textarea>
        </label>

        <div v-if="['MC','CHECK','DROP'].includes(question.question_type)">
          <h4>Options</h4>
          <div v-if="question.question_type === 'DROP'" class="option-block">
            <label>
              Triggers question for any selection:
              <select v-model="question.any_option_triggers_question">
                <option :value="null">None</option>
                <option v-for="q in questions" :key="q.id || q.order" :value="q.id">{{ q.text }}</option>
              </select>
            </label>
          </div>
          <div v-for="(option, oIdx) in question.options" :key="option.id || oIdx" class="option-block">
            <input v-model="option.text" placeholder="Option text" />
            <label>
              Triggers question:
              <select v-model="option.triggers_question">
                <option :value="null">None</option>
                <option v-for="q in questions" :key="q.id || q.order" :value="q.id">{{ q.text }}</option>
              </select>
            </label>
            <button @click="removeOption(qIdx, oIdx)">Delete Option</button>
          </div>
          <button @click="addOption(qIdx)">Add Option</button>
        </div>
      </div>
      <button @click="addQuestion">Add Question</button>
      <div class="actions">
        <button @click="saveForm" :disabled="saving">Save Form</button>
        <span v-if="saveSuccess" class="success">Saved!</span>
        <span v-if="saveError" class="error">Error saving form.</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const mode = ref(null); // 'new' or 'edit'
const formId = ref(null);
const selectedFormId = ref("");
const availableForms = ref([]);
const loading = ref(false);
const saving = ref(false);
const saveSuccess = ref(false);
const saveError = ref(false);
const form = reactive({ name: '', description: '' });
const questions = ref([]);

const selectMode = (m) => {
  mode.value = m;
  if (m === 'edit') {
    fetchAvailableForms();
  } else if (m === 'new') {
    formId.value = 'new';
    resetForm();
  }
};

const fetchAvailableForms = async () => {
  loading.value = true;
  try {
    const res = await axios.get(`${API_BASE}/api/forms/`);
    availableForms.value = res.data;
  } catch (e) {
    availableForms.value = [];
  } finally {
    loading.value = false;
  }
};

const loadForm = async (id) => {
  loading.value = true;
  try {
    const res = await axios.get(`${API_BASE}/api/forms/${id}/`);
    Object.assign(form, res.data);
    questions.value = (res.data.questions || []).map(q => ({
      ...q,
      hidden: q.hidden || false,
      any_option_triggers_question: q.any_option_triggers_question || null,
      options: q.options ? q.options.map(o => ({ ...o })) : [],
    }));
    formId.value = id;
  } catch (e) {
    // handle error
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  form.name = '';
  form.description = '';
  questions.value = [];
};

const addQuestion = () => {
  questions.value.push({
    text: '',
    question_type: 'TEXT',
    order: questions.value.length + 1,
    output_template: '',
    options: [],
    hidden: false,
  });
};
const removeQuestion = idx => {
  questions.value.splice(idx, 1);
  questions.value.forEach((q, i) => (q.order = i + 1));
};
const moveQuestion = (idx, dir) => {
  const newIdx = idx + dir;
  if (newIdx < 0 || newIdx >= questions.value.length) return;
  const temp = questions.value[idx];
  questions.value[idx] = questions.value[newIdx];
  questions.value[newIdx] = temp;
  questions.value.forEach((q, i) => (q.order = i + 1));
};

const addOption = qIdx => {
  questions.value[qIdx].options.push({ text: '', triggers_question: null });
};
const removeOption = (qIdx, oIdx) => {
  questions.value[qIdx].options.splice(oIdx, 1);
};

const saveForm = async () => {
  saving.value = true;
  saveSuccess.value = false;
  saveError.value = false;
  try {
    const payload = {
      ...form,
      questions: questions.value.map(q => ({
        ...q,
        hidden: !!q.hidden,
        any_option_triggers_question: q.any_option_triggers_question || null,
        options: q.options.map(o => ({
          text: o.text,
          triggers_question: o.triggers_question || null,
          id: o.id,
        })),
      })),
    };
    if (formId.value === 'new') {
      await axios.post(`${API_BASE}/api/forms/`, payload);
    } else {
      await axios.put(`${API_BASE}/api/forms/${formId.value}/`, payload);
    }
    saveSuccess.value = true;
    setTimeout(() => (saveSuccess.value = false), 2000);
  } catch (e) {
    saveError.value = true;
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.form-builder {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}
.form-meta label {
  display: block;
  margin-bottom: 1rem;
}
.question-block {
  border: 1px solid #ccc;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 6px;
  background: #fafbfc;
}
.question-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}
.option-block {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}
.actions {
  margin-top: 2rem;
}
.success {
  color: green;
  margin-left: 1rem;
}
.error {
  color: red;
  margin-left: 1rem;
}
  /* Tile styles for edit mode, matching HomePage */
  .form-tiles {
    display: flex;
    flex-wrap: wrap;
    gap: 2rem;
    margin-top: 2rem;
  }
  .form-tile {
    background: #f5f7fa;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    padding: 2rem 2.5rem;
    min-width: 220px;
    max-width: 320px;
    cursor: pointer;
    transition: box-shadow 0.2s, transform 0.2s;
    border: 1px solid #e0e0e0;
  }
  .form-tile:hover {
    box-shadow: 0 6px 18px rgba(0,0,0,0.13);
    transform: translateY(-4px) scale(1.03);
    border-color: #b3b3ff;
  }
  .form-tile h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.15rem;
    color: #3a3a6a;
  }
  .form-tile p {
    color: #666;
    margin: 0;
  }
</style>

