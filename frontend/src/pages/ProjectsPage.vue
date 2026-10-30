<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { clearProjects, deleteProject, listProjects } from '../services/history'
import { assetUrl } from '../services/api'

const router = useRouter()
const items = ref(listProjects())
const count = computed(() => items.value.length)

function refresh() {
  items.value = listProjects()
}

function remove(id) {
  items.value = deleteProject(id)
}

function wipe() {
  clearProjects()
  refresh()
}

function openInApp(id) {
  router.push({ path: '/app', query: { project: id } })
}

function fmtDate(iso) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}
</script>

<template>
  <div class="page">
    <header class="head">
      <div>
        <p class="eyebrow">Workspace <span class="track-pill">Push the Frontier · Indie Track</span></p>
        <h1>Saved audits</h1>
        <p class="lead">Stored in your browser ({{ count }}). Re-open any audit in the engine.</p>
      </div>
      <div class="actions">
        <RouterLink to="/app" class="btn">New audit</RouterLink>
        <button v-if="count" type="button" class="btn ghost" @click="wipe">Clear all</button>
      </div>
    </header>

    <p v-if="!count" class="empty">
      No saved projects yet. Run an audit and it will appear here automatically.
    </p>

    <div v-else class="list">
      <article v-for="p in items" :key="p.id" class="card">
        <img :src="assetUrl(p.render_url || p.image_url)" :alt="p.label" />
        <div class="meta">
          <h2>{{ p.label }}</h2>
          <p>{{ fmtDate(p.savedAt) }}</p>
          <p class="kpis">
            {{ p.layout?.total_panels ?? '—' }} panels ·
            {{ p.analytics?.system_capacity_kw ?? '—' }} kWp ·
            ROI {{ p.analytics?.roi_years ?? 'N/A' }}y
          </p>
          <div class="row">
            <button type="button" class="btn" @click="openInApp(p.id)">Open</button>
            <button type="button" class="btn ghost" @click="remove(p.id)">Delete</button>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 3rem 1.5rem 4rem;
}

.head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.75rem;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  font-weight: 700;
  color: #1fa87a;
  margin: 0 0 0.5rem;
}

h1 {
  font-family: 'Syne', sans-serif;
  font-size: clamp(1.7rem, 3vw, 2.3rem);
  letter-spacing: -0.03em;
  color: #0b3d2e;
  margin: 0 0 0.5rem;
}

.lead {
  margin: 0;
  color: #3f5248;
}

.actions {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
}

.btn {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
  border: none;
  cursor: pointer;
  background: #0b3d2e;
  color: #f4faf6;
  font-weight: 700;
  font-size: 0.88rem;
  padding: 0.6rem 0.95rem;
  border-radius: 999px;
}

.btn.ghost {
  background: transparent;
  border: 1.5px solid rgba(11, 61, 46, 0.25);
  color: #0b3d2e;
}

.empty {
  padding: 1.5rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px dashed rgba(11, 61, 46, 0.25);
  color: #4d5c54;
}

.list {
  display: grid;
  gap: 1rem;
}

@media (min-width: 800px) {
  .list { grid-template-columns: 1fr 1fr; }
}

.card {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 0.9rem;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(11, 61, 46, 0.1);
  border-radius: 16px;
  overflow: hidden;
}

.card img {
  width: 100%;
  height: 100%;
  min-height: 120px;
  object-fit: cover;
}

.meta {
  padding: 0.85rem 0.85rem 0.95rem 0;
}

h2 {
  font-family: 'Syne', sans-serif;
  font-size: 1rem;
  margin: 0 0 0.25rem;
  color: #0b3d2e;
}

.meta p {
  margin: 0;
  font-size: 0.82rem;
  color: #6b7a72;
}

.kpis {
  margin-top: 0.45rem !important;
  color: #3f5248 !important;
  font-weight: 600;
}

.row {
  display: flex;
  gap: 0.45rem;
  margin-top: 0.75rem;
}
</style>
