<template>
  <div class="form-builder">
    <h1>Form Builder</h1>
    <div v-if="!mode || (mode === 'edit' && !formId)">
      <h2>Select a form to edit or create a new one</h2>
      <div class="form-tiles">
        <div class="form-tile new-form-tile" @click="selectMode('new')">
          <div class="plus-sign">+</div>
          <h3>New</h3>
        </div>
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
      <FormMeta :form="form" :validationErrors="validationErrors" @update:form="updateFormMeta" />


      <h2>Sections</h2>

      <div class="sections-list">
        <SectionEditor
          v-for="(section, sIdx) in sections"
          :key="section.id"
          :section="section"
          :index="sIdx"
          :isOpen="activeSectionIdx === sIdx"
          @dragdrop="handleSectionDragDrop($event)"
          @toggle="() => openSection(sIdx)"
          @rename="renameSection(sIdx, $event)"
        >
          <template #header-extra>
            <button @click.stop="moveSection(sIdx, -1)" style="position:absolute;top:0.5em;right:3em;background:none;border:none;font-size:1.2em;line-height:1;color:#333;cursor:pointer;" title="Move Up">↑</button>
            <button @click.stop="moveSection(sIdx, 1)" style="position:absolute;top:0.5em;right:1.9em;background:none;border:none;font-size:1.2em;line-height:1;color:#333;cursor:pointer;" title="Move Down">↓</button>
            <button @click.stop="removeSection(sIdx)" style="position:absolute;top:0.5em;right:0.75em;background:none;border:none;font-size:1.2em;line-height:1;color:#c00;cursor:pointer;" title="Delete">Delete ×</button>
          </template>
          <div class="questions-in-section">
            <QuestionEditor
              v-for="(question, qIdx) in questions.filter(q => q.section_id === section.id)"
              :key="question.id || qIdx"
              :question="question"
              :questions="questions"
              :sections="sections"
              :questionIndex="questions.findIndex(qq => qq === question)"
              :validationError="validationErrors.questions[questions.findIndex(qq => qq === question)]"
              @update:question="updateQuestion(questions.findIndex(qq => qq === question), $event)"
              @remove="removeQuestion(questions.findIndex(qq => qq === question))"
              @move="moveQuestion(questions.findIndex(qq => qq === question), $event)"
            />
            <button @click="addQuestion(section.id)" style="margin-top: 0.5em;">Add Question to {{ section.name }}</button>
          </div>
        </SectionEditor>
        <div style="margin-top:1em;text-align:center;">
          <button @click="addSectionAndOpen">+ Add Section</button>
        </div>
      </div>

      <div class="actions">
        <button @click="onSaveForm" :disabled="saving">Save Form</button>
        <button @click="cancelEdit" :disabled="saving" style="margin-left: 1rem;">Cancel</button>
        <span v-if="saveSuccess" class="success">Saved!</span>
        <span v-if="saveError" class="error">Error saving form.</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useFormBuilder } from '@/composables/useFormBuilder';
import { useFormSections } from '@/composables/useFormSections';
import FormMeta from '@/components/builder/FormMeta.vue';
import SectionEditor from '@/components/builder/SectionEditor.vue';
import QuestionEditor from '@/components/builder/QuestionEditor.vue';
import '@/main.css';


const {
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
} = useFormBuilder();

const {
  activeSectionIdx,
  addSection,
  removeSection,
  renameSection,
  openSection,
} = useFormSections(sections, questions, sectionIdCounter);

const getNextQuestionId = () => {
  if (questions.value.length === 0) {
    return 1;
  }
  const maxId = Math.max(...questions.value.map(q => q.id || 0));
  console.log('[FormBuilder.vue] getNextQuestionId called, maxId:', maxId + 1);
  return maxId + 1;
};

const addQuestion = (sectionId = null) => {
  let secId = sectionId;
  if (!secId && sections.value.length > 0) secId = sections.value[0].id;
  questions.value.push({
    id: getNextQuestionId(),
    text: '',
    question_type: 'TEXT', // default, but can be changed to 'DATE' in UI
    order: questions.value.length + 1,
    output_template: '',
    options: [],
    hidden: false,
    section_id: secId,
  });
};

const removeQuestion = idx => {
  const removedQuestion = questions.value[idx];
  const removedId = removedQuestion && removedQuestion.id !== undefined ? removedQuestion.id : null;
  questions.value.splice(idx, 1);
  if (removedId !== null) {
    questions.value.forEach(q => {
      if (q.options && Array.isArray(q.options)) {
        q.options.forEach(o => {
          if (Array.isArray(o.triggers_question)) {
            o.triggers_question = o.triggers_question.filter(tid => tid !== removedId);
          }
        });
      }
    });
  }
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

const moveSection = (idx, dir) => {
  const newIdx = idx + dir;
  if (newIdx < 0 || newIdx >= sections.value.length) return;
  const temp = sections.value[idx];
  sections.value[idx] = sections.value[newIdx];
  sections.value[newIdx] = temp;
  activeSectionIdx.value = newIdx;
};

const addSectionAndOpen = () => {
  addSection();
  openSection(sections.value.length - 1);
};


const onSaveForm = () => {
  console.debug('[FormBuilder.vue] onSaveForm called', { form, questions, sections });
  saveForm();
};

const updateQuestion = (idx, question) => {
  questions.value[idx] = question;
};

const handleSectionDragDrop = ({ from, to }) => {
  // Reorder sections array based on drag/drop
  if (typeof from !== 'number' || typeof to !== 'number' || from === to) return;
  const moved = sections.value.splice(from, 1)[0];
  sections.value.splice(to, 0, moved);
  activeSectionIdx.value = to;
};
</script>

<style scoped>
/* Existing styles retained; new drag/drop CSS could be added here if needed */
</style>