<template>
  <div class="p-3">
    <h6>Item type filters</h6>

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
        <span v-if="hit.count" class="badge bg-secondary mt-1">{{ hit.count?.toLocaleString() }}</span>
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
  </div>
</template>

<script setup>
import {computed} from 'vue';

const props = defineProps({
  isaTicked: {type: Array, default: () => []},
  itemTypeHits: {type: Array, default: () => []},
  searchResults: {type: Array, default: () => []},
  searchQuery: {type: String, default: ''},
});

const emit = defineEmits(['toggle-isa', 'clear-all', 'update:search']);

const searchQuery = computed({
  get: () => props.searchQuery || '',
  set: (val) => emit('update:search', val),
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
