<script setup>
import { ref } from 'vue'

const props = defineProps({
  result: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  defaults: { type: Object, default: null },
})

const emit = defineEmits(['view-render', 'download-pdf', 'apply-assumptions'])

const formOpen = ref(false)
const form = ref(null)

function openForm() {
  if (form.value || !props.defaults) {
    formOpen.value = !formOpen.value
    return
  }
  form.value = {
    panel_w: Math.round(props.defaults.panel_kw * 1000),
    panel_width_m: props.defaults.panel_width_m,
    panel_height_m: props.defaults.panel_height_m,
    cost_per_kw_usd: props.defaults.cost_per_kw_usd,
    tariff_per_kwh_usd: props.defaults.tariff_per_kwh_usd,
    peak_sun_hours: props.defaults.peak_sun_hours,
    grid_type: 'ongrid',
    battery_kwh: 0,
    battery_price_per_kwh_usd: props.defaults.battery_price_per_kwh_usd,
  }
  formOpen.value = true
}

function applyForm() {
  if (!form.value) return
  emit('apply-assumptions', {
    panel_kw: form.value.panel_w / 1000,
    panel_width_m: +form.value.panel_width_m,
    panel_height_m: +form.value.panel_height_m,
    cost_per_kw_usd: +form.value.cost_per_kw_usd,
    tariff_per_kwh_usd: +form.value.tariff_per_kwh_usd,
    peak_sun_hours: +form.value.peak_sun_hours,
    grid_type: form.value.grid_type,
    battery_kwh: +form.value.battery_kwh || 0,
    battery_price_per_kwh_usd: +form.value.battery_price_per_kwh_usd,
  })
}

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
            <div v-if="result.analytics.grid_type && result.analytics.grid_type !== 'ongrid'" class="mt-1 text-[10px] font-semibold text-slate-700">
              Off-grid{{ result.analytics.battery_kwh ? ` · ${result.analytics.battery_kwh} kWh battery ($${fmt(result.analytics.battery_cost_usd, 0)})` : '' }}
            </div>
            <div v-else-if="result.analytics.battery_kwh" class="mt-1 text-[10px] font-semibold text-slate-700">
              + {{ result.analytics.battery_kwh }} kWh battery (${{ fmt(result.analytics.battery_cost_usd, 0) }})
            </div>
          </div>
        </div>

        <div class="rounded-lg border border-slate-200 p-2.5 col-span-2">
          <button
            class="flex w-full items-center justify-between text-[11px] font-bold uppercase tracking-wide text-slate-900"
            type="button"
            @click="openForm"
          >
            Estimate settings
            <span class="font-semibold normal-case text-cyan-700">{{ formOpen ? 'Hide' : 'Edit' }}</span>
          </button>
          <div v-if="formOpen && form" class="mt-2 grid grid-cols-2 gap-2 text-[11px]">
            <label class="flex flex-col gap-1 text-slate-500">Panel, W
              <input v-model.number="form.panel_w" type="number" min="1" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-800" />
            </label>
            <label class="flex flex-col gap-1 text-slate-500">Cost, $/kW
              <input v-model.number="form.cost_per_kw_usd" type="number" min="0" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-800" />
            </label>
            <label class="flex flex-col gap-1 text-slate-500">Panel W, m
              <input v-model.number="form.panel_width_m" type="number" step="0.1" min="0.1" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-800" />
            </label>
            <label class="flex flex-col gap-1 text-slate-500">Panel H, m
              <input v-model.number="form.panel_height_m" type="number" step="0.1" min="0.1" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-800" />
            </label>
            <label class="flex flex-col gap-1 text-slate-500">Tariff, $/kWh
              <input v-model.number="form.tariff_per_kwh_usd" type="number" step="0.01" min="0" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-800" />
            </label>
            <label class="flex flex-col gap-1 text-slate-500">Sun hours/yr
              <input v-model.number="form.peak_sun_hours" type="number" min="1" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-800" />
            </label>
            <label class="flex flex-col gap-1 text-slate-500">Grid
              <select v-model="form.grid_type" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-800">
                <option value="ongrid">On-grid</option>
                <option value="offgrid">Off-grid</option>
              </select>
            </label>
            <label class="flex flex-col gap-1 text-slate-500">Battery, kWh
              <input v-model.number="form.battery_kwh" type="number" min="0" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-800" />
            </label>
            <label class="col-span-2 flex flex-col gap-1 text-slate-500">Battery price, $/kWh
              <input v-model.number="form.battery_price_per_kwh_usd" type="number" min="0" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-800" />
            </label>
            <button class="btn btn-primary col-span-2 mt-1" type="button" @click="applyForm">
              Recalculate
            </button>
          </div>
          <p v-else-if="formOpen" class="mt-2 text-[11px] text-slate-500">Loading defaults…</p>
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
