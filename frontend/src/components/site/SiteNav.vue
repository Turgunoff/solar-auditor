<script setup>
import { useRoute } from 'vue-router'

defineProps({
  overHero: { type: Boolean, default: false },
})

const route = useRoute()
const links = [
  { to: '/how-it-works', label: 'How it works' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/projects', label: 'Projects' },
  { to: '/setup', label: 'API setup' },
  { to: '/contact', label: 'Contact' },
]
</script>

<template>
  <nav class="site-nav" :class="{ over: overHero }">
    <RouterLink to="/" class="brand">
      <span class="brand-mark" aria-hidden="true" />
      <span class="brand-name">Solar Auditor</span>
    </RouterLink>

    <div class="nav-links">
      <RouterLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="nav-link"
        :class="{ active: route.path === link.to }"
      >
        {{ link.label }}
      </RouterLink>
    </div>

    <RouterLink to="/app" class="nav-cta">Open auditor</RouterLink>
  </nav>
</template>

<style scoped>
.site-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.5rem;
  max-width: 1120px;
  margin: 0 auto;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  text-decoration: none;
  color: inherit;
}

.brand-mark {
  width: 0.9rem;
  height: 0.9rem;
  border-radius: 0.2rem;
  background: linear-gradient(135deg, #1fa87a, #e8a317);
  box-shadow: 0 0 0 3px rgba(31, 168, 122, 0.2);
}

.brand-name {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: -0.02em;
}

.over .brand-name {
  color: #f2f7f4;
}

.nav-links {
  display: none;
  gap: 1.25rem;
}

@media (min-width: 840px) {
  .nav-links {
    display: flex;
  }
}

.nav-link {
  text-decoration: none;
  color: #3d4a42;
  font-size: 0.92rem;
  font-weight: 500;
}

.over .nav-link {
  color: rgba(242, 247, 244, 0.78);
}

.nav-link.active,
.nav-link:hover {
  color: #0b3d2e;
}

.over .nav-link.active,
.over .nav-link:hover {
  color: #fff;
}

.nav-cta {
  text-decoration: none;
  background: #0b3d2e;
  color: #f4faf6;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.55rem 0.95rem;
  border-radius: 4px;
  transition: transform 0.2s ease, background 0.2s ease;
}

.over .nav-cta {
  background: #e8a317;
  color: #1a1405;
}

.nav-cta:hover {
  transform: translateY(-1px);
  background: #14664c;
}

.over .nav-cta:hover {
  background: #f0b429;
}
</style>
