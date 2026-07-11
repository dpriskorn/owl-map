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
import {computed} from 'vue';

const props = defineProps({
  isaTicked: {type: Array, default: () => []},
  itemTypeHits: {type: Array, default: () => []},
  searchResults: {type: Array, default: () => []},
  searchQuery: {type: String, default: ''},
});

const emit = defineEmits(['toggle-isa', 'clear-all', 'update:search', 'clear-cache']);

const searchQuery = computed({
  get: () => props.searchQuery || '',
  set: (val) => emit('update:search', val),
});

const selectedItems = computed(() => {
  const allItems = [...props.searchResults, ...props.itemTypeHits];
  const unique = new Map();
  for (const item of allItems) {
    const qid = item.qid || item.id;
    if (props.isaTicked.includes(qid) && !unique.has(qid)) {
      unique.set(qid, {qid, label: item.label || item.qid || item.id});
    }
  }
  return Array.from(unique.values());
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
