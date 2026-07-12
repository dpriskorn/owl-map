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
  osmObjects: {type: Object, default: () => ({})},
  currentItem: {type: Object, default: null},
  selectedItems: {type: Object, default: () => ({})},
  currentOsm: {type: Object, default: null},
  initialLat: {type: Number, default: null},
  initialLon: {type: Number, default: null},
  initialZoom: {type: Number, default: null},
});

const emit = defineEmits(['item-click', 'osm-click', 'bounds-change', 'position-change']);

const mapEl = ref(null);
const map = ref(null);
const currentHit = ref(null);
const markerMap = new Map();
const osmMarkerMap = new Map();

const MARKER_COLORS = {
  wikidata_matched: '#28a745',
  wikidata_only: '#007bff',
  osm_matched: '#fd7e14',
  osm_only: '#dc3545',
};

const getMarkerColor = (item) => {
  if (item.match_status === 'matched') {
    return MARKER_COLORS.wikidata_matched;
  }
  return MARKER_COLORS.wikidata_only;
};

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

  const color = getMarkerColor(item);
  const markersList = [];
  markers.forEach(markerData => {
    const marker = L.circleMarker([markerData.lat, markerData.lon], {
      radius: 5,
      color: color,
    });
    marker.on('click', () => emit('item-click', item.qid, marker));
    marker.addTo(mapInstance);
    markersList.push(marker);
  });
  markerMap.set(item.qid, markersList);
};

const addOsmMarkersToMap = (osmObj, mapInstance) => {
  const markers = osmObj.markers;
  if (!markers || markers.length === 0) {
    console.debug('addOsmMarkersToMap: no markers for OSM object', {osm_id: osmObj.osm_id});
    return;
  }
  if (osmMarkerMap.has(osmObj.osm_id)) {
    console.debug('addOsmMarkersToMap: already has markers for', {osm_id: osmObj.osm_id});
    return;
  }

  const color = MARKER_COLORS.osm_only;
  const markersList = [];
  markers.forEach(markerData => {
    const marker = L.circleMarker([markerData.lat, markerData.lon], {
      radius: 5,
      color: color,
    });
    marker.on('click', () => emit('osm-click', osmObj.osm_id, marker));
    marker.addTo(mapInstance);
    markersList.push(marker);
  });
  osmMarkerMap.set(osmObj.osm_id, markersList);
};

const removeMarkersForItem = (qid) => {
  const markers = markerMap.get(qid);
  if (markers) {
    markers.forEach(m => m.removeFrom(map.value));
    markerMap.delete(qid);
  }
};

const removeOsmMarkersForItem = (osmId) => {
  const markers = osmMarkerMap.get(osmId);
  if (markers) {
    markers.forEach(m => m.removeFrom(map.value));
    osmMarkerMap.delete(osmId);
  }
};

const DEFAULT_LAT = parseFloat(import.meta.env.VITE_DEFAULT_LAT || '62.3913');
const DEFAULT_LON = parseFloat(import.meta.env.VITE_DEFAULT_LON || '17.3068');
const DEFAULT_ZOOM = parseInt(import.meta.env.VITE_DEFAULT_ZOOM || '8', 10);

let ignoreNextMoveend = false;

onMounted(() => {
  const lat = props.initialLat ?? DEFAULT_LAT;
  const lon = props.initialLon ?? DEFAULT_LON;
  const zoom = props.initialZoom ?? DEFAULT_ZOOM;

  map.value = L.map('map').setView([lat, lon], zoom);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
  }).addTo(map.value);

  map.value.on('moveend', () => {
    if (ignoreNextMoveend) {
      ignoreNextMoveend = false;
      return;
    }
    const center = map.value.getCenter();
    const zoom = map.value.getZoom();
    const bounds = map.value.getBounds();
    console.debug('MapView bounds-change', {zoom, center});
    const boundsArray = [
      bounds.getSouthWest().lat,
      bounds.getSouthWest().lng,
      bounds.getNorthEast().lat,
      bounds.getNorthEast().lng,
    ];
    emit('bounds-change', bounds, boundsArray, zoom);
    emit('position-change', {lat: center.lat, lon: center.lng, zoom});
  });

  // Initial load
  const bounds = map.value.getBounds();
  const boundsArray = [
    bounds.getSouthWest().lat,
    bounds.getSouthWest().lng,
    bounds.getNorthEast().lat,
    bounds.getNorthEast().lng,
  ];
  emit('bounds-change', bounds, boundsArray, zoom);
  emit('position-change', {lat, lon, zoom});
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

watch(() => props.osmObjects, (newOsms, oldOsms) => {
  console.debug('MapView OSM objects changed', {
    newKeys: Object.keys(newOsms || {}),
    oldKeys: Object.keys(oldOsms || {}),
  });
  if (!map.value) {
    console.debug('MapView map not ready yet');
    return;
  }
  const currentOsmIds = new Set(Object.keys(newOsms || {}));
  for (const [osmId] of osmMarkerMap) {
    if (!currentOsmIds.has(osmId)) {
      removeOsmMarkersForItem(osmId);
    }
  }
  Object.values(newOsms || {}).forEach(osmObj => {
    addOsmMarkersToMap(osmObj, map.value);
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

const flyTo = (lat, lon, zoom) => {
  if (map.value) {
    ignoreNextMoveend = true;
    map.value.flyTo([lat, lon], zoom);
  }
};

defineExpose({map, flyTo});
</script>
