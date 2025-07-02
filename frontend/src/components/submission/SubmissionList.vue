
<template>
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
      @click="$emit('loadSubmission', sub)"
    >
      <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 0.5em;">{{ sub.client_name }}</div>
      <div style="font-size: 0.95em; color: #666;">Date: {{ sub.submission_date }}</div>
      <div style="font-size: 0.9em; color: #888; margin-top: 0.5em;">Submission #{{ sub.id }}</div>
    </div>
  </div>
  <div v-else-if="searchClient && searchPerformed" style="margin-top: 1rem; color: #888; font-size: 0.95em;">No submissions found.</div>
</template>

<script setup>
  import { ref, onMounted, nextTick, watch } from 'vue';

  const props = defineProps(['searchResults', 'selectedSubmissionId', 'searchClient', 'searchPerformed', 'questions', 'loading']);
  defineEmits(['loadSubmission']);

  const tilesColumn = ref(null);
  const formHeight = ref(null);

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
    [() => props.questions.length, () => props.loading],
    () => {
      nextTick(updateTilesHeight);
    },
    { immediate: false }
  );

</script>
