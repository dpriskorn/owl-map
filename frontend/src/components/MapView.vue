<template>
  <div id="map-container" class="position-relative h-100">
    <div id="map" ref="mapEl" class="h-100"></div>

    <button
      v-if="currentHit"
      id="select-area-btn"
      type="button"
      class="btn btn-primary btn-lg position-absolute top-0 start-50 translate-middle-x mt-2"
      @click="$emit('item-click', currentHit.qid)"
    >
      Select this area
    </button>
  </div>
</template>

<script setup>
import {ref, onMounted, watch} from 'vue';
import L from 'leaflet';
import 'leaflet-extra-markers';

const props = defineProps({
  items: {type: Object, default: () => ({})},
  currentItem: {type: Object, default: null},
  selectedItems: {type: Object, default: () => ({})},
  currentOsm: {type: Object, default: null},
});

const emit = defineEmits(['item-click', 'bounds-change']);

const mapEl = ref(null);
const map = ref(null);
const currentHit = ref(null);
const markerMap = new Map();

const addMarkersToMap = (item, mapInstance) => {
  console.debug('addMarkersToMap called', {item, hasQid: !!item.qid, hasMarkers: !!item.markers, hasWikidataMarkers: !!item.wikidata?.markers});
  const markers = item.markers || item.wikidata?.markers;
  if (!markers) {
    console.debug('addMarkersToMap: no markers found for item', {item});
    return;
  }
  if (markerMap.has(item.qid)) {
    console.debug('addMarkersToMap: already has markers for', {qid: item.qid});
    return;
  }

  const markersList = [];
  markers.forEach(markerData => {
    const marker = L.circleMarker([markerData.lat, markerData.lon], {
      radius: 5,
      color: 'blue',
    });
    marker.on('click', () => emit('item-click', item.qid, marker));
    marker.addTo(mapInstance);
    markersList.push(marker);
  });
  markerMap.set(item.qid, markersList);
};

const removeMarkersForItem = (qid) => {
  const markers = markerMap.get(qid);
  if (markers) {
    markers.forEach(m => m.removeFrom(map.value));
    markerMap.delete(qid);
  }
};

const DEFAULT_LAT = parseFloat(import.meta.env.VITE_DEFAULT_LAT || '62.3913');
const DEFAULT_LON = parseFloat(import.meta.env.VITE_DEFAULT_LON || '17.3068');
const DEFAULT_ZOOM = parseInt(import.meta.env.VITE_DEFAULT_ZOOM || '8', 10);

onMounted(() => {
  map.value = L.map('map').setView([DEFAULT_LAT, DEFAULT_LON], DEFAULT_ZOOM);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
  }).addTo(map.value);

  map.value.on('moveend', () => {
    const bounds = map.value.getBounds();
    const zoom = map.value.getZoom();
    console.debug('MapView bounds-change', {zoom});
    const boundsArray = [
      bounds.getSouthWest().lat,
      bounds.getSouthWest().lng,
      bounds.getNorthEast().lat,
      bounds.getNorthEast().lng,
    ];
    emit('bounds-change', bounds, boundsArray, zoom);
  });

  // Initial load
  const bounds = map.value.getBounds();
  const zoom = map.value.getZoom();
  const boundsArray = [
    bounds.getSouthWest().lat,
    bounds.getSouthWest().lng,
    bounds.getNorthEast().lat,
    bounds.getNorthEast().lng,
  ];
  emit('bounds-change', bounds, boundsArray, zoom);
});

// Watch items and update markers
watch(() => props.items, (newItems, oldItems) => {
  console.debug('MapView items changed', {
    newItems,
    oldItems,
    newKeys: Object.keys(newItems || {}),
    oldKeys: Object.keys(oldItems || {}),
    sameRef: newItems === oldItems
  });
  if (!map.value) {
    console.debug('MapView map not ready yet');
    return;
  }
  if (!newItems || Object.keys(newItems).length === 0) {
    console.debug('MapView: no items to display');
    return;
  }
  const currentQids = new Set(Object.keys(newItems));
  for (const [qid] of markerMap) {
    if (!currentQids.has(qid)) {
      removeMarkersForItem(qid);
    }
  }
  Object.values(newItems).forEach(item => {
    addMarkersToMap(item, map.value);
  });
}, {deep: true});

watch(() => props.currentItem, (item) => {
  if (!map.value) return;

  if (!item) return;

  const markers = item.markers || item.wikidata?.markers;
  if (markers) {
    markers.forEach(marker => {
      L.circleMarker([marker.lat, marker.lon], {
        radius: 20,
        color: 'orange',
      }).addTo(map.value);
    });
  }
});

defineExpose({map, flyTo: (latlng, zoom) => map.value?.flyTo(latlng, zoom)});
</script>
