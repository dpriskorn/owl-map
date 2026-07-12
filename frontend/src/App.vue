<template>
  <div id="app" class="d-flex flex-column vh-100">
    <div class="alert alert-info alert-map" role="alert" v-if="state.loading">
      <span class="spinner-border spinner-border-sm me-2"></span>
      Loading Wikidata items...
    </div>

    <div class="alert alert-primary alert-map" role="alert" v-if="!state.loading && state.item_count > 0">
      Showing {{ state.item_count }} Wikidata items on map.
    </div>

    <div class="alert alert-primary alert-map" role="alert" v-if="state.area_too_big">
      Zoom in to see Wikidata items on the map.
    </div>

    <div class="alert alert-primary alert-map" role="alert" v-if="!state.area_too_big && state.too_many_items">
      Found {{ state.item_count.toLocaleString() }} Wikidata items.<br/>
      Zoom in to see them.
    </div>

    <div class="alert alert-danger alert-map" role="alert" v-if="state.error">
      <i class="fa fa-exclamation-triangle"></i>
      {{ state.error }}
    </div>

    <div class="d-flex flex-grow-1 overflow-hidden">
      <MapView
        class="flex-grow-1"
        :items="state.items"
        :osm-objects="state.osm_objects"
        :current-item="state.current_item"
        :selected-items="state.selected_items"
        :current-osm="state.current_osm"
        :initial-lat="mapPosition.lat"
        :initial-lon="mapPosition.lon"
        :initial-zoom="mapPosition.zoom"
        @item-click="handleItemClick"
        @osm-click="handleOsmClick"
        @bounds-change="handleBoundsChange"
        @position-change="handlePositionChange"
      />

      <AppSidebar class="w-25 min-width-300">
        <template v-if="state.current_item">
          <ItemDetail
            :item="state.current_item"
            :wd-item="state.wd_item"
            @close="closeItem"
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
            :isa-ticked="state.item_type_ticked"
            :item-type-hits="state.item_type_hits"
            :search-results="state.wikidata_search_results"
            :search-query="state.item_type_search"
            @toggle-isa="handleToggleItemType"
            @clear-all="clearItemTypeFilters"
            @update:search="state.item_type_search = $event"
            @clear-cache="api.clearAllCaches()"
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

    <P1282WarningModal
      v-if="state.p1282_warning"
      :warning="state.p1282_warning"
      @dismiss="clearP1282Warning"
    />
  </div>
</template>

<script setup>
import {ref, watch} from 'vue';
import {useRoute} from 'vue-router';
import MapView from './components/MapView.vue';
import AppSidebar from './components/AppSidebar.vue';
import SearchPanel from './components/SearchPanel.vue';
import ItemList from './components/ItemList.vue';
import ItemDetail from './components/ItemDetail.vue';
import ItemTypeFilter from './components/ItemTypeFilter.vue';
import P1282WarningModal from './components/P1282WarningModal.vue';

import {useState} from './composables/useState.js';
import {useApi} from './composables/useApi.js';

const MIN_ZOOM = parseInt(import.meta.env.VITE_MIN_ZOOM || '13', 10);

const route = useRoute();

const {
  state,
  visibleItems,
  openItem,
  closeItem,
  setItems,
  setOsmObjects,
  setLoading,
  setAreaTooBig,
  setTooManyItems,
  setError,
  setHits,
  setCurrentHit,
  setWikidataDetail,
  setWikidataSearchResults,
  toggleItemType,
  clearItemTypeFilters,
  setP1282Warning,
  clearP1282Warning,
} = useState();

const api = useApi();

if (route.query.item_type) {
  state.item_type_ticked = [route.query.item_type];
}

const mapPosition = ref({
  lat: parseFloat(route.params.lat) || parseFloat(import.meta.env.VITE_DEFAULT_LAT || '62.3913'),
  lon: parseFloat(route.params.lon) || parseFloat(import.meta.env.VITE_DEFAULT_LON || '17.3068'),
  zoom: parseInt(route.params.zoom) || parseInt(import.meta.env.VITE_DEFAULT_ZOOM || '8'),
});

const updateUrl = () => {
  const {lat, lon, zoom} = mapPosition.value;
  const itemType = state.item_type_ticked.length > 0 ? state.item_type_ticked[0] : null;
  let newUrl = `/map/${zoom}/${lat.toFixed(6)}/${lon.toFixed(6)}`;
  if (itemType) {
    newUrl += `?item_type=${itemType}`;
  }
  if (window.location.pathname + window.location.search !== newUrl) {
    window.history.replaceState(null, '', newUrl);
  }
};

const handlePositionChange = ({lat, lon, zoom}) => {
  mapPosition.value = {lat, lon, zoom};
  updateUrl();
};

let searchTimeout = null;

const debounceSearch = async (query) => {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(async () => {
    if (query && query.length >= 3) {
      try {
        const results = await api.searchWikidata(query);
        if (results.length > 0) {
          const enriched = results.map(r => ({
            id: r.id,
            label: r.label || r.id,
            description: r.description || null,
          }));
          setWikidataSearchResults(enriched);
        } else {
          setWikidataSearchResults([]);
        }
      } catch (err) {
        console.error('Search error:', err);
        setError(err.message);
        setWikidataSearchResults([]);
      }
    } else {
      setWikidataSearchResults([]);
    }
  }, 300);
};

watch(() => state.item_type_search, (newQuery) => {
  debounceSearch(newQuery);
});

const handleItemClick = async (qid, marker) => {
  const item = state.items[qid];
  if (item) {
    openItem(item, marker);
    try {
      const labels = await api.fetchLabels([qid]);
      if (labels[qid]) {
        setWikidataDetail(qid, labels[qid]);
      }
    } catch (err) {
      console.error('Error fetching labels:', err);
    }
  }
};

const handleOsmClick = async (osmId, marker) => {
  const osmObj = state.osm_objects[osmId];
  if (osmObj) {
    state.current_osm = osmObj;
    state.current_item = null;
    state.selected_marker = marker;

    if (osmObj.wikidata_qid) {
      try {
        const labels = await api.fetchLabels([osmObj.wikidata_qid]);
        if (labels[osmObj.wikidata_qid]) {
          state.wd_item = {
            qid: osmObj.wikidata_qid,
            label: labels[osmObj.wikidata_qid].label,
          };
        }
      } catch (err) {
        console.error('Error fetching labels:', err);
        state.wd_item = null;
      }
    } else {
      state.wd_item = null;
    }
  }
};

let boundsChangeTimeout = null;

const handleBoundsChange = async (bounds, boundsArray, zoom) => {
  console.debug('handleBoundsChange called', {zoom, boundsArray, item_type_ticked: state.item_type_ticked});
  if (boundsChangeTimeout) clearTimeout(boundsChangeTimeout);
  boundsChangeTimeout = setTimeout(async () => {
    console.debug('handleBoundsChange timeout fired', {item_type_ticked: state.item_type_ticked});
    if (zoom < MIN_ZOOM) {
      setAreaTooBig(true);
      setTooManyItems(false);
      setItems({});
      setOsmObjects({});
      return;
    }
    setAreaTooBig(false);
    setLoading(true);
    setError(null);

    try {
      const itemType = state.item_type_ticked.length > 0 ? state.item_type_ticked[0] : null;
      console.debug('handleBoundsChange fetching with', {itemType, boundsArray});

      const result = await api.fetchItems(boundsArray, itemType);
      const data = result.data;
      const items = data.items || {};
      const osmObjects = data.osm_objects || {};
      const warnings = data.warnings || [];

      console.debug('handleBoundsChange results', {
        wikidata: Object.keys(items).length,
        osm: Object.keys(osmObjects).length,
        warnings: warnings.length
      });

      if (warnings.length > 0) {
        for (const warning of warnings) {
          if (warning.type === 'no_p1282') {
            setP1282Warning(warning);
          }
        }
      } else {
        clearP1282Warning();
      }

      const qids = Object.keys(items);
      if (qids.length > 0) {
        try {
          const labels = await api.fetchLabels(qids);
          console.debug('handleBoundsChange labels', {labels});
          for (const qid of qids) {
            if (labels[qid]) {
              items[qid].wikidata = items[qid].wikidata || {};
              items[qid].wikidata.label = labels[qid].label;
            }
          }
        } catch (err) {
          console.error('Error fetching labels:', err);
        }
      }

      setItems(items);
      setOsmObjects(osmObjects);
    } catch (err) {
      console.error('handleBoundsChange error:', err);
      setError(err.message);
      setItems({});
      setOsmObjects({});
    } finally {
      setLoading(false);
    }
  }, 300);
};

const handleSearch = async (query) => {
  setHits([]);
  state.recent_search = query;
};

const handleVisitHit = (hit) => {
  setCurrentHit(hit);
  state.map?.flyTo([hit.lat, hit.lon], 14);
};

const handleOpenItem = (qid) => {
  const item = state.items[qid];
  if (item) {
    openItem(item);
  }
};

const handleZoomMarker = () => {
  if (state.selected_marker) {
    state.map?.flyTo(state.selected_marker.getLatLng(), 18);
  }
};

const handleToggleItemType = (qid) => {
  toggleItemType(qid);
  state.item_type_search = '';
  updateUrl();
};
</script>

<style>
#app {
  overflow: hidden;
}
.min-width-300 {
  min-width: 300px;
}
</style>
