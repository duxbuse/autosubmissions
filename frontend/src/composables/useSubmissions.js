
import { ref } from 'vue';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export function useSubmissions(formId, questions, answers, clientName, submissionDate, submissionId, submitSuccess, submitError) {
  const searchClient = ref('');
  const searchResults = ref([]);
  const searchPerformed = ref(false);
  const selectedSubmissionId = ref(null);

  const onSearchClient = async () => {
    const name = searchClient.value.trim();
    if (!name) {
      searchResults.value = [];
      searchPerformed.value = false;
      return;
    }
    try {
      const res = await axios.get(`${API_BASE}/api/submissions/?form=${formId}`);
      let results = Array.isArray(res.data) ? res.data : (res.data.results || []);
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

  const loadSubmission = (sub) => {
    if (!sub) return;
    selectedSubmissionId.value = sub.id;
    clientName.value = sub.client_name;
    submissionDate.value = sub.submission_date;
    if (Array.isArray(sub.answers)) {
      for (const q of questions.value) {
        const found = sub.answers.find(a => String(a.question) === String(q.id));
        if (found) {
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
    submissionId.value = sub.id;
    submitSuccess.value = false;
    submitError.value = false;
  };

  const deleteSubmission = async () => {
    if (!submissionId.value) return;
    if (!confirm('Are you sure you want to delete this submission? This action cannot be undone.')) return;
    try {
      await axios.delete(`${API_BASE}/api/submissions/${submissionId.value}/`);
      submissionId.value = null;
      submitSuccess.value = false;
      submitError.value = false;
      Object.keys(answers).forEach(k => answers[k] = Array.isArray(answers[k]) ? [] : '');
      clientName.value = '';
      submissionDate.value = (new Date()).toISOString().slice(0, 10);
      alert('Submission deleted.');
      if (searchClient.value) await onSearchClient();
    } catch (e) {
      alert('Failed to delete submission.');
    }
  };

  return {
    searchClient,
    searchResults,
    searchPerformed,
    selectedSubmissionId,
    onSearchClient,
    loadSubmission,
    deleteSubmission,
  };
}
