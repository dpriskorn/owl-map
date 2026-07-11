<template>
  <div class="p-3">
    <div class="form-check form-switch mb-3">
      <input
        id="show-filter"
        :checked="showFilter"
        type="checkbox"
        class="form-check-input"
        @change="$emit('update:showFilter', $event.target.checked)"
      >
      <label class="form-check-label" for="show-filter">
        Item type filter
      </label>
    </div>

    <div v-if="!items.length" class="text-muted">
      No items in view. Zoom out or pan the map.
    </div>

    <div class="list-group">
      <a
        v-for="item in items"
        :key="item.qid"
        class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
        href="#"
        @click.prevent="$emit('open-item', item.qid)"
      >
        <span>
          <strong>{{ item.wikidata?.label || item.qid }}</strong>
          <span class="badge bg-secondary ms-1">{{ item.qid }}</span>
        </span>
        <span v-if="item.osm" class="badge bg-success">linked</span>
      </a>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: {type: Array, default: () => []},
  showFilter: {type: Boolean, default: false},
});

defineEmits(['open-item', 'update:showFilter']);
</script>
