
<template>
  <div class="form-section-accordion">
    <div
      class="section-header"
      @click="$emit('toggle')"
      :aria-expanded="isOpen"
    >
      <span>{{ section.name }}</span>
      <span v-if="isOpen" class="toggle-icon">▼</span>
      <span v-else class="toggle-icon">▶</span>
    </div>
    <transition name="fade">
      <div v-show="isOpen" class="section-body">
        <slot></slot>
      </div>
    </transition>
  </div>
</template>

<script setup>
  defineProps(['section', 'isOpen']);
  defineEmits(['toggle']);
</script>

<style scoped>
.section-header {
  cursor: pointer;
  background: #f7f7f7;
  border-radius: 8px;
  padding: 0.75em 1em;
  margin-bottom: 0.5em;
  font-weight: bold;
  font-size: 1.1em;
  border: 1px solid #ddd;
  box-shadow: 0 1px 4px #0001;
}

.toggle-icon {
  float: right;
}

.section-body {
  padding: 1em 1.5em 1.5em 1.5em;
  background: #fff;
  border-radius: 0 0 8px 8px;
  border: 1px solid #eee;
  border-top: none;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
