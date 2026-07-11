<template>
  <div class="p-3">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">Upload to OSM</h5>
      <button class="btn-close" @click="$emit('close')"></button>
    </div>

    <div v-if="mockUpload" class="alert alert-danger">
      <i class="fa fa-exclamation-triangle"></i>
      Mock mode - changes won't be saved to OpenStreetMap.
    </div>
    <div v-else class="alert alert-info">
      <i class="fa fa-info-circle"></i>
      Editing is live - changes will be uploaded to OpenStreetMap.
    </div>

    <p>
      {{ edits.length }} {{ edits.length === 1 ? 'edit' : 'edits' }} to upload
    </p>

    <form @submit.prevent="handleUpload">
      <div class="mb-3">
        <label for="comment" class="form-label">Changeset comment</label>
        <input
          id="comment"
          v-model="localComment"
          type="text"
          class="form-control"
          :disabled="isUploading"
        >
      </div>

      <button
        type="submit"
        class="btn btn-primary w-100"
        :disabled="!edits.length || isUploading"
      >
        <span v-if="!uploadState">Upload to OSM</span>
        <span v-else-if="uploadState === 'init'">Starting...</span>
        <span v-else-if="uploadState === 'uploading'">
          Uploading... {{ uploadProgress.toFixed(0) }}%
        </span>
        <span v-else-if="uploadState === 'closing'">Closing...</span>
        <span v-else-if="uploadState === 'done'" class="text-success">Done!</span>
        <span v-else-if="uploadState === 'auth-fail'">
          <a href="/login">Login required</a>
        </span>
        <span v-else-if="uploadState === 'changeset-error'" class="text-danger">
          Error: {{ uploadError }}
        </span>
      </button>
    </form>

    <div v-if="uploadState === 'auth-fail'" class="alert alert-danger mt-2">
      Authentication failed. <a href="/login">Click to login</a>.
    </div>

    <div v-if="uploadsGroupedByQid.length" class="mt-3">
      <h6>Edits by item:</h6>
      <div v-for="group in uploadsGroupedByQid" :key="group.qid" class="mb-2">
        <strong>{{ group.wikidata?.label || group.qid }}</strong>
        <span class="badge bg-secondary ms-1">{{ group.osm.length }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, computed} from 'vue';

const props = defineProps({
  edits: {type: Array, default: () => []},
  uploadsGroupedByQid: {type: Array, default: () => []},
  uploadState: {type: String, default: null},
  uploadProgress: {type: Number, default: 0},
  uploadError: {type: String, default: null},
  changesetComment: {type: String, default: '+wikidata'},
  mockUpload: {type: Boolean, default: false},
});

const emit = defineEmits(['close', 'upload']);

const localComment = ref(props.changesetComment);

const isUploading = computed(() => {
  return props.uploadState &&
    props.uploadState !== 'done' &&
    props.uploadState !== 'error';
});

const handleUpload = () => {
  emit('upload', localComment.value);
};
</script>
