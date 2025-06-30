
<script setup>
import { RouterView } from 'vue-router'
import '../src/main.css';
</script>

<template>
  <header>
    <nav>
      <RouterLink to="/">Home</RouterLink> |
      <RouterLink to="/form/build/new">Form Builder</RouterLink>
    </nav>
  </header>
  <RouterView />
</template>

