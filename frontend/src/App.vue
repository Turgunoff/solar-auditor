<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import SiteLayout from './layouts/SiteLayout.vue'

const route = useRoute()
const isApp = computed(() => route.meta.layout === 'app')
</script>

<template>
  <SiteLayout v-if="!isApp">
    <RouterView />
  </SiteLayout>
  <RouterView v-else />
</template>
