<template>
  <div class="p-3">
    <h6>Item type filters</h6>

    <div v-if="isaTicked.length" class="mb-2 d-flex flex-wrap gap-1">
      <span
        v-for="item in selectedItems"
        :key="item.qid"
        class="badge bg-primary d-flex align-items-center gap-1"
      >
        {{ item.label || item.qid }}
        <button
          type="button"
          class="btn-close btn-close-white"
          style="font-size: 0.5rem;"
          @click.prevent="$emit('toggle-isa', item.qid)"
        ></button>
      </span>
    </div>

    <input
      v-model="searchQuery"
      type="text"
      class="form-control mb-2"
      placeholder="Search type..."
    >

    <div v-if="displayHits.length" class="list-group">
      <a
        v-for="hit in displayHits"
        :key="hit.qid || hit.id"
        class="list-group-item d-flex flex-column"
        href="#"
        @click.prevent="$emit('toggle-isa', hit.qid || hit.id)"
      >
        <span :class="isTicked(hit.qid || hit.id) ? 'fw-bold' : ''">
          {{ hit.label || hit.qid || hit.id }}
        </span>
        <small v-if="hit.description" class="text-muted">{{ hit.description }}</small>
      </a>
    </div>

    <div v-else-if="searchQuery && searchQuery.length >= 3" class="text-muted small">
      No results found
    </div>

    <button
      v-if="isaTicked.length"
      class="btn btn-sm btn-outline-secondary mt-2"
      @click="$emit('clear-all')"
    >
      Clear all
    </button>

    <button
      class="btn btn-sm btn-outline-danger mt-2"
      @click="$emit('clear-cache')"
    >
      Clear cache
    </button>
  </div>
</template>

<script setup>
import {computed, ref, watch} from 'vue';

const props = defineProps({
  isaTicked: {type: Array, default: () => []},
  itemTypeHits: {type: Array, default: () => []},
  searchResults: {type: Array, default: () => []},
  searchQuery: {type: String, default: ''},
});

const emit = defineEmits(['toggle-isa', 'clear-all', 'update:search', 'clear-cache']);

const selectedLabels = ref({});

watch(() => props.searchResults, (newResults) => {
  for (const item of newResults) {
    const qid = item.id || item.qid;
    if (item.label && item.label !== qid) {
      selectedLabels.value[qid] = item.label;
    }
  }
});

watch(() => props.isaTicked, (newTicked, oldTicked) => {
  for (const qid of newTicked) {
    if (!oldTicked.includes(qid)) {
      const fromSearch = props.searchResults.find(r => (r.id || r.qid) === qid);
      if (fromSearch?.label) {
        selectedLabels.value[qid] = fromSearch.label;
      }
    }
  }
}, {deep: true});

const searchQuery = computed({
  get: () => props.searchQuery || '',
  set: (val) => emit('update:search', val),
});

const selectedItems = computed(() => {
  return props.isaTicked.map(qid => ({
    qid,
    label: selectedLabels.value[qid] || qid,
  }));
});

const displayHits = computed(() => {
  if (props.searchQuery && props.searchQuery.length >= 3) {
    return props.searchResults.map(r => ({
      qid: r.id,
      label: r.label,
      description: r.description,
    }));
  }
  return props.itemTypeHits;
});

const isTicked = (qid) => props.isaTicked.includes(qid);
</script>
