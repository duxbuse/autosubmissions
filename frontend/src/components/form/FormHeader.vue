
<template>
  <div class="submission-meta" style="margin-bottom: 1.5rem;">
    <label for="client_name"><b>Client Name:</b></label>
    <input id="client_name" :value="clientName" @input="$emit('update:clientName', $event.target.value)" placeholder="Enter client name" required style="margin-bottom: 1rem; width: 100%; max-width: 400px;" />
    <label for="submission_date"><b>Date:</b></label>
    <input id="submission_date" type="date" :value="submissionDate" @input="$emit('update:submissionDate', $event.target.value)" required style="margin-bottom: 1rem; width: 100%; max-width: 220px;" />
  </div>
</template>

<script setup>
  defineProps(['clientName', 'submissionDate']);
  defineEmits(['update:clientName', 'update:submissionDate']);
</script>
