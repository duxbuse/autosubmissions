import { ref, reactive, onMounted } from 'vue';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export function useFormBuilder() {
  const mode = ref('edit');
  const formId = ref(null);
  const availableForms = ref([]);
  const loading = ref(false);
  const saving = ref(false);
  const saveSuccess = ref(false);
  const saveError = ref(false);
  const form = reactive({ name: '', description: '' });
  const questions = ref([]);
  const sections = ref([{ id: 1, name: 'Section 1' }]);
  let sectionIdCounter = 2;

  const validationErrors = reactive({
    form: {},
    questions: []
  });

  const selectMode = (m) => {
    const prevMode = mode.value;
    console.debug('[selectMode] prevMode:', prevMode, 'newMode:', m);
    mode.value = m;
    if (m === 'edit') {
      fetchAvailableForms();
      formId.value = null;
    } else if (m === 'new') {
      formId.value = 'new';
      if (prevMode !== 'new') {
        console.debug('[selectMode] Calling resetForm()');
        resetForm();
      }
    }
    console.debug('[selectMode] form:', JSON.stringify(form), 'formId:', formId.value);
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

  onMounted(() => {
    if (mode.value === 'edit') {
      fetchAvailableForms();
    }
  });

  function mapTriggersQuestionIdToIndex(questionsArr) {
    questionsArr.forEach((q) => {
      if (q.options) {
        q.options.forEach((o) => {
          if (!Array.isArray(o.triggers_question)) {
            if (o.triggers_question == null) o.triggers_question = [];
            else o.triggers_question = [o.triggers_question];
          }
        });
      }
    });
  }

  const loadForm = async (id) => {
    loading.value = true;
    try {
      const res = await axios.get(`${API_BASE}/api/forms/${id}/`);
      updateFormFromBackend(res.data);
      formId.value = id;
    } catch (e) {
      // handle error
    } finally {
      loading.value = false;
    }
  };

  const resetForm = () => {
    console.debug('[resetForm] Resetting form');
    form.name = '';
    form.description = '';
    questions.value = [];
    sections.value = [{ id: 1, name: 'Section 1' }];
    sectionIdCounter = 2;
    console.debug('[resetForm] After reset:', JSON.stringify(form));
  };

  // Only call resetForm when starting a new form, not after save
function validateFormAndScroll() {
  let valid = true;
  validationErrors.form = {};
  validationErrors.questions = [];
  let firstInvalidQuestionIdx = null;
  if (!form.name || !form.name.trim()) {
    validationErrors.form.name = 'Form name is required.';
    valid = false;
  }
  questions.value.forEach((q, qIdx) => {
    const qErr = {};
    if (!q.text || !q.text.trim()) {
      qErr.text = 'Question text is required.';
      valid = false;
      if (firstInvalidQuestionIdx === null) firstInvalidQuestionIdx = qIdx;
    }
    if (["MC", "CHECK", "DROP"].includes(q.question_type)) {
      if (!q.options || q.options.length === 0) {
        qErr.options = 'At least one option is required.';
        valid = false;
        if (firstInvalidQuestionIdx === null) firstInvalidQuestionIdx = qIdx;
      } else {
        q.options.forEach((o, oIdx) => {
          if (!o.text || !o.text.trim()) {
            if (!qErr.optionsDetail) qErr.optionsDetail = {};
            qErr.optionsDetail[oIdx] = 'Option text is required.';
            valid = false;
            if (firstInvalidQuestionIdx === null) firstInvalidQuestionIdx = qIdx;
          }
        });
      }
    }
    validationErrors.questions[qIdx] = qErr;
  });
  // Scroll to first invalid question if any
  if (firstInvalidQuestionIdx !== null) {
    setTimeout(() => {
      const el = document.querySelector(`[data-question-idx="${firstInvalidQuestionIdx}"]`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('highlight-validation');
        setTimeout(() => el.classList.remove('highlight-validation'), 2000);
      }
    }, 100);
  }
  return valid;
}

  function resolveTriggersQuestion(option, questionsArr) {
    if (!option.triggers_question) return [];
    if (Array.isArray(option.triggers_question)) {
      return option.triggers_question.filter(id => id != null);
    }
    return option.triggers_question != null ? [option.triggers_question] : [];
  }

  const saveForm = async () => {
    console.debug('[saveForm] form before validate:', JSON.stringify(form));
    if (!validateFormAndScroll()) {
      saveError.value = true;
      console.debug('[saveForm] Validation failed. form:', JSON.stringify(form));
      return;
    }
    saving.value = true;
    saveSuccess.value = false;
    saveError.value = false;
    try {
      const { questions_read, ...formForPayload } = form;
      const payload = {
        ...formForPayload,
        sections: sections.value.map(s => ({ id: s.id, name: s.name })),
        questions: questions.value.map((q, qIdx) => ({
          ...q,
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
      console.debug('[saveForm] payload:', JSON.stringify(payload));
      let res;
      if (formId.value === 'new') {
        res = await axios.post(`${API_BASE}/api/forms/`, payload);
        const newId = res.data.id;
        updateFormFromBackend(res.data);
        formId.value = newId;
      } else {
        res = await axios.put(`${API_BASE}/api/forms/${formId.value}/`, payload);
        updateFormFromBackend(res.data);
      }
      saveSuccess.value = true;
      setTimeout(() => (saveSuccess.value = false), 2000);
    } catch (e) {
      saveError.value = true;
      console.debug('[saveForm] Error:', e);
    } finally {
      saving.value = false;
      console.debug('[saveForm] Done. form:', JSON.stringify(form));
    }
  };

  function updateFormFromBackend(data) {
    Object.assign(form, data);
    const backendQuestions = data.questions_read || data.questions || [];
    if (data.sections && Array.isArray(data.sections) && data.sections.length > 0) {
      questions.value = (backendQuestions).map((q) => {
        let sectionId = q.section_id != null ? Number(q.section_id) : null;
        return {
          ...q,
          hidden: q.hidden || false,
          any_option_triggers_question: q.any_option_triggers_question || null,
          section_id: sectionId,
          options: q.options ? q.options.map(o => ({
            ...o,
            triggers_question: o.triggers_question !== undefined ? o.triggers_question : null,
          })) : [],
        };
      });
    } else {
      questions.value = (backendQuestions).map(q => ({
        ...q,
        hidden: q.hidden || false,
        any_option_triggers_question: q.any_option_triggers_question || null,
        section_id: q.section_id != null ? Number(q.section_id) : null,
        options: q.options ? q.options.map(o => ({
          ...o,
          triggers_question: o.triggers_question !== undefined ? o.triggers_question : null,
        })) : [],
      }));
    }
    if (data.sections && Array.isArray(data.sections) && data.sections.length > 0) {
      sections.value = data.sections.map(s => ({ id: Number(s.id), name: s.name }));
      const maxId = Math.max(0, ...sections.value.map(s => s.id));
      sectionIdCounter = maxId + 1;
    } else {
      const sectionMap = {};
      questions.value.forEach(q => {
        if (q.section_id != null) {
          const secId = Number(q.section_id);
          if (!sectionMap[secId]) {
            sectionMap[secId] = { id: secId, name: `Section ${secId}` };
          }
        }
      });
      const sectionArr = Object.values(sectionMap);
      if (sectionArr.length === 0) {
        sectionArr.push({ id: 1, name: 'Section 1' });
      }
      sections.value = sectionArr;
      sectionIdCounter = Math.max(...sections.value.map(s => s.id)) + 1;
    }
    mapTriggersQuestionIdToIndex(questions.value);
  }

  function cancelEdit() {
    mode.value = 'edit';
    formId.value = null;
    fetchAvailableForms();
  }

    // Use this to update form meta reactively from FormMeta
  function updateFormMeta(newForm) {
    Object.assign(form, newForm);
  }

  return {
    mode,
    formId,
    availableForms,
    loading,
    saving,
    saveSuccess,
    saveError,
    form,
    questions,
    sections,
    validationErrors,
    selectMode,
    loadForm,
    saveForm,
    cancelEdit,
    sectionIdCounter,
    updateFormMeta
  };
}
