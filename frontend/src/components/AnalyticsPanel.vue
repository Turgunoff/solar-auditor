<script setup>
import { computed, ref, watch } from 'vue'

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
    region: 'global',
  }
  formOpen.value = true
}

const REGION_LABELS = {
  global: 'Global (server defaults)',
  uzbekistan: 'Uzbekistan',
  us_southwest: 'US Southwest',
  eu_central: 'EU Central',
}

function onRegionChange() {
  const preset = props.defaults?.regions?.[form.value.region]
  if (!preset) return
  form.value.peak_sun_hours = preset.peak_sun_hours
  form.value.tariff_per_kwh_usd = preset.tariff_per_kwh_usd
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
    region: form.value.region || 'global',
  })
}

function fmt(n, digits = 1) {
  if (n == null || Number.isNaN(n)) return '—'
  return Number(n).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  })
}

const capFactor = computed(() => {
  const a = props.result?.analytics
  if (!a?.system_capacity_kw || !a?.annual_generation_kwh) return null
  return (a.annual_generation_kwh / (a.system_capacity_kw * 8760)) * 100
})

const panelWatts = computed(() => {
  const a = props.result?.analytics
  const n = props.result?.layout?.total_panels
  if (!a?.system_capacity_kw || !n) return null
  return Math.round((a.system_capacity_kw * 1000) / n)
})

const obstacleCount = computed(() => props.result?.segmentation?.obstacles?.length ?? null)

const showFull = ref(false)
watch(() => props.result?.project_id, () => { showFull.value = false })

// Plain-language takeaways built from the numbers (no AI text needed).
const plainBullets = computed(() => {
  const a = props.result?.analytics
  const n = props.result?.layout?.total_panels
  if (!a || !n) return []
  const monthly = Math.round(a.annual_generation_kwh / 12)
  const bullets = [
    `Tomga ${n} ta panel sig'adi — jami ${fmt(a.system_capacity_kw, 1)} kWp quvvat.`,
    `Yiliga ~${fmt(a.annual_generation_kwh, 0)} kWh, ya'ni oyiga o'rtacha ${fmt(monthly, 0)} kWh elektr beradi.`,
  ]
  if (a.roi_years != null) {
    bullets.push(
      `Yiliga ~$${fmt(a.annual_savings_usd, 0)} tejaladi; $${fmt(a.estimated_cost_usd, 0)} xarajat taxminan ${fmt(a.roi_years, 1)} yilda qoplanadi.`,
    )
  } else {
    bullets.push(`Taxminiy o'rnatish narxi: $${fmt(a.estimated_cost_usd, 0)}.`)
  }
  return bullets
})

// First two sentences of the AI note; the rest is behind "Batafsil".
const shortSummary = computed(() => {
  const text = (props.result?.analytics?.agent_summary || '').trim()
  if (!text) return ''
  const parts = text.match(/[^.!?]+[.!?]+/g) || [text]
  return parts.slice(0, 2).join(' ').trim()
})

const hasMoreSummary = computed(() => {
  const text = (props.result?.analytics?.agent_summary || '').trim()
  return text.length > shortSummary.value.length + 10
})

// Illustrative grid factor (kg CO2 per kWh) — estimate only, not a credit.
const co2TonnesPerYear = computed(() => {
  const kwh = props.result?.analytics?.annual_generation_kwh
  if (!kwh) return null
  return (kwh * 0.55) / 1000
})
</script>

<template>
  <aside class="eng-panel">
    <div class="eng-head">
      <h2>Natijalar</h2>
      <span class="eng-cert">Hisob dvigateli · bank hisoboti emas</span>
    </div>

    <div v-if="loading" class="space-y-3">
      <div class="grid grid-cols-2 gap-3">
        <div class="h-24 animate-pulse rounded-xl bg-slate-200" />
        <div class="h-24 animate-pulse rounded-xl bg-slate-200" />
        <div class="h-24 animate-pulse rounded-xl bg-slate-200" />
        <div class="h-24 animate-pulse rounded-xl bg-slate-200" />
      </div>
    </div>

    <template v-else-if="result">
      <div v-if="plainBullets.length" class="verdict">
        <p class="verdict-title">Qisqa xulosa</p>
        <ul>
          <li v-for="b in plainBullets" :key="b">{{ b }}</li>
        </ul>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="metric">
          <div class="metric-label">Tizim quvvati</div>
          <div class="metric-value">{{ fmt(result.analytics.system_capacity_kw, 1) }} <small>kWp</small></div>
          <div class="metric-sub"><b>{{ result.layout.total_panels }} ta</b> panel × {{ panelWatts ?? '—' }}W</div>
        </div>
        <div class="metric">
          <div class="metric-label">Yillik ishlab chiqarish</div>
          <div class="metric-value text-emerald-600">{{ fmt(result.analytics.annual_generation_kwh, 0) }} <small>kWh</small></div>
          <div class="metric-sub">Oyiga ~<b>{{ fmt(result.analytics.annual_generation_kwh / 12, 0) }} kWh</b></div>
        </div>
        <div class="metric">
          <div class="metric-label">Taxminiy narx</div>
          <div class="metric-value">${{ fmt(result.analytics.estimated_cost_usd, 0) }}</div>
          <div class="metric-sub">Yaroqli maydon: <b>{{ fmt(result.analytics.usable_area_m2, 0) }} m²</b></div>
        </div>
        <div class="metric">
          <div class="metric-label">O'zini oqlash</div>
          <div class="metric-value text-sky-600">
            {{ result.analytics.roi_years == null ? '—' : fmt(result.analytics.roi_years, 1) }}
            <small v-if="result.analytics.roi_years != null">yil</small>
          </div>
          <div class="metric-sub">Tejash: <b>${{ fmt(result.analytics.annual_savings_usd, 0) }}/yil</b></div>
        </div>
      </div>

      <div class="eng-section">
        <div class="eng-section-head">
          <h3>AI izohi</h3>
          <span class="eng-chip">{{ result.provider?.agent || result.provider?.segmentation || 'AI' }}</span>
        </div>
        <div class="narrative">
          <p>{{ showFull ? result.analytics.agent_summary : shortSummary }}</p>
          <button
            v-if="hasMoreSummary"
            class="more-btn"
            type="button"
            @click="showFull = !showFull"
          >
            {{ showFull ? 'Qisqartirish' : 'Batafsil o‘qish' }}
          </button>
        </div>
        <p class="obstacle-note">
          {{ obstacleCount ?? '—' }} ta to‘siq (mo‘ri, shamollatish, daraxt soyasi va h.k.) hisobga olindi —
          panellar ularga tegmasdan, faqat quyoshli qismga joylandi.
        </p>
      </div>

      <div class="eng-section">
        <h3 class="eng-specs-head">Texnik ma'lumotlar</h3>
        <dl class="specs">
          <div><dt>Panel</dt><dd>{{ panelWatts ?? '—' }} W · {{ fmt(result.analytics.usable_area_m2 && result.layout.total_panels ? result.analytics.usable_area_m2 / result.layout.total_panels : null, 1) }} m²/panel</dd></div>
          <div><dt>Yaroqli tom maydoni</dt><dd>{{ fmt(result.analytics.usable_area_m2, 1) }} m²</dd></div>
          <div v-if="co2TonnesPerYear != null"><dt>CO₂ kamayishi (taxminiy)</dt><dd>{{ fmt(co2TonnesPerYear, 1) }} t/yil</dd></div>
          <div><dt>Tarmoq rejimi</dt><dd>{{ result.analytics.grid_type === 'offgrid' ? 'Mustaqil (off-grid)' : 'Tarmoqqa ulangan' }}{{ result.analytics.battery_kwh ? ` · ${result.analytics.battery_kwh} kWh batareya` : '' }}</dd></div>
          <div v-if="result.analytics.region && result.analytics.region !== 'global'"><dt>Region</dt><dd>{{ REGION_LABELS[result.analytics.region] || result.analytics.region }}</dd></div>
        </dl>
        <button
          class="specs-toggle"
          type="button"
          @click="openForm"
        >
          Hisob sozlamalari
          <span>{{ formOpen ? 'Yashirish' : 'Tahrirlash' }}</span>
        </button>
        <div v-if="formOpen && form" class="mt-2 grid grid-cols-2 gap-2 text-[11px]">
          <label class="fld">Region (davlat)
            <select v-model="form.region" @change="onRegionChange">
              <option v-for="(label, key) in REGION_LABELS" :key="key" :value="key">{{ label }}</option>
            </select>
          </label>
          <label class="fld">Panel quvvati, W
            <input v-model.number="form.panel_w" type="number" min="1" />
          </label>
          <label class="fld">Narx, $/kW
            <input v-model.number="form.cost_per_kw_usd" type="number" min="0" />
          </label>
          <label class="fld">Panel W, m
            <input v-model.number="form.panel_width_m" type="number" step="0.1" min="0.1" />
          </label>
          <label class="fld">Panel H, m
            <input v-model.number="form.panel_height_m" type="number" step="0.1" min="0.1" />
          </label>
          <label class="fld">Tarif, $/kWh
            <input v-model.number="form.tariff_per_kwh_usd" type="number" step="0.01" min="0" />
          </label>
          <label class="fld">Quyosh soati/yil
            <input v-model.number="form.peak_sun_hours" type="number" min="1" />
          </label>
          <label class="fld">Tarmoq
            <select v-model="form.grid_type">
              <option value="ongrid">Tarmoqqa ulangan</option>
              <option value="offgrid">Mustaqil (off-grid)</option>
            </select>
          </label>
          <label class="fld">Batareya, kWh
            <input v-model.number="form.battery_kwh" type="number" min="0" />
          </label>
          <label class="fld col-span-2">Batareya narxi, $/kWh
            <input v-model.number="form.battery_price_per_kwh_usd" type="number" min="0" />
          </label>
          <button class="btn btn-primary col-span-2 mt-1" type="button" @click="applyForm">
            Qayta hisoblash
          </button>
        </div>
        <p v-else-if="formOpen" class="mt-2 text-[11px] text-slate-500">Yuklanmoqda…</p>
      </div>

      <div class="rounded-xl border border-amber-200 bg-amber-50 p-3">
        <p class="text-[11px] leading-relaxed text-amber-800">
          Bu dastlabki hisob: kWh va oqlash muddati belgilangan quyosh/tarif taxminlariga asoslanadi.
          Sotib olishdan oldin joyida o‘lchov bilan tasdiqlang.
        </p>
      </div>

      <div class="mt-auto flex flex-col gap-2">
        <button class="btn btn-ghost w-full" type="button" @click="$emit('view-render')">
          Konsept renderni ko'rish
        </button>
        <button class="btn btn-primary w-full" type="button" @click="$emit('download-pdf')">
          PDF hisobotni yuklash
        </button>
      </div>
    </template>

    <p v-else class="text-sm text-slate-500">
      Boshlash uchun yuqoridan manba tanlab, AI Auditni bosing — natijalar shu yerda chiqadi.
    </p>
  </aside>
</template>

<style scoped>
.eng-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #fff;
  padding: 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

.eng-head h2 {
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #0f172a;
}

.eng-cert {
  display: inline-block;
  margin-top: 0.25rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: #15803d;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 9999px;
  padding: 0.1rem 0.55rem;
}

.verdict {
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
}

.verdict-title {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #15803d;
  margin: 0 0 0.4rem;
}

.verdict ul {
  margin: 0;
  padding-left: 1.05rem;
  font-size: 0.84rem;
  line-height: 1.55;
  color: #14532d;
}

.verdict li { margin: 0.2rem 0; }

.more-btn {
  margin-top: 0.45rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #0e7490;
  cursor: pointer;
}

.more-btn:hover { text-decoration: underline; }

.obstacle-note {
  font-size: 0.78rem;
  line-height: 1.5;
  color: #64748b;
  margin: 0.5rem 0 0;
}

.metric {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.7rem 0.8rem;
  background: #fff;
}

.metric-label {
  font-size: 0.72rem;
  color: #64748b;
  font-weight: 500;
}

.metric-value {
  margin-top: 0.15rem;
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.metric-value small {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
}

.metric-sub {
  margin-top: 0.15rem;
  font-size: 0.72rem;
  color: #64748b;
}

.metric-sub b {
  color: #334155;
}

.eng-section h3 {
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #0f172a;
}

.eng-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.eng-chip {
  font-size: 0.68rem;
  font-weight: 700;
  color: #0369a1;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 6px;
  padding: 0.1rem 0.5rem;
}

.narrative {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.7rem 0.8rem;
  font-size: 0.8rem;
  line-height: 1.5;
  color: #475569;
  margin-bottom: 0.5rem;
}

.narr-title {
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  display: inline-block;
}

.dot-green { background: #16a34a; }
.dot-red { background: #ef4444; }

.eng-specs-head {
  margin-bottom: 0.5rem;
  color: #94a3b8 !important;
}

.specs {
  font-size: 0.78rem;
}

.specs > div {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.3rem 0;
  border-top: 1px dashed #e2e8f0;
}

.specs dt { color: #64748b; }
.specs dd { font-weight: 600; color: #0f172a; text-align: right; }

.specs-toggle {
  margin-top: 0.5rem;
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #0f172a;
}

.specs-toggle span {
  color: #0e7490;
  text-transform: none;
  letter-spacing: 0;
}

.fld {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  color: #64748b;
}

.fld input,
.fld select {
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0.35rem 0.5rem;
  font-size: 0.75rem;
  color: #1e293b;
  background: #fff;
}
</style>
