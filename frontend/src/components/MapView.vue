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

const addMarkersToMap = (item, mapInstance) => {
  if (!item.wikidata?.markers) return;

  item.markers.forEach(markerData => {
    const marker = L.circleMarker([markerData.lat, markerData.lon], {
      radius: 5,
      color: 'blue',
    });
    marker.on('click', () => emit('item-click', item.qid, marker));
    marker.addTo(mapInstance);
    item._markers = item._markers || [];
    item._markers.push(marker);
  });
};

onMounted(() => {
  map.value = L.map('map').setView([52, 0], 8);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
  }).addTo(map.value);

  map.value.on('moveend', () => {
    const bounds = map.value.getBounds();
    const boundsArray = [
      bounds.getSouthWest().lat,
      bounds.getSouthWest().lng,
      bounds.getNorthEast().lat,
      bounds.getNorthEast().lng,
    ];
    emit('bounds-change', bounds, boundsArray);
  });

  // Initial load
  const bounds = map.value.getBounds();
  const boundsArray = [
    bounds.getSouthWest().lat,
    bounds.getSouthWest().lng,
    bounds.getNorthEast().lat,
    bounds.getNorthEast().lng,
  ];
  emit('bounds-change', bounds, boundsArray);
});

// Watch items and update markers
watch(() => props.items, (newItems) => {
  Object.values(newItems).forEach(item => {
    if (item._markers) {
      item._markers.forEach(m => m.removeFrom(map.value));
    }
    addMarkersToMap(item, map.value);
  });
}, {deep: true});

watch(() => props.currentItem, (item) => {
  if (!map.value) return;

  if (!item) return;

  if (item.markers) {
    item.markers.forEach(marker => {
      L.circleMarker([marker.lat, marker.lon], {
        radius: 20,
        color: 'orange',
      }).addTo(map.value);
    });
  }
});

defineExpose({map, flyTo: (latlng, zoom) => map.value?.flyTo(latlng, zoom)});
</script>
