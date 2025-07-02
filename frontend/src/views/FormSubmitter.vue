<template>
  <div class="form-submitter">
    <div style="display: flex; flex-direction: row; align-items: flex-start; gap: 2rem;">
      <div style="flex: 1 1 0; min-width: 0;">
        <h1>Generate: {{ form?.name || '...' }}</h1>
        <div v-if="loading">Loading form...</div>
        <div v-else-if="!form">
          <p>Form not found.</p>
        </div>
        <form v-else @submit.prevent="submitForm">
          <div class="submission-meta" style="margin-bottom: 1.5rem;">
            <label for="client_name"><b>Client Name:</b></label>
            <input id="client_name" v-model="clientName" placeholder="Enter client name" required style="margin-bottom: 1rem; width: 100%; max-width: 400px;" />
            <label for="submission_date"><b>Date:</b></label>
            <input id="submission_date" type="date" v-model="submissionDate" required style="margin-bottom: 1rem; width: 100%; max-width: 220px;" />
          </div>
          <div v-if="form && form.sections && form.sections.length">
            <div v-for="(section, sIdx) in form.sections" :key="section.id" class="form-section-accordion">
              <div
                class="section-header"
                :style="{ cursor: 'pointer', background: '#f7f7f7', borderRadius: '8px', padding: '0.75em 1em', marginBottom: '0.5em', fontWeight: 'bold', fontSize: '1.1em', border: '1px solid #ddd', boxShadow: '0 1px 4px #0001' }"
                @click="openSection(sIdx)"
                :aria-expanded="activeSectionIdx === sIdx"
              >
                <span>{{ section.name }}</span>
                <span v-if="activeSectionIdx === sIdx" style="float:right;">▼</span>
                <span v-else style="float:right;">▶</span>
              </div>
              <transition name="fade">
                <div v-show="activeSectionIdx === sIdx" class="section-body" style="padding: 1em 1.5em 1.5em 1.5em; background: #fff; border-radius: 0 0 8px 8px; border: 1px solid #eee; border-top: none;">
                  <template v-for="(question, qIdx) in sectionQuestions(section.id)" :key="question.id || qIdx">
                    <div v-if="!question.hidden || (question.hidden && isTriggeredByAnswers(question))" class="question-block">
                      <label :for="'q_' + question.id">{{ question.text }}</label>
                      <component
                        :is="components[getInputComponent(question)]"
                        v-model="answers[question.id]"
                        :options="question.options"
                        :id="'q_' + question.id"
                      ></component>
                    </div>
                  </template>
                </div>
              </transition>
            </div>
          </div>
          <button type="submit" :disabled="!canSubmit">Submit</button>
          <button type="button" @click="downloadDoc" :disabled="!submissionId">Download Word Doc</button>
          <button type="button" @click="deleteSubmission" :disabled="!submissionId" style="margin-left: 0.5rem; color: #fff; background: #d9534f; border: none; border-radius: 4px; padding: 0.5em 1em;">Delete Submission</button>
          <span v-if="submitSuccess" class="success">Submitted!</span>
          <span v-if="submitError" class="error">Error submitting form.</span>

      </form>
    </div>
    <div v-if="form" style="width: 320px; min-width: 220px; max-width: 400px;">
      <input
        v-model="searchClient"
        @input="onSearchClient"
        placeholder="Search submissions by client name..."
        style="width: 100%; padding: 0.5rem; border-radius: 6px; border: 1px solid #ccc;"
      />
      <div
        v-if="searchResults.length > 0"
        class="search-results-tiles"
        :style="{
          marginTop: '1rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          maxHeight: formHeight ? (formHeight + 'px') : 'unset',
          overflowY: 'auto',
        }"
        ref="tilesColumn"
      >
        <div
          v-for="sub in searchResults"
          :key="sub.id"
          class="tile"
          :class="{ selected: sub.id === selectedSubmissionId }"
          style="background: #fff; border-radius: 12px; box-shadow: 0 2px 8px #0001; padding: 1rem; min-width: 180px; cursor: pointer; border: 2px solid #eee; transition: border 0.2s;"
          @click="loadSubmission(sub)"
        >
          <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 0.5em;">{{ sub.client_name }}</div>
          <div style="font-size: 0.95em; color: #666;">Date: {{ sub.submission_date }}</div>
          <div style="font-size: 0.9em; color: #888; margin-top: 0.5em;">Submission #{{ sub.id }}</div>
        </div>
      </div>
      <div v-else-if="searchClient && searchPerformed" style="margin-top: 1rem; color: #888; font-size: 0.95em;">No submissions found.</div>
    </div>
    </div>
  </div>
</template>



<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue';

// --- State declarations ---
const tilesColumn = ref(null);
const formHeight = ref(null);
const searchClient = ref("");
const searchResults = ref([]);
const searchPerformed = ref(false);
const selectedSubmissionId = ref(null);
// (removed duplicate declarations)
const loading = ref(true);
const form = ref(null);
const questions = ref([]);
const answers = reactive({});

// --- For scrollable tiles column ---
const updateTilesHeight = () => {
  const formEl = document.querySelector('.form-submitter form');
  if (formEl) {
    formHeight.value = formEl.offsetHeight;
  }
};

onMounted(() => {
  nextTick(() => {
    updateTilesHeight();
    window.addEventListener('resize', updateTilesHeight);
  });
});

watch(
  [() => questions.value.length, () => loading.value],
  () => {
    nextTick(updateTilesHeight);
  },
  { immediate: false }
);

// Search submissions by client name
const onSearchClient = async () => {
  const name = searchClient.value.trim();
  if (!name) {
    searchResults.value = [];
    searchPerformed.value = false;
    return;
  }
  try {
    // Fetch all submissions for this form (backend may not filter client_name strictly)
    const res = await axios.get(`${API_BASE}/api/submissions/?form=${formId}`);
    let results = Array.isArray(res.data) ? res.data : (res.data.results || []);
    // Filter strictly by client name (case-insensitive substring match)
    const searchLower = name.toLowerCase();
    results = results.filter(sub =>
      typeof sub.client_name === 'string' && sub.client_name.toLowerCase().includes(searchLower)
    );
    searchResults.value = results;
    searchPerformed.value = true;
  } catch (e) {
    searchResults.value = [];
    searchPerformed.value = true;
  }
};

// Load a submission into the form for review
const loadSubmission = (sub) => {
  if (!sub) return;
  selectedSubmissionId.value = sub.id;
  // Set client name and date
  clientName.value = sub.client_name;
  submissionDate.value = sub.submission_date;
  // Set answers
  if (Array.isArray(sub.answers)) {
    for (const q of questions.value) {
      const found = sub.answers.find(a => String(a.question) === String(q.id));
      if (found) {
        // If value is a JSON array (for CHECK), parse it
        if (q.question_type === 'CHECK' && typeof found.value === 'string' && found.value.startsWith('[')) {
          try { answers[q.id] = JSON.parse(found.value); } catch { answers[q.id] = []; }
        } else {
          answers[q.id] = found.value;
        }
      } else {
        answers[q.id] = q.question_type === 'CHECK' ? [] : '';
      }
    }
  }
  // Set submissionId so download works for this submission
  submissionId.value = sub.id;
  submitSuccess.value = false;
  submitError.value = false;
};
import '../main.css';
import { useRoute } from 'vue-router';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const route = useRoute();
const formId = route.params.id;

const submitSuccess = ref(false);
const submitError = ref(false);
const submissionId = ref(null);
const clientName = ref("");
const submissionDate = ref((() => {
  const today = new Date();
  return today.toISOString().slice(0, 10);
})());


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
            onChange: () => {
              console.log('[SELECT] MC', { id: props.id, selected: opt.text });
              emit('update:modelValue', opt.text);
            }
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
      console.log('[SELECT] CHECK', { id: props.id, selected: val, checked: e.target.checked, newValue: arr });
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
      onChange: e => {
        console.log('[SELECT] DROP', { id: props.id, selected: e.target.value });
        emit('update:modelValue', e.target.value);
      }
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
    // Defensive: try to extract sections from both top-level and description (for legacy forms)
    let sections = res.data.sections;
    if (!sections || !Array.isArray(sections) || sections.length === 0) {
      // Try to parse from description if present
      if (res.data.description && res.data.description.includes('__SECTIONS__:')) {
        try {
          const match = res.data.description.match(/__SECTIONS__:(\{.*\}|\[.*\])/);
          if (match) {
            sections = JSON.parse(match[1]);
          }
        } catch (err) {
          // ignore
        }
      }
    }
    form.value = { ...res.data, sections };
    // Defensive: flatten questions from sections if top-level questions is empty
    let allQuestions = Array.isArray(res.data.questions) ? res.data.questions.slice() : [];
    if ((!allQuestions || allQuestions.length === 0) && Array.isArray(sections)) {
      for (const section of sections) {
        if (Array.isArray(section.questions)) {
          for (const q of section.questions) {
            // Attach section_id if missing
            if (q.section_id === undefined) q.section_id = section.id;
            allQuestions.push(q);
          }
        }
      }
    }
    questions.value = allQuestions;
    // Clear all previous answers
    Object.keys(answers).forEach(k => delete answers[k]);
    // Initialize answers for ALL questions (including hidden)
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
  const newlyVisible = [];
  // Debug: log questions and answers on every re-compute
  console.log('[DEBUG] visibleQuestions: questions', questions.value);
  console.log('[DEBUG] visibleQuestions: answers', JSON.parse(JSON.stringify(answers)));
  const hiddenQs = questions.value.filter(q => q.hidden);
  console.log('[DEBUG] Currently hidden questions:', hiddenQs.map(q => ({ id: q.id, text: q.text })));
  for (let i = 0; i < questions.value.length; ++i) {
    const q = questions.value[i];
    // Always show if not hidden
    if (!q.hidden) {
      visible.push(q);
      continue;
    }
    // If hidden, check if triggered by any previous answer
    let triggered = false;
    outer: for (let j = 0; j < i; ++j) {
      const prevQ = questions.value[j];
      if (prevQ.options && prevQ.options.length) {
        for (const opt of prevQ.options) {
          // Debug: log trigger check for every option, including types
          console.log('[DEBUG] Checking trigger', {
            prevQid: prevQ.id,
            prevQType: prevQ.question_type,
            optText: opt.text,
            optTriggers: opt.triggers_question,
            optTriggersType: typeof opt.triggers_question,
            qid: q.id,
            qidType: typeof q.id,
            answer: answers[prevQ.id]
          });
          if (opt.triggers_question == q.id) {
            // For MC, DROP: check if answer matches option
            if ((prevQ.question_type === 'MC' || prevQ.question_type === 'DROP') && answers[prevQ.id] === opt.text) {
              console.log('[TRIGGER] MC/DROP', { prevQid: prevQ.id, answer: answers[prevQ.id], opt: opt.text, triggers: q.id });
              triggered = true;
              break outer;
            }
            // For CHECK: always treat answer as array
            if (prevQ.question_type === 'CHECK') {
              const arr = Array.isArray(answers[prevQ.id]) ? answers[prevQ.id] : [];
              // Debug log
              console.log('[DEBUG] CHECK trigger compare', { arr, optText: opt.text, includes: arr.includes(opt.text) });
              if (arr.includes(opt.text)) {
                console.log('[TRIGGER] CHECK', { prevQid: prevQ.id, answer: arr, opt: opt.text, triggers: q.id });
                triggered = true;
                break outer;
              }
            }
          }
        }
      }
      // For DROP: any_option_triggers_question
      if (prevQ.question_type === 'DROP' && prevQ.any_option_triggers_question == q.id && answers[prevQ.id]) {
        console.log('[TRIGGER] DROP any_option', { prevQid: prevQ.id, answer: answers[prevQ.id], triggers: q.id });
        triggered = true;
        break outer;
      }
    }
    if (triggered) {
      visible.push(q);
      newlyVisible.push(q.id);
    }
  }
  if (newlyVisible.length > 0) {
    console.log('[VISIBLE] Newly visible hidden questions:', newlyVisible);
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

const canSubmit = computed(() => {
  return clientName.value.trim() !== '' && submissionDate.value.trim() !== '';
});

const submitForm = async () => {
  submitSuccess.value = false;
  submitError.value = false;
  submissionId.value = null;
  // Validate required fields
  if (!canSubmit.value) {
    submitError.value = true;
    alert('Please enter both client name and date.');
    return;
  }
  try {
    const payload = {
      form: formId,
      client_name: clientName.value,
      submission_date: submissionDate.value,
      answers: Object.entries(answers).map(([question, value]) => ({
        question,
        value: Array.isArray(value) ? JSON.stringify(value) : value,
      })),
    };

    // 1. Check for existing submission with same form, client_name, and submission_date
    let existing = null;
    try {
      const checkRes = await axios.get(`${API_BASE}/api/submissions/?form=${formId}`);
      let allSubs = Array.isArray(checkRes.data) ? checkRes.data : (checkRes.data.results || []);
      existing = allSubs.find(sub =>
        sub.client_name && sub.client_name.trim().toLowerCase() === clientName.value.trim().toLowerCase() &&
        sub.submission_date === submissionDate.value
      );
    } catch (e) {
      // If check fails, fallback to create
      existing = null;
    }

    let res;
    if (existing) {
      // Update existing submission
      res = await axios.put(`${API_BASE}/api/submissions/${existing.id}/`, payload);
    } else {
      // Create new submission
      res = await axios.post(`${API_BASE}/api/submissions/`, payload);
    }
    submissionId.value = res.data.id || null;
    submitSuccess.value = true;
    setTimeout(() => (submitSuccess.value = false), 2000);
    // Automatically download the Word doc after successful submission
    if (submissionId.value) {
      await downloadDoc();
    }
  } catch (e) {
    submitError.value = true;
  }
};

const downloadDoc = async () => {
  if (!submissionId.value) return;
  try {
    const url = `${API_BASE}/api/submissions/${submissionId.value}/generate_doc/`;
    const res = await axios.get(url, { responseType: 'blob' });
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    // Try to get filename from Content-Disposition header
    let filename = `submission_${submissionId.value}.docx`;
    const cd = res.headers['content-disposition'];
    if (cd) {
      const match = cd.match(/filename="?([^";]+)"?/);
      if (match) filename = match[1];
    }
    // Create a link and trigger download
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      document.body.removeChild(link);
    }, 100);
  } catch (e) {
    alert('Failed to download Word document.');
  }
};

// Helper: Determine if a hidden question is being triggered (shown due to prior selection)
function isTriggered(qIdx) {
  // A question is considered triggered if it is hidden by default and is not the first visible question
  // (since visibleQuestions is ordered, and hidden questions only appear if triggered)
  // This logic can be adjusted for more complex cases.
  const q = visibleQuestions.value[qIdx];
  return q && q.hidden;
}


// Delete the current submission
const deleteSubmission = async () => {
  if (!submissionId.value) return;
  if (!confirm('Are you sure you want to delete this submission? This action cannot be undone.')) return;
  try {
    await axios.delete(`${API_BASE}/api/submissions/${submissionId.value}/`);
    // Clear form state after deletion
    submissionId.value = null;
    submitSuccess.value = false;
    submitError.value = false;
    // Optionally, reload form or clear answers
    Object.keys(answers).forEach(k => answers[k] = Array.isArray(answers[k]) ? [] : '');
    clientName.value = '';
    submissionDate.value = (new Date()).toISOString().slice(0, 10);
    alert('Submission deleted.');
    // Optionally, refresh search results
    if (searchClient.value) await onSearchClient();
  } catch (e) {
    alert('Failed to delete submission.');
  }
};

// --- Accordion section logic ---
const activeSectionIdx = ref(0);
// Only allow opening next section if all required questions in current section are answered
function openSection(idx) {
  if (idx === activeSectionIdx.value) return;
  // Only allow opening next section if current is complete or previous
  if (idx > activeSectionIdx.value) {
    // Check if current section is complete
    const currentSection = form.value.sections[activeSectionIdx.value];
    if (!isSectionComplete(currentSection)) {
      alert('Please complete all questions in this section before proceeding.');
      return;
    }
  }
  activeSectionIdx.value = idx;
}

function sectionQuestions(sectionId) {
  // Return questions for this section, in order
  return questions.value.filter(q => q.section_id === sectionId);
}

function isSectionComplete(section) {
  if (!section) return true;
  const qs = questions.value.filter(q => q.section_id === section.id && !q.hidden);
  for (const q of qs) {
    if (q.question_type === 'CHECK') {
      if (!answers[q.id] || answers[q.id].length === 0) return false;
    } else {
      if (!answers[q.id] || answers[q.id] === '') return false;
    }
  }
  return true;
}

// Helper: For hidden questions, check if they are triggered by answers
function isTriggeredByAnswers(question) {
  // Find all questions before this one (in the same section or previous sections)
  const idx = questions.value.findIndex(q => q.id === question.id);
  for (let j = 0; j < idx; ++j) {
    const prevQ = questions.value[j];
    if (prevQ.options && prevQ.options.length) {
      for (const opt of prevQ.options) {
        // Multi-trigger support: triggers_question is an array of IDs
        let triggers = opt.triggers_question;
        if (!Array.isArray(triggers)) triggers = triggers != null ? [triggers] : [];
        if (triggers.includes(question.id)) {
          if ((prevQ.question_type === 'MC' || prevQ.question_type === 'DROP') && answers[prevQ.id] === opt.text) {
            return true;
          }
          if (prevQ.question_type === 'CHECK') {
            const arr = Array.isArray(answers[prevQ.id]) ? answers[prevQ.id] : [];
            if (arr.includes(opt.text)) {
              return true;
            }
          }
        }
      }
    }
    if (prevQ.question_type === 'DROP' && prevQ.any_option_triggers_question == question.id && answers[prevQ.id]) {
      return true;
    }
  }
  return false;
}
// --- End accordion section logic ---
</script>  