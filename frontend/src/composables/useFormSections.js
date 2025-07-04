
import { ref, watch, nextTick } from 'vue';

export function useFormSections(sections, questions, sectionIdCounter) {
  const activeSectionIdx = ref(0);

  const addSection = () => {
    sections.value.push({ id: sectionIdCounter++, name: `Section ${sections.value.length + 1}` });
  };

  const removeSection = (idx) => {
    const secId = sections.value[idx].id;
    questions.value = questions.value.filter(q => q.section_id !== secId);
    sections.value.splice(idx, 1);
  };

  const renameSection = (idx, newName) => {
    sections.value[idx].name = newName;
  };

  const openSection = (idx) => {
    activeSectionIdx.value = idx;
  };

  watch(
    () => sections.value.length,
    (len) => {
      if (len > 0) {
        nextTick(() => { activeSectionIdx.value = 0; });
      }
    },
    { immediate: true }
  );

  return {
    activeSectionIdx,
    addSection,
    removeSection,
    renameSection,
    openSection,
  };
}
