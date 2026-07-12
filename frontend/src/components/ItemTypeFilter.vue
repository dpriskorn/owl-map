<template>
  <div class="d-flex flex-column h-100">
    <div class="p-3 flex-grow-1">
      <h6>Item type filter</h6>

      <div v-if="isaTicked.length" class="mb-2">
        <div class="input-group">
          <span class="form-control bg-primary text-white d-flex align-items-center gap-2">
            {{ selectedItems[0]?.label || selectedItems[0]?.qid }}
            <button
              type="button"
              class="btn-close btn-close-white ms-auto"
              @click.prevent="$emit('toggle-isa', selectedItems[0].qid)"
            ></button>
          </span>
        </div>
        <small class="text-muted">Press X to search for another type</small>
      </div>

      <input
        v-else
        v-model="searchQuery"
        type="text"
        class="form-control mb-2"
        placeholder="Search type..."
      >

      <div v-if="!isaTicked.length && displayHits.length" class="list-group">
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

      <div v-else-if="!isaTicked.length && searchQuery && searchQuery.length >= 3" class="text-muted small">
        No results found
      </div>
    </div>

    <div class="p-3 border-top">
      <button
        class="btn btn-sm btn-outline-danger w-100"
        @click="$emit('clear-cache')"
      >
        Clear cache
      </button>
    </div>
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
