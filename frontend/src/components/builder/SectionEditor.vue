
<template>
  <div class="section-block">
    <div
      class="section-header"
      :style="{ cursor: 'pointer', background: '#f7f7f7', borderRadius: '8px', padding: '0.75em 1em', marginBottom: '0.5em', fontWeight: 'bold', fontSize: '1.1em', border: '1px solid #ddd', boxShadow: '0 1px 4px #0001' }"
      @click="$emit('toggle')"
      :aria-expanded="isOpen"
    >
      <span>{{ section.name }}</span>
      <span v-if="isOpen" style="float:right;">▼</span>
      <span v-else style="float:right;">▶</span>
    </div>
    <transition name="fade">
      <div v-show="isOpen" class="section-body" style="padding: 1em 1.5em 1.5em 1.5em; background: #fff; border-radius: 0 0 8px 8px; border: 1px solid #eee; border-top: none;">
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
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
