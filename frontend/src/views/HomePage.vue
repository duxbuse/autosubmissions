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

<style scoped>
.form-tiles {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  margin-top: 2rem;
}
.form-tile {
  background: #f5f7fa;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  padding: 2rem 2.5rem;
  min-width: 220px;
  max-width: 320px;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
  border: 1px solid #e0e0e0;
}
.form-tile:hover {
  box-shadow: 0 6px 18px rgba(0,0,0,0.13);
  transform: translateY(-4px) scale(1.03);
  border-color: #b3b3ff;
}
.form-tile h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.3rem;
  color: #3a3a6a;
}
.form-tile p {
  color: #666;
  margin: 0;
}
</style>

