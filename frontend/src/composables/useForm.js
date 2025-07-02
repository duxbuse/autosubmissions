import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export function useForm() {
  const route = useRoute();
  const formId = route.params.id;

  const loading = ref(true);
  const form = ref(null);
  const questions = ref([]);
  const answers = reactive({});
  const submitSuccess = ref(false);
  const submitError = ref(false);
  const submissionId = ref(null);
  const clientName = ref('');
  const submissionDate = ref(new Date().toISOString().slice(0, 10));

  const fetchForm = async () => {
    loading.value = true;
    try {
      const res = await axios.get(`${API_BASE}/api/forms/${formId}/`);
      let sections = res.data.sections;
      if (!sections || !Array.isArray(sections) || sections.length === 0) {
        if (res.data.description && res.data.description.includes('__SECTIONS__:')) {
          try {
            const match = res.data.description.match(/__SECTIONS__:({.*}|\[.*\])/);
            if (match) {
              sections = JSON.parse(match[1]);
            }
          } catch (err) {
            // ignore
          }
        }
      }
      form.value = { ...res.data, sections };
      let allQuestions = Array.isArray(res.data.questions) ? res.data.questions.slice() : [];
      if ((!allQuestions || allQuestions.length === 0) && Array.isArray(sections)) {
        for (const section of sections) {
          if (Array.isArray(section.questions)) {
            for (const q of section.questions) {
              if (q.section_id === undefined) q.section_id = section.id;
              allQuestions.push(q);
            }
          }
        }
      }
      questions.value = allQuestions;
      Object.keys(answers).forEach(k => delete answers[k]);
      for (const q of questions.value) {
        answers[q.id] = q.question_type === 'CHECK' ? [] : '';
      }
    } catch (e) {
      form.value = null;
    } finally {
      loading.value = false;
    }
  };

  const canSubmit = computed(() => {
    return clientName.value.trim() !== '' && submissionDate.value.trim() !== '';
  });

  const submitForm = async () => {
    submitSuccess.value = false;
    submitError.value = false;
    submissionId.value = null;
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
      let existing = null;
      try {
        const checkRes = await axios.get(`${API_BASE}/api/submissions/?form=${formId}`);
        let allSubs = Array.isArray(checkRes.data) ? checkRes.data : (checkRes.data.results || []);
        existing = allSubs.find(sub =>
          sub.client_name && sub.client_name.trim().toLowerCase() === clientName.value.trim().toLowerCase() &&
          sub.submission_date === submissionDate.value
        );
      } catch (e) {
        existing = null;
      }
      let res;
      if (existing) {
        res = await axios.put(`${API_BASE}/api/submissions/${existing.id}/`, payload);
      } else {
        res = await axios.post(`${API_BASE}/api/submissions/`, payload);
      }
      submissionId.value = res.data.id || null;
      submitSuccess.value = true;
      setTimeout(() => (submitSuccess.value = false), 2000);
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
      let filename = `submission_${submissionId.value}.docx`;
      const cd = res.headers['content-disposition'];
      if (cd) {
        const match = cd.match(/filename="?([^";]+)"?/);
        if (match) filename = match[1];
      }
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

  onMounted(fetchForm);

  return {
    loading,
    form,
    questions,
    answers,
    clientName,
    submissionDate,
    submissionId,
    submitSuccess,
    submitError,
    canSubmit,
    fetchForm,
    submitForm,
    downloadDoc,
  };
}
