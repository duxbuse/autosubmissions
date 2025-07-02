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
          <FormHeader v-model:clientName="clientName" v-model:submissionDate="submissionDate" />
          <div v-if="form && form.sections && form.sections.length">
            <FormSection
              v-for="(section, sIdx) in form.sections"
              :key="section.id"
              :section="section"
              :isOpen="activeSectionIdx === sIdx"
              @toggle="openSection(sIdx)"
            >
              <Question
                v-for="(question, qIdx) in sectionQuestions(section.id)"
                :key="question.id || qIdx"
                :question="question"
                v-model="answers[question.id]"
                :isTriggered="isTriggeredByAnswers(question)"
              />
            </FormSection>
          </div>
          <button type="submit" :disabled="!canSubmit">Submit</button>
          <button type="button" @click="downloadDoc" :disabled="!submissionId">Download Word Doc</button>
          <button type="button" @click="deleteSubmission" :disabled="!submissionId" style="margin-left: 0.5rem; color: #fff; background: #d9534f; border: none; border-radius: 4px; padding: 0.5em 1em;">Delete Submission</button>
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
import { ref } from 'vue';
import { useRoute } from 'vue-router';
import { useForm } from '../composables/useForm';
import { useSubmissions } from '../composables/useSubmissions';
import FormHeader from '../components/form/FormHeader.vue';
import FormSection from '../components/form/FormSection.vue';
import Question from '../components/form/Question.vue';
import SubmissionSearch from '../components/submission/SubmissionSearch.vue';
import SubmissionList from '../components/submission/SubmissionList.vue';
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
  if (idx > activeSectionIdx.value) {
    const currentSection = form.value.sections[activeSectionIdx.value];
    if (!isSectionComplete(currentSection)) {
      alert('Please complete all questions in this section before proceeding.');
      return;
    }
  }
  activeSectionIdx.value = idx;
}

function sectionQuestions(sectionId) {
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

function isTriggeredByAnswers(question) {
  const idx = questions.value.findIndex(q => q.id === question.id);
  for (let j = 0; j < idx; ++j) {
    const prevQ = questions.value[j];
    if (prevQ.options && prevQ.options.length) {
      for (const opt of prevQ.options) {
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
</script>