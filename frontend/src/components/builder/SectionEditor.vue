<template>
  <div class="section-block" ref="sectionBlock" draggable="true" @dragstart="onDragStart" @dragover.prevent @drop="onDrop">
    <div
      class="section-header"
      :aria-expanded="isOpen"
      @click="onHeaderClick"
      @dblclick="onHeaderDblClick"
    >
      <div class="section-title">
        <span v-if="!editing">{{ section.name }}</span>
        <input v-else type="text" v-model="editName" @blur="finishEditing" @keyup.enter="finishEditing" @keyup.esc="cancelEditing" />
      </div>
      <div class="header-controls">
        <slot name="header-extra" :sectionIndex="index"></slot>
        <span class="accordion-arrow">{{ isOpen ? '▼' : '▶' }}</span>
      </div>
    </div>
    <transition name="fade">
      <div v-show="isOpen" class="section-body">
        <slot></slot>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
const props = defineProps(['section','isOpen','index']);
const emit = defineEmits(['toggle', 'rename','dragdrop']);

const editing = ref(false);
const editName = ref(props.section.name);
const sectionBlock = ref(null);

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    // Wait for the section to expand before scrolling
    setTimeout(() => {
      sectionBlock.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }
});

watch(() => props.section.name, (val) => {
  if (!editing.value) editName.value = val;
});

// Drag and drop handlers
const onDragStart = (e) => {
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', String(props.index));
};

const onDrop = (e) => {
  const fromIndex = Number(e.dataTransfer.getData('text/plain'));
  const toIndex = props.index;
  if (!isNaN(fromIndex) && fromIndex !== toIndex) {
    emit('dragdrop', { from: fromIndex, to: toIndex });
  }
};

// Header click editing logic
let clickTimeout = null;
const onHeaderClick = (e) => {
  if (editing.value) return;
  if (clickTimeout) clearTimeout(clickTimeout);
  clickTimeout = setTimeout(() => {
    emit('toggle');
    clickTimeout = null;
  }, 200);
};

const onHeaderDblClick = (e) => {
  if (editing.value) return;
  if (clickTimeout) clearTimeout(clickTimeout);
  editing.value = true;
  editName.value = props.section.name;
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
.section-block {
  margin-bottom: 1em;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1em;
  cursor: pointer;
  background: #f7f7f7;
  border-radius: 8px;
  padding: 0.75em 1em;
  font-weight: bold;
  font-size: 1.1em;
  border: 1px solid #ddd;
  box-shadow: 0 1px 4px #0001;
}

.section-title {
  flex-grow: 1;
  user-select: none;
}

.section-title input {
  font-size: 1em;
  font-weight: bold;
  width: 95%;
  border: 1px solid #ccc;
  padding: 2px 5px;
  border-radius: 4px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 1.5em; /* More space between arrow and button */
}

.accordion-arrow {
  font-size: 1em; /* Adjusted size */
  cursor: pointer;
}

.section-body {
  padding: 1em 1.5em 1.5em 1.5em;
  background: #fff;
  border-radius: 0 0 8px 8px;
  border: 1px solid #eee;
  border-top: none;
  margin-top: -0.5em; /* Pulls body up to header */
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

/*
  Reset button styles from the slot.
  Using :deep() to pierce component scope.
*/
.header-controls :deep(button) {
  position: static !important;
  top: auto !important;
  right: auto !important;
  margin: 0; /* Reset margins */
}
</style>