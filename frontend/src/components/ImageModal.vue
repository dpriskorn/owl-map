<template>
  <div class="modal show d-block" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ item.qid }}</h5>
          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>
        <div class="modal-body text-center">
          <img
            v-if="currentImage"
            :src="currentImage"
            class="img-fluid"
            :alt="item.qid"
          >
          <p v-else class="text-muted">No image available</p>

          <div v-if="imageList.length > 1" class="mt-2">
            <button
              v-for="(img, idx) in imageList"
              :key="idx"
              class="btn btn-sm btn-outline-secondary me-1"
              :class="{active: currentImage === img}"
              @click="currentImage = img"
            >
              {{ idx + 1 }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, computed, watch} from 'vue';

const props = defineProps({
  item: {type: Object, required: true},
  wdItem: {type: Object, default: null},
});

defineEmits(['close']);

const currentIdx = ref(0);

const imageList = computed(() => {
  return props.wdItem?.image_list || [];
});

const currentImage = computed(() => {
  return imageList.value[currentIdx.value] || null;
});

watch(() => props.item, () => {
  currentIdx.value = 0;
});
</script>
