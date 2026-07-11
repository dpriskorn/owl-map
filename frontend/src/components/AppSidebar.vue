<template>
  <div class="app-sidebar d-flex flex-column bg-light h-100">
    <slot />
  </div>
</template>

<script setup>
</script>

<style scoped>
.app-sidebar {
  width: 320px;
  max-width: 100%;
  overflow-y: auto;
}
</style>
