<template>
  <div v-if="warning" class="modal show d-block" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Warning</h5>
        </div>
        <div class="modal-body">
          <p class="text-danger">{{ warning.message }}</p>
          <p>This Wikidata item does not have an OSM tag (P1282) configured.</p>
          <p>You can help improve Wikidata by adding an OSM tag reference to this item.</p>
          <a :href="warning.url" target="_blank" rel="noopener noreferrer" class="btn btn-primary">
            Edit on Wikidata
          </a>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('dismiss')">Dismiss</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  warning: {type: Object, default: null},
});

defineEmits(['dismiss']);
</script>
