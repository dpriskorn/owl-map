<template>
  <div class="p-3">
    <button class="btn btn-outline-secondary mb-3" @click="$emit('close')">
      <i class="fa fa-arrow-left"></i> Back
    </button>

    <h4>{{ wdItem?.label || item.qid }}</h4>
    <p v-if="wdItem?.description" class="text-muted">{{ wdItem.description }}</p>

    <div v-if="wdItem?.image_list?.length" class="mb-3">
      <img
        :src="`/commons/${wdItem.image_list[0]}`"
        class="img-fluid rounded"
        alt="Item image"
      >
    </div>

    <div v-if="item.nearby?.length" class="mb-3">
      <h6>Nearby OSM objects:</h6>
      <div class="list-group">
        <div
          v-for="osm in item.nearby"
          :key="osm.identifier"
          class="list-group-item"
        >
          <div class="form-check">
            <input
              :id="'osm-' + osm.identifier"
              type="checkbox"
              :checked="osm.selected"
              class="form-check-input"
              @change="$emit('toggle-osm', osm)"
            >
            <label :for="'osm-' + osm.identifier" class="form-check-label">
              <strong>{{ osm.name || osm.identifier }}</strong>
              <span class="text-muted ms-1">{{ osm.identifier }}</span>
            </label>
          </div>
          <div v-if="osm.tags" class="mt-1">
            <span
              v-for="(value, key) in osm.tags"
              :key="key"
              class="badge bg-light text-dark me-1"
            >
              {{ key }}={{ value }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="wdItem?.isa_list?.length" class="mb-3">
      <h6>Types:</h6>
      <span
        v-for="isa in wdItem.isa_list"
        :key="isa.qid"
        class="badge bg-info me-1"
      >
        {{ isa.label || isa.qid }}
      </span>
    </div>

    <div class="mt-3">
      <a :href="'https://www.wikidata.org/wiki/' + item.qid" target="_blank" class="btn btn-sm btn-outline-primary">
        <i class="fa fa-external-link"></i> Wikidata
      </a>
    </div>
  </div>
</template>

<script setup>
defineProps({
  item: {type: Object, required: true},
  wdItem: {type: Object, default: null},
});

defineEmits(['close', 'toggle-osm', 'zoom-marker']);
</script>
