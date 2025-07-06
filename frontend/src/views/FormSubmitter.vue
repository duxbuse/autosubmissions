<template>
  <div class="form-submitter">
    <div class="form-layout">
      <div class="form-container">
        <h1>Generate: {{ form?.name || '...' }}</h1>
        <div v-if="loading">Loading form...</div>
        <div v-else-if="!form">
          <p>Form not found.</p>
        </div>
        <form v-else @submit.prevent="submitForm">
          <FormHeader v-model:clientName="clientName" v-model:submissionDate="submissionDate" />
          <div v-if="form && form.sections && form.sections.length">
            <FormSection
              v-for="(section, sIdx) in form.sections"
              :key="section.id"
              :section="section"
              :isOpen="activeSectionIdx === sIdx"
              @toggle="openSection(sIdx)"
            >
              <template v-for="(question, qIdx) in sectionQuestions(section.id)" :key="question.id || qIdx">
                <Question
                  v-if="visibleQuestions.has(question.id)"
                  :question="question"
                  v-model="answers[question.id]"
                />
              </template>
            </FormSection>
          </div>
          <button type="submit" :disabled="!canSubmit">Submit</button>
          <button type="button" @click="downloadDoc" :disabled="!submissionId">Download Word Doc</button>
          <button type="button" @click="deleteSubmission" :disabled="!submissionId" class="delete-button">Delete Submission</button>
          <span v-if="submitSuccess" class="success">Submitted!</span>
          <span v-if="submitError" class="error">Error submitting form.</span>
        </form>
      </div>
      <SubmissionSearch v-if="form" v-model:searchClient="searchClient" :onSearchClient="onSearchClient">
        <SubmissionList
          :searchResults="searchResults"
          :selectedSubmissionId="selectedSubmissionId"
          :searchClient="searchClient"
          :searchPerformed="searchPerformed"
          :questions="questions"
          :loading="loading"
          @loadSubmission="loadSubmission"
        />
      </SubmissionSearch>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useForm } from '@/composables/useForm';
import { useSubmissions } from '@/composables/useSubmissions';
import FormHeader from '@/components/form/FormHeader.vue';
import FormSection from '@/components/form/FormSection.vue';
import Question from '@/components/form/Question.vue';
import SubmissionSearch from '@/components/submission/SubmissionSearch.vue';
import SubmissionList from '@/components/submission/SubmissionList.vue';
import '../main.css';

const route = useRoute();
const formId = route.params.id;

const {
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
} = useForm();

const {
  searchClient,
  searchResults,
  searchPerformed,
  selectedSubmissionId,
  onSearchClient,
  loadSubmission,
  deleteSubmission,
} = useSubmissions(formId, questions, answers, clientName, submissionDate, submissionId, submitSuccess, submitError);

const activeSectionIdx = ref(0);

function openSection(idx) {
  if (idx === activeSectionIdx.value) return;
  activeSectionIdx.value = idx;
}

function sectionQuestions(sectionId) {
  return questions.value.filter(q => q.section_id === sectionId);
}

const visibleQuestions = computed(() => {
  if (!questions.value) {
    return new Set();
  }

  const allTriggeredIds = new Set();
  questions.value.forEach(q => {
    (q.triggers_question || []).forEach(id => allTriggeredIds.add(id));
    (q.options || []).forEach(opt => {
      (opt.triggers_question || []).forEach(id => allTriggeredIds.add(id));
    });
  });

  const visible = new Set();
  questions.value.forEach(q => {
    const isTriggerTarget = allTriggeredIds.has(q.id);

    if (!isTriggerTarget) {
      if (!q.hidden) {
        visible.add(q.id);
      }
      return;
    }

    const isMadeVisible = questions.value.some(triggering_q => {
      const answer = answers[triggering_q.id];
      
      if (answer === undefined || answer === null || answer === '' || (Array.isArray(answer) && answer.length === 0)) {
        return false;
      }

      // Check direct question-to-question trigger
      if ((triggering_q.triggers_question || []).includes(q.id)) {
        return true;
      }

      // Check option-based trigger
      if (triggering_q.options) {
        const answerMatchesOption = (triggering_q.options || []).some(opt => {
          if (!(opt.triggers_question || []).includes(q.id)) {
            return false;
          }
          
          let isMatch = false;
          if (Array.isArray(answer)) {
            isMatch = answer.includes(opt.text);
          } else {
            isMatch = answer === opt.text;
          }

          return isMatch;
        });

        if (answerMatchesOption) {
          return true;
        }
      }

      return false;
    });

    if (isMadeVisible) {
      visible.add(q.id);
    }
  });

  return visible;
});
</script>

<style scoped>
.form-layout {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 2rem;
}

.form-container {
  flex: 1 1 0;
  min-width: 0;
}

.delete-button {
  margin-left: 0.5rem;
  color: #fff;
  background: #d9534f;
  border: none;
  border-radius: 4px;
  padding: 0.5em 1em;
}
</style>