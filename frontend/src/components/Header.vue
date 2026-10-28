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
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white/80 px-4 py-3 md:px-6">
      <div class="flex items-center gap-3">
        <RouterLink to="/" class="text-xs font-semibold text-slate-500 hover:text-cyan-700">
          ← Site
        </RouterLink>
        <div>
          <h1 class="text-lg font-bold tracking-tight text-slate-900 md:text-xl">
            Solar Auditor
          </h1>
          <p class="text-xs text-slate-500">AI Rooftop Solar Auditor &amp; Engineering Engine</p>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span
          class="rounded-full border px-2.5 py-1 text-xs font-semibold"
          :class="mode === 'live'
            ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
            : 'border-cyan-300 bg-cyan-50 text-cyan-700'"
        >
          SAM:
          {{
            runProviders?.segmentation
              || (models.segmentation === 'mock' ? 'mock' : models.segmentation)
          }}
        </span>
        <span
          v-if="runProviders?.render"
          class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-600"
        >
          Render: {{ runProviders.render }}
        </span>
        <span class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-600">
          Mode: {{ mode }}
        </span>
        <RouterLink
          to="/setup"
          class="text-xs text-slate-500 underline-offset-2 hover:text-cyan-700 hover:underline"
        >
          API setup
        </RouterLink>
        <RouterLink
          to="/projects"
          class="text-xs text-slate-500 underline-offset-2 hover:text-cyan-700 hover:underline"
        >
          Projects
        </RouterLink>
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
