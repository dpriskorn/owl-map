<template>
  <div class="p-3">
    <form @submit.prevent="$emit('search', searchText)">
      <div class="input-group mb-2">
        <input
          v-model="searchText"
          type="text"
          class="form-control"
          placeholder="Search place..."
        >
        <button type="submit" class="btn btn-primary">
          <i class="fa fa-search"></i>
        </button>
      </div>
    </form>

    <p v-if="recentSearch" class="text-muted small mb-2">
      Searching for "{{ recentSearch }}", found {{ hits.length }} places.
    </p>

    <div v-if="hits.length" class="list-group">
      <a
        v-for="hit in hits"
        :key="hit.identifier"
        class="list-group-item list-group-item-action"
        :class="{active: hit === currentHit}"
        href="#"
        @click.prevent="$emit('visit-hit', hit)"
      >
        {{ hit.name }}
        <span class="badge bg-info">{{ hit.label }}</span>
      </a>
    </div>

    <div v-if="hits.length === 1" class="alert alert-info mt-2 small">
      <i class="fa fa-info-circle"></i>
      One search result. Click to continue.
    </div>
  </div>
</template>

<script setup>
import {ref} from 'vue';

defineProps({
  hits: {type: Array, default: () => []},
  currentHit: {type: Object, default: null},
  recentSearch: {type: String, default: null},
});

defineEmits(['search', 'visit-hit']);

const searchText = ref('');
</script>
