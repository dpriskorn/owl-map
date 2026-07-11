<template>
  <div class="p-3">
    <h6>Item type filters</h6>

    <input
      v-model="searchQuery"
      type="text"
      class="form-control mb-2"
      placeholder="Search type..."
    >

    <div v-if="filteredHits.length" class="list-group">
      <a
        v-for="hit in filteredHits"
        :key="hit.qid"
        class="list-group-item d-flex justify-content-between align-items-center"
        href="#"
        @click.prevent="$emit('toggle-isa', hit.qid)"
      >
        <span :class="isTicked(hit.qid) ? 'fw-bold' : ''">
          {{ hit.label }}
        </span>
        <span class="badge bg-secondary">{{ hit.count?.toLocaleString() }}</span>
      </a>
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
  searchQuery: {type: String, default: ''},
});

const emit = defineEmits(['toggle-isa', 'clear-all', 'update:search']);

const searchQuery = computed({
  get: () => props.searchQuery || '',
  set: (val) => emit('update:search', val),
});

const filteredHits = computed(() => {
  if (!props.searchQuery) return props.itemTypeHits;
  const q = props.searchQuery.toLowerCase();
  return props.itemTypeHits.filter(h =>
    h.label?.toLowerCase().includes(q)
  );
});

const isTicked = (qid) => props.isaTicked.includes(qid);
</script>
