
<template>
  <div>
    <label v-for="opt in options" :key="opt.id">
      <input
        type="checkbox"
        :value="opt.text"
        :checked="modelValue && modelValue.includes(opt.text)"
        @change="onChange($event, opt.text)"
      />
      {{ opt.text }}
    </label>
  </div>
</template>

<script setup>
  const props = defineProps(['modelValue', 'options', 'id']);
  const emit = defineEmits(['update:modelValue']);

  const onChange = (e, val) => {
    let arr = Array.isArray(props.modelValue) ? [...props.modelValue] : [];
    if (e.target.checked && !arr.includes(val)) arr.push(val);
    else if (!e.target.checked) arr = arr.filter(v => v !== val);
    emit('update:modelValue', arr);
  };
</script>
