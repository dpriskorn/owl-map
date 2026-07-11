<template>
  <div id="app" class="d-flex flex-column vh-100">
    <div class="alert alert-danger alert-map" role="alert" v-if="!backendUp">
      <i class="fa fa-exclamation-triangle"></i>
      Backend is not available. Please ensure the API server is running on port 8080.
    </div>

    <div class="alert alert-primary alert-map" role="alert" v-if="state.loading">
      Found {{ state.item_count }} Wikidata items. Updating markers.
      <span class="spinner-border spinner-border-sm"></span>
    </div>

    <div class="alert alert-primary alert-map" role="alert" v-if="state.area_too_big">
      Zoom in to see Wikidata items on the map.
    </div>

    <div class="alert alert-primary alert-map" role="alert" v-if="!state.area_too_big && state.too_many_items">
      Found {{ state.item_count.toLocaleString() }} Wikidata items.<br/>
      Zoom in to see them.
    </div>

    <div class="d-flex flex-grow-1 overflow-hidden">
      <MapView
        class="flex-grow-1"
        :items="state.items"
        :current-item="state.current_item"
        :selected-items="state.selected_items"
        :current-osm="state.current_osm"
        @item-click="handleItemClick"
        @bounds-change="handleBoundsChange"
      />

      <AppSidebar class="w-25 min-width-300">
        <template v-if="state.view_edits">
          <EditPanel
            :edits="state.edits"
            :uploads-grouped-by-qid="uploadsGroupedByQid"
            :upload-state="state.upload_state"
            :upload-progress="state.upload_progress"
            :upload-error="state.upload_error"
            :changeset-comment="state.changeset_comment"
            :mock-upload="!state.user"
            @close="closeEditList"
            @upload="handleUpload"
          />
        </template>

        <template v-else-if="state.current_item">
          <ItemDetail
            :item="state.current_item"
            :wd-item="state.wd_item"
            @close="closeItem"
            @toggle-osm="handleToggleOsm"
            @zoom-marker="handleZoomMarker"
          />
        </template>

        <template v-else>
          <SearchPanel
            :hits="state.hits"
            :current-hit="state.current_hit"
            :recent-search="state.recent_search"
            @search="handleSearch"
            @visit-hit="handleVisitHit"
          />

          <ItemTypeFilter
            v-if="state.show_item_type_filter"
            :isa-ticked="state.isa_ticked"
            :item-type-hits="state.item_type_hits"
            :search-results="state.wikidata_search_results"
            :search-query="state.item_type_search"
            @toggle-isa="handleToggleIsa"
            @clear-all="clearIsaFilters"
            @update:search="state.item_type_search = $event"
          />

          <ItemList
            v-else
            :items="visibleItems"
            :show-filter="state.show_item_type_filter"
            @open-item="handleOpenItem"
            @update:showFilter="state.show_item_type_filter = $event"
          />
        </template>
      </AppSidebar>
    </div>

    <div v-if="state.edits.length && !state.view_edits" id="edit-count" class="p-2">
      <span>edits: {{ state.edits.length }}</span>
      <button class="btn btn-primary btn-sm ms-2" @click="state.view_edits = true">
        <i class="fa fa-upload"></i> save
      </button>
    </div>

    <ErrorModal
      :message="state.api_call_error_message"
      :traceback="state.api_call_error_traceback"
    />

    <ImageModal
      v-if="state.current_item"
      :item="state.current_item"
      :wd-item="state.wd_item"
    />
  </div>
</template>

<script setup>
import {ref, watch, onMounted, onUnmounted} from 'vue';
import MapView from './components/MapView.vue';
import AppSidebar from './components/AppSidebar.vue';
import SearchPanel from './components/SearchPanel.vue';
import ItemList from './components/ItemList.vue';
import ItemDetail from './components/ItemDetail.vue';
import ItemTypeFilter from './components/ItemTypeFilter.vue';
import EditPanel from './components/EditPanel.vue';
import ErrorModal from './components/ErrorModal.vue';
import ImageModal from './components/ImageModal.vue';

import {useState} from './composables/useState.js';
import {useApi} from './composables/useApi.js';
import {useEdits} from './composables/useEdits.js';

const MIN_ZOOM = parseInt(import.meta.env.VITE_MIN_ZOOM || '13', 10);

const {
  state,
  visibleItems,
  uploadsGroupedByQid,
  openItem,
  closeItem,
  clearEdits,
  setItems,
  setLoading,
  setAreaTooBig,
  setTooManyItems,
  setError,
  setUploadState,
  resetUpload,
  setHits,
  setCurrentHit,
  setWikidataDetail,
  setItemTypeHits,
  setWikidataSearchResults,
  toggleIsa,
  clearIsaFilters,
} = useState();

const api = useApi();
const {toggleEdit, buildEditList, handleUploadEvent} = useEdits();

const backendUp = ref(true);
let healthCheckInterval = null;

const checkBackendHealth = async () => {
  backendUp.value = await api.healthCheck();
};

const startHealthCheck = () => {
  checkBackendHealth();
  healthCheckInterval = setInterval(checkBackendHealth, 30000);
};

const stopHealthCheck = () => {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval);
    healthCheckInterval = null;
  }
};

// Debounce helper
let searchTimeout = null;
const debounceSearch = (query) => {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(async () => {
    if (query && query.length >= 3) {
      const results = await api.searchWikidata(query);
      setWikidataSearchResults(results);
    } else {
      setWikidataSearchResults([]);
    }
  }, 300);
};

watch(() => state.item_type_search, (newQuery) => {
  debounceSearch(newQuery);
});

// Map event handlers
const handleItemClick = async (qid, marker) => {
  openItem(qid, marker);
  const labels = await api.fetchLabels([qid]);
  if (labels[qid]) {
    setWikidataDetail(qid, labels[qid]);
  }
};

const handleBoundsChange = async (bounds, boundsArray, zoom) => {
  console.debug('handleBoundsChange', {zoom, MIN_ZOOM});
  if (zoom < MIN_ZOOM) {
    setAreaTooBig(true);
    setTooManyItems(false);
    setItems({});
    return;
  }
  setAreaTooBig(false);
  setLoading(true);
  try {
    const [itemsResponse, isaResponse] = await Promise.all([
      api.fetchItems(boundsArray),
      api.fetchIsaCounts(boundsArray),
    ]);
    setItems(itemsResponse.data.items);
    setItemTypeHits(isaResponse.data.isa_count || []);
  } catch (err) {
    setError(err.api_call_error_message, err.api_call_error_traceback);
  } finally {
    setLoading(false);
  }
};

// Search handlers
const handleSearch = async (query) => {
  try {
    const response = await api.search(query);
    setHits(response.data);
    state.recent_search = query;
  } catch (err) {
    setError(err.api_call_error_message);
  }
};

const handleVisitHit = (hit) => {
  setCurrentHit(hit);
  state.map?.flyTo([hit.lat, hit.lon], 14);
};

// Item handlers
const handleOpenItem = (qid) => {
  const item = state.items[qid];
  if (item) {
    openItem(item);
  }
};

const handleToggleOsm = (osm) => {
  if (!state.current_item) return;
  osm.selected = !osm.selected;
  toggleEdit(state.edits, state.current_item, osm);
};

const handleZoomMarker = () => {
  if (state.selected_marker) {
    state.map?.flyTo(state.selected_marker.getLatLng(), 18);
  }
};

// Edit handlers
const handleUpload = async () => {
  if (!state.edits.length) return;

  setUploadState('init');
  try {
    const editList = buildEditList(state.edits);
    const response = await api.createEditSession(state.changeset_comment, editList);
    const sessionId = response.data.session_id;

    const es = new EventSource(`${api.api_base_url}/api/1/save/${sessionId}`);
    es.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleUploadEvent(state, data);
      if (data.event === 'done' || data.type === 'done') {
        es.close();
      }
    };
    es.onerror = () => {
      setUploadState('error', {upload_error: 'EventSource error'});
      es.close();
    };
  } catch (err) {
    setUploadState('error', {upload_error: err.message});
  }
};

const closeEditList = () => {
  state.view_edits = false;
  clearEdits();
  resetUpload();
};

// Filter handlers
const handleToggleIsa = (qid) => {
  toggleIsa(qid);
};

// Lifecycle
onMounted(() => {
  startHealthCheck();
});

onUnmounted(() => {
  stopHealthCheck();
});
</script>

<style>
#app {
  overflow: hidden;
}
.min-width-300 {
  min-width: 300px;
}
</style>
