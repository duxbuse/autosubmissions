<template>
  <div class="form-builder">
    <h1>Form Builder</h1>
    <!-- Default view: show all forms as tiles, with a big plus sign for new form -->
    <div v-if="!mode || (mode === 'edit' && !formId)">
      <h2>Select a form to edit or create a new one</h2>
      <div class="form-tiles">
        <!-- Big plus sign tile for new form -->
        <div class="form-tile new-form-tile" @click="selectMode('new')">
          <div class="plus-sign">+</div>
          <h3>New</h3>
        </div>
        <!-- Existing forms -->
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
    </div>
    <div v-else>
      <div class="form-meta">
        <label>
          <span>Form Name:</span>
          <input v-model="form.name" placeholder="Form name" />
        </label>
        <span v-if="validationErrors.form.name" class="error">{{ validationErrors.form.name }}</span>
        <label>
          <span>Description:</span>
          <textarea v-model="form.description" placeholder="Form description"></textarea>
        </label>
      </div>

      <h2>Sections</h2>
      <div class="sections-list">
        <button @click="addSection" >+ Add Section</button>
        <div v-for="(section, sIdx) in sections" :key="section.id" class="section-block">
          <input v-model="section.name" @input="renameSection(sIdx, section.name)" style="font-weight: bold; font-size: 1.1em; width: 60%;" />
          <button @click="removeSection(sIdx)" :disabled="sections.length === 1">Delete Section</button>
          <div class="questions-in-section">
            <div v-for="(question, qIdx) in questions.filter(q => q.section_id === section.id)" :key="question.id || qIdx" class="question-block">
              <div class="question-header">
                <span>Q{{ qIdx + 1 }}</span>
                <button @click="removeQuestion(questions.findIndex(qq => qq === question))">Delete</button>
                <button @click="moveQuestion(questions.findIndex(qq => qq === question), -1)" :disabled="questions.findIndex(qq => qq === question) === 0">↑</button>
                <button @click="moveQuestion(questions.findIndex(qq => qq === question), 1)" :disabled="questions.findIndex(qq => qq === question) === questions.length - 1">↓</button>
              </div>
              <div style="display: flex; align-items: center; gap: 1rem;">
                <input v-model="question.text" placeholder="Question text" style="flex:1;" />
                <label style="white-space:nowrap;">
                  <input type="checkbox" v-model="question.hidden" /> Hidden by default
                </label>
              </div>
              <span v-if="validationErrors.questions[questions.findIndex(qq => qq === question)] && validationErrors.questions[questions.findIndex(qq => qq === question)].text" class="error">{{ validationErrors.questions[questions.findIndex(qq => qq === question)].text }}</span>
              <select v-model="question.question_type">
                <option value="TEXT">Text</option>
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
                <div v-if="validationErrors.questions[questions.findIndex(qq => qq === question)] && validationErrors.questions[questions.findIndex(qq => qq === question)].options" class="error">{{ validationErrors.questions[questions.findIndex(qq => qq === question)].options }}</div>
                <div v-if="question.question_type === 'DROP'" class="option-block">
                  <label>
                    Triggers question for any selection:
                    <select v-model.number="question.any_option_triggers_question">
                      <option :value="null">None</option>
                      <option v-for="q in questions" :key="q.id || q.order" :value="Number(q.id)">{{ q.text }}</option>
                    </select>
                  </label>
                </div>
                <div v-for="(option, oIdx) in question.options" :key="option.id || oIdx" class="option-block">
                  <input v-model="option.text" placeholder="Option text" />
                  <label>
                    Triggers question:
                    <select v-model.number="option.triggers_question">
                      <option :value="null">None</option>
                      <template v-for="(q, qIdx2) in questions">
                        <option
                          v-if="qIdx2 !== questions.findIndex(qq => qq === question)"
                          :key="q.id !== undefined ? q.id : 'new-' + qIdx2"
                          :value="qIdx2"
                        >
                          {{ q.text }}
                        </option>
                      </template>
                    </select>
                  </label>
                  <button @click="removeOption(questions.findIndex(qq => qq === question), oIdx)">Delete Option</button>
                  <span v-if="validationErrors.questions[questions.findIndex(qq => qq === question)] && validationErrors.questions[questions.findIndex(qq => qq === question)].optionsDetail && validationErrors.questions[questions.findIndex(qq => qq === question)].optionsDetail[oIdx]" class="error">{{ validationErrors.questions[questions.findIndex(qq => qq === question)].optionsDetail[oIdx] }}</span>
                </div>
                <button @click="addOption(questions.findIndex(qq => qq === question))">Add Option</button>
              </div>
              <div style="margin-top: 0.5em;">
                <label>Section:
                  <select v-model="question.section_id">
                    <option v-for="sec in sections" :key="sec.id" :value="sec.id">{{ sec.name }}</option>
                  </select>
                </label>
              </div>
            </div>
            <button @click="addQuestion(section.id)" style="margin-top: 0.5em;">Add Question to Section</button>
          </div>
          
        </div>
      </div>

      <div class="actions">
        <button @click="saveForm" :disabled="saving">Save Form</button>
        <button @click="cancelEdit" :disabled="saving" style="margin-left: 1rem;">Cancel</button>
        <span v-if="saveSuccess" class="success">Saved!</span>
        <span v-if="saveError" class="error">Error saving form.</span>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import '../main.css';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const mode = ref('edit'); // Default to 'edit' mode
const formId = ref(null);
const selectedFormId = ref("");
const availableForms = ref([]);
const loading = ref(false);
const saving = ref(false);
const saveSuccess = ref(false);
const saveError = ref(false);
const form = reactive({ name: '', description: '' });
const questions = ref([]);
const validationErrors = reactive({
  form: {},
  questions: []
});

const selectMode = (m) => {
  mode.value = m;
  if (m === 'edit') {
    fetchAvailableForms();
    formId.value = null;
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

// Fetch forms on mount (for default view)
onMounted(() => {
  if (mode.value === 'edit') {
    fetchAvailableForms();
  }
});

// Helper: Map triggers_question from id to index for UI dropdowns
function mapTriggersQuestionIdToIndex(questionsArr) {
  const idToIndex = {};
  questionsArr.forEach((q, idx) => {
    if (q.id !== undefined && q.id !== null) idToIndex[q.id] = idx;
  });
  questionsArr.forEach((q) => {
    if (q.options) {
      q.options.forEach((o) => {
        // Always map triggers_question from id to index if it's not null/undefined
        if (o.triggers_question !== null && o.triggers_question !== undefined) {
          // If triggers_question is already an index (from UI), skip remapping
          if (typeof o.triggers_question === 'number' && o.triggers_question >= 0 && o.triggers_question < questionsArr.length && questionsArr[o.triggers_question].id === o.triggers_question) {
            return;
          }
          // Map id to index, or null if not found
          const idx = idToIndex[o.triggers_question];
          o.triggers_question = (typeof idx === 'number') ? idx : null;
        } else {
          o.triggers_question = null;
        }
      });
    }
  });
}

const loadForm = async (id) => {
  loading.value = true;
  try {
    const res = await axios.get(`${API_BASE}/api/forms/${id}/`);
    Object.assign(form, res.data);
    questions.value = (res.data.questions || []).map(q => ({
      ...q,
      hidden: q.hidden || false,
      any_option_triggers_question: q.any_option_triggers_question || null,
      options: q.options ? q.options.map(o => ({
        ...o,
        triggers_question: o.triggers_question !== undefined ? o.triggers_question : null,
      })) : [],
    }));
    // Map triggers_question from id to index for UI
    mapTriggersQuestionIdToIndex(questions.value);
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

const addQuestion = (sectionId = null) => {
  // Default to first section if exists
  let secId = sectionId;
  if (!secId && sections.value.length > 0) secId = sections.value[0].id;
  questions.value.push({
    text: '',
    question_type: 'TEXT',
    order: questions.value.length + 1,
    output_template: '',
    options: [],
    hidden: false,
    section_id: secId,
    // No id: new question, backend will assign
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
  // No id: new option, backend will assign
};
const removeOption = (qIdx, oIdx) => {
  questions.value[qIdx].options.splice(oIdx, 1);
};

function validateForm() {
  let valid = true;
  validationErrors.form = {};
  validationErrors.questions = [];
  // Form name required
  if (!form.name || !form.name.trim()) {
    validationErrors.form.name = 'Form name is required.';
    valid = false;
  }
  // Validate questions
  questions.value.forEach((q, qIdx) => {
    const qErr = {};
    if (!q.text || !q.text.trim()) {
      qErr.text = 'Question text is required.';
      valid = false;
    }
    if (["MC", "CHECK", "DROP"].includes(q.question_type)) {
      if (!q.options || q.options.length === 0) {
        qErr.options = 'At least one option is required.';
        valid = false;
      } else {
        q.options.forEach((o, oIdx) => {
          if (!o.text || !o.text.trim()) {
            if (!qErr.optionsDetail) qErr.optionsDetail = {};
            qErr.optionsDetail[oIdx] = 'Option text is required.';
            valid = false;
          }
        });
      }
    }
    validationErrors.questions[qIdx] = qErr;
  });
  return valid;
}


// Helper to resolve triggers_question index to id for payload
function resolveTriggersQuestion(option, questionsArr) {
  if (option.triggers_question == null) return null;
  const idx = option.triggers_question;
  const q = questionsArr[idx];
  return q && q.id !== undefined ? q.id : null;
}

const saveForm = async () => {
  if (!validateForm()) {
    saveError.value = true;
    return;
  }
  saving.value = true;
  saveSuccess.value = false;
  saveError.value = false;
  try {
    // Only send questions, never questions_read in payload
    const { questions_read, ...formForPayload } = form;
    const payload = {
      ...formForPayload,
      sections: sections.value.map(s => ({ id: s.id, name: s.name })),
      questions: questions.value.map((q, qIdx) => ({
        ...q,
        // Always include id if present, so backend can match for update
        hidden: !!q.hidden,
        any_option_triggers_question: q.any_option_triggers_question || null,
        section_id: q.section_id,
        options: q.options.map(o => ({
          text: o.text,
          triggers_question: resolveTriggersQuestion(o, questions.value),
          id: o.id,
        })),
      })),
    };
    console.log('Payload sent to backend:', JSON.stringify(payload, null, 2));
    let res;
    if (formId.value === 'new') {
      res = await axios.post(`${API_BASE}/api/forms/`, payload);
      // After create, update local state from backend response
      const newId = res.data.id;
      updateFormFromBackend(res.data);
      formId.value = newId;
    } else {
      res = await axios.put(`${API_BASE}/api/forms/${formId.value}/`, payload);
      // After update, update local state from backend response
      updateFormFromBackend(res.data);
    }
    saveSuccess.value = true;
    setTimeout(() => (saveSuccess.value = false), 2000);
  } catch (e) {
    saveError.value = true;
  } finally {
    saving.value = false;
  }
};

// Helper: Update local form/questions/sections state from backend response (using questions_read)
function updateFormFromBackend(data) {
  Object.assign(form, data);
  // Prefer questions_read if present, else fallback to questions
  const backendQuestions = data.questions_read || data.questions || [];
  questions.value = (backendQuestions).map(q => ({
    ...q,
    hidden: q.hidden || false,
    any_option_triggers_question: q.any_option_triggers_question || null,
    section_id: q.section_id,
    options: q.options ? q.options.map(o => ({
      ...o,
      triggers_question: o.triggers_question !== undefined ? o.triggers_question : null,
    })) : [],
  }));
  // Sections
  if (data.sections) {
    sections.value = data.sections.map(s => ({ id: s.id, name: s.name }));
    // Update sectionIdCounter to avoid id collision
    const maxId = Math.max(0, ...sections.value.map(s => s.id));
    sectionIdCounter = maxId + 1;
  }
  mapTriggersQuestionIdToIndex(questions.value);
}

// Debug: Watch for changes to triggers_question
watch(questions, (newVal) => {
  newVal.forEach((q, qIdx) => {
    if (q.options) {
      q.options.forEach((o, oIdx) => {
        console.log(`Question ${qIdx} (${q.text}, id=${q.id}) Option ${oIdx} (${o.text}, id=${o.id}) triggers_question:`, o.triggers_question, typeof o.triggers_question);
      });
    }
  });
}, { deep: true });

// Cancel editing: return to tile view (edit mode, no form selected)
function cancelEdit() {
  mode.value = 'edit';
  formId.value = null;
  fetchAvailableForms();
}

// --- Section support ---
const sections = ref([
  { id: 1, name: 'Section 1' }
]);
let sectionIdCounter = 2;
const addSection = () => {
  sections.value.push({ id: sectionIdCounter++, name: `Section ${sections.value.length + 1}` });
};
const removeSection = (idx) => {
  const secId = sections.value[idx].id;
  // Remove all questions in this section
  questions.value = questions.value.filter(q => q.section_id !== secId);
  sections.value.splice(idx, 1);
};
const renameSection = (idx, newName) => {
  sections.value[idx].name = newName;
};
// --- End section support ---
</script>
