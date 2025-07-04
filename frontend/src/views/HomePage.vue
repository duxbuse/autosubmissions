<template>
  <main>
    <h1>Select a Form to Begin</h1>
    <div class="form-tiles">
      <div
        v-for="form in forms"
        :key="form.id"
        class="form-tile"
        @click="goToForm(form.id)"
      >
        <h2>{{ form.name }}</h2>
        <p>{{ form.description }}</p>
      </div>
    </div>
  </main>
</template>


<script setup>
import { ref, onMounted } from 'vue';
import '../main.css';
import axios from 'axios';
import { useRouter } from 'vue-router';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const forms = ref([]);
const router = useRouter();

const fetchForms = async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/forms/`);
    forms.value = res.data;
  } catch (e) {
    forms.value = [];
  }
};

const goToForm = (id) => {
  router.push(`/form/submit/${id}`);
};

onMounted(fetchForms);
</script>

/* Styles moved to main.css for global consistency */

