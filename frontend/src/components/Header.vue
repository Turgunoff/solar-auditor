<script setup>
defineProps({
  mode: { type: String, default: 'mock' },
  models: {
    type: Object,
    default: () => ({ segmentation: 'mock', render: 'mock', agent: 'mock' }),
  },
  runProviders: {
    type: Object,
    default: null,
  },
  statusMessage: { type: String, default: '' },
})
</script>

<template>
  <div>
    <header class="eng-topbar">
      <div class="flex items-center gap-2.5">
        <RouterLink to="/" class="eng-logo" title="Back to site">★</RouterLink>
        <div class="leading-tight">
          <h1>AI Rooftop Solar Auditor</h1>
          <p>v3.4-PRO</p>
        </div>
        <span class="eng-track">Push the Frontier · Indie Track</span>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span
          class="eng-badge"
          :class="mode === 'live' ? 'eng-badge-live' : 'eng-badge-mock'"
        >
          <i />Meta SAM 3.1: {{ mode === 'live' ? 'READY' : 'MOCK' }}
        </span>
        <span class="eng-badge eng-badge-idle">
          <i />Muse Engine: {{ runProviders?.agent ? 'USED' : 'STANDBY' }}
        </span>
        <span class="eng-badge eng-badge-mode">Mode: {{ mode }}</span>
        <RouterLink to="/setup" class="eng-link">API Docs</RouterLink>
        <RouterLink to="/projects" class="eng-link">Projects</RouterLink>
      </div>
    </header>
    <div
      v-if="statusMessage && mode === 'mock'"
      class="border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800 md:px-6"
    >
      {{ statusMessage }}
      <RouterLink to="/setup" class="ml-2 font-semibold underline underline-offset-2">Details</RouterLink>
    </div>
  </div>
</template>

<style scoped>
.eng-topbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
  padding: 0.6rem 1rem;
}

@media (min-width: 768px) {
  .eng-topbar { padding-left: 1.5rem; padding-right: 1.5rem; }
}

.eng-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: #10b981;
  color: #fff;
  font-size: 15px;
}

.eng-topbar h1 {
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: #0f172a;
}

.eng-topbar p {
  font-size: 0.65rem;
  font-weight: 600;
  color: #94a3b8;
}

.eng-track {
  display: none;
  font-size: 0.7rem;
  font-weight: 700;
  color: #15803d;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 9999px;
  padding: 0.2rem 0.7rem;
}

@media (min-width: 900px) {
  .eng-track { display: inline-block; }
}

.eng-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.7rem;
  font-weight: 700;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  border-radius: 9999px;
  padding: 0.25rem 0.7rem;
  white-space: nowrap;
}

.eng-badge i {
  width: 7px;
  height: 7px;
  border-radius: 9999px;
  background: #94a3b8;
}

.eng-badge-live { border-color: #6ee7b7; background: #ecfdf5; color: #047857; }
.eng-badge-live i { background: #10b981; }
.eng-badge-mock { border-color: #67e8f9; background: #ecfeff; color: #0e7490; }
.eng-badge-mock i { background: #06b6d4; }
.eng-badge-idle { border-color: #bfdbfe; background: #eff6ff; color: #1d4ed8; }
.eng-badge-idle i { background: #3b82f6; }

.eng-badge-mode {
  border-color: #e2e8f0;
  background: #fff;
  color: #64748b;
}

.eng-link {
  font-size: 0.72rem;
  font-weight: 600;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.25rem 0.6rem;
  background: #fff;
}

.eng-link:hover { color: #0e7490; border-color: #67e8f9; }
</style>
