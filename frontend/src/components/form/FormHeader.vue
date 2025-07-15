
<template>
  <div class="submission-meta">
    <div class="name-fields">
      <div class="field">
        <label for="client_honorific"><b>Honorific:</b></label>
        <select 
          id="client_honorific" 
          :value="clientHonorific" 
          @change="$emit('update:clientHonorific', $event.target.value)"
          required
        >
          <option value="">-- Select --</option>
          <option value="MR">Mr</option>
          <option value="MRS">Mrs</option>
          <option value="MS">Ms</option>
          <option value="DR">Dr</option>
          <option value="HON">Hon</option>
        </select>
      </div>

      <div class="field">
        <label for="client_first_name"><b>First Name:</b></label>
        <input 
          id="client_first_name" 
          :value="clientFirstName" 
          @input="updateName"
          placeholder="Enter first name" 
          required 
        />
      </div>

      <div class="field">
        <label for="client_surname"><b>Surname:</b></label>
        <input 
          id="client_surname" 
          :value="clientSurname" 
          @input="updateName"
          placeholder="Enter surname" 
          required 
        />
      </div>
    </div>

    <div class="field">
      <label for="submission_date"><b>Date:</b></label>
      <input 
        id="submission_date" 
        type="date" 
        :value="submissionDate" 
        @input="$emit('update:submissionDate', $event.target.value)" 
        required 
      />
    </div>
  </div>
</template>

<script setup>
const props = defineProps(['clientHonorific', 'clientFirstName', 'clientSurname', 'submissionDate']);
const emit = defineEmits(['update:clientHonorific', 'update:clientFirstName', 'update:clientSurname', 'update:submissionDate']);

function updateName(e) {
  const id = e.target.id;
  if (id === 'client_first_name') {
    emit('update:clientFirstName', e.target.value);
  } else if (id === 'client_surname') {
    emit('update:clientSurname', e.target.value);
  }
}
</script>

<style scoped>
.submission-meta {
  margin-bottom: 1.5rem;
}

.name-fields {
  display: grid;
  grid-template-columns: auto 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

input, select {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  width: 100%;
}

select {
  min-width: 120px;
}

input[type="date"] {
  max-width: 220px;
}
</style>
