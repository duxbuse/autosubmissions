
<template>
  <div class="section-block">
    <div
      class="section-header"
      :style="{ cursor: 'pointer', background: '#f7f7f7', borderRadius: '8px', padding: '0.75em 1em', marginBottom: '0.5em', fontWeight: 'bold', fontSize: '1.1em', border: '1px solid #ddd', boxShadow: '0 1px 4px #0001' }"
      :aria-expanded="isOpen"
      @click="onHeaderClick"
      @dblclick="onHeaderDblClick"
    >
      <span v-if="!editing" style="user-select: none;">{{ section.name }}</span>
      <input v-else type="text" v-model="editName" @blur="finishEditing" @keyup.enter="finishEditing" @keyup.esc="cancelEditing" style="font-size:1em; font-weight:bold; width: 60%;" />
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
import { ref, watch } from 'vue';
const props = defineProps(['section', 'isOpen']);
const emit = defineEmits(['toggle', 'rename']);

const editing = ref(false);
const editName = ref(props.section.name);

watch(() => props.section.name, (val) => {
  if (!editing.value) editName.value = val;
});
// Handle click and double click on the whole header
let clickTimeout = null;
const onHeaderClick = (e) => {
  // Prevent click if editing
  if (editing.value) return;
  // Delay to distinguish single from double click
  if (clickTimeout) clearTimeout(clickTimeout);
  clickTimeout = setTimeout(() => {
    emit('toggle');
    clickTimeout = null;
  }, 200);
};

const onHeaderDblClick = (e) => {
  // Prevent double click if already editing
  if (editing.value) return;
  if (clickTimeout) clearTimeout(clickTimeout);
  editing.value = true;
  editName.value = props.section.name;
  // Optionally, focus input after next tick
};

const startEditing = (e) => {
  editing.value = true;
  editName.value = props.section.name;
  e.stopPropagation();
};
const finishEditing = () => {
  editing.value = false;
  if (editName.value.trim() && editName.value !== props.section.name) {
    emit('rename', editName.value.trim());
  }
};
const cancelEditing = () => {
  editing.value = false;
  editName.value = props.section.name;
};
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
