<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import SiteNav from '../components/site/SiteNav.vue'
import SiteFooter from '../components/site/SiteFooter.vue'

const route = useRoute()
const isHome = computed(() => route.path === '/')
</script>

<template>
  <div class="site-shell" :class="{ home: isHome }">
    <header class="top" :class="{ over: isHome }">
      <SiteNav :over-hero="isHome" />
    </header>
    <main>
      <slot />
    </main>
    <SiteFooter />
  </div>
</template>

<style scoped>
.site-shell {
  min-height: 100vh;
  background: #e8efe9;
  color: #14201b;
  font-family: 'Manrope', sans-serif;
}

.site-shell.home {
  background: #07140f;
  color: #f2f7f4;
}

.top {
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(14px);
  background: rgba(232, 239, 233, 0.88);
  border-bottom: 1px solid rgba(11, 61, 46, 0.08);
}

.top.over {
  background: rgba(7, 20, 15, 0.35);
  border-bottom-color: rgba(255, 255, 255, 0.08);
}
</style>
