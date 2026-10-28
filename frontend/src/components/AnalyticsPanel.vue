<script setup>
defineProps({
  result: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['view-render', 'download-pdf'])

function fmt(n, digits = 1) {
  if (n == null || Number.isNaN(n)) return '—'
  return Number(n).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  })
}
</script>

<template>
  <aside class="card flex flex-col gap-4 p-4">
    <div>
      <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-500">Analytics</h2>
      <p class="mt-1 text-xs text-slate-500">Layout-engine estimates · not a bankable report</p>
    </div>

    <div v-if="loading" class="space-y-3">
      <div class="h-14 animate-pulse rounded-lg bg-slate-200" />
      <div class="h-14 animate-pulse rounded-lg bg-slate-200" />
      <div class="h-14 animate-pulse rounded-lg bg-slate-200" />
    </div>

    <template v-else-if="result">
      <div class="grid grid-cols-1 gap-3">
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-[11px] uppercase tracking-wide text-slate-500">System Capacity</div>
          <div class="mt-1 text-2xl font-bold text-cyan-700">
            {{ fmt(result.analytics.system_capacity_kw, 2) }}
            <span class="text-sm font-medium text-slate-500">kWp</span>
          </div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-[11px] uppercase tracking-wide text-slate-500">Est. Annual Gen</div>
          <div class="mt-1 text-2xl font-bold text-emerald-700">
            {{ fmt(result.analytics.annual_generation_kwh, 0) }}
            <span class="text-sm font-medium text-slate-500">kWh</span>
          </div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div class="text-[11px] uppercase tracking-wide text-slate-500">Est. ROI</div>
          <div class="mt-1 text-2xl font-bold text-slate-900">
            {{ result.analytics.roi_years == null ? 'N/A' : fmt(result.analytics.roi_years, 1) }}
            <span v-if="result.analytics.roi_years != null" class="text-sm font-medium text-slate-500">Years</span>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 text-sm">
          <div class="rounded-lg border border-slate-200 p-2.5">
            <div class="text-[11px] text-slate-500">Cost</div>
            <div class="font-semibold">${{ fmt(result.analytics.estimated_cost_usd, 0) }}</div>
          </div>
          <div class="rounded-lg border border-slate-200 p-2.5">
            <div class="text-[11px] text-slate-500">Savings / yr</div>
            <div class="font-semibold">${{ fmt(result.analytics.annual_savings_usd, 0) }}</div>
          </div>
          <div class="rounded-lg border border-slate-200 p-2.5">
            <div class="text-[11px] text-slate-500">Panels (sun face)</div>
            <div class="font-semibold">{{ result.layout.total_panels }}</div>
          </div>
          <div class="rounded-lg border border-slate-200 p-2.5">
            <div class="text-[11px] text-slate-500">Usable area</div>
            <div class="font-semibold">{{ fmt(result.analytics.usable_area_m2, 1) }} m²</div>
          </div>
          <div class="rounded-lg border border-slate-200 p-2.5 col-span-2">
            <div class="text-[11px] text-slate-500">Module size</div>
            <div class="font-semibold">1.7 × 1.0 m · 400 W</div>
            <div class="mt-0.5 text-[10px] text-slate-500">
              {{ result.layout.total_panels }} × 1.7 m² ≈
              {{ fmt(result.layout.total_panels * 1.7, 0) }} m² glass
              <span v-if="result.analytics.usable_area_m2">
                / {{ fmt(result.analytics.usable_area_m2, 0) }} m² usable
                ({{ fmt((result.layout.total_panels * 1.7 / result.analytics.usable_area_m2) * 100, 0) }}%)
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-amber-200 bg-amber-50 p-3">
        <div class="text-[11px] uppercase tracking-wide text-amber-700">Disclaimer</div>
        <p class="mt-1 text-[11px] leading-relaxed text-amber-800">
          Demo feasibility only. kWh / ROI use fixed sun-hours &amp; tariff. Muse is concept
          art — trust <span class="text-cyan-700">Layout (engine)</span> + panel count here
          for the BOM sketch. Confirm on site before procurement.
        </p>
      </div>

      <div class="rounded-lg border border-slate-200 bg-slate-100 p-3">
        <div class="text-[11px] uppercase tracking-wide text-slate-500">Feasibility notes</div>
        <p class="mt-1 text-xs leading-relaxed text-slate-600">
          {{ result.analytics.agent_summary }}
        </p>
      </div>

      <div class="mt-auto flex flex-col gap-2">
        <button class="btn btn-primary w-full" @click="$emit('view-render')">
          View layout / 3D
        </button>
        <button class="btn btn-ghost w-full" @click="$emit('download-pdf')">
          Download PDF Report
        </button>
      </div>
    </template>

    <p v-else class="text-sm text-slate-500">
      Run an audit to see capacity, generation, and payback estimates.
    </p>
  </aside>
</template>
