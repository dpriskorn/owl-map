<template>
  <div v-if="message" class="modal show d-block" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Error</h5>
          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>
        <div class="modal-body">
          <p class="text-danger">{{ message }}</p>
          <pre v-if="traceback" class="text-muted small">{{ traceback }}</pre>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  message: {type: String, default: null},
  traceback: {type: String, default: null},
});

defineEmits(['close']);
</script>
