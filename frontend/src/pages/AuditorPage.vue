<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Header from '../components/Header.vue'
import Presets from '../components/Presets.vue'
import ImageCanvas from '../components/ImageCanvas.vue'
import AnalyticsPanel from '../components/AnalyticsPanel.vue'
import RenderModal from '../components/RenderModal.vue'
import MapPicker from '../components/MapPicker.vue'
import {
  getAssumptionDefaults,
  getHealth,
  getPresets,
  pdfUrl,
  processMap,
  processPreset,
  processUpload,
  refineLayout,
  staticMapUrl,
} from '../services/api'
import { getProject, saveProject } from '../services/history'
import { mapsConfigured } from '../services/googleMaps'
import { friendlyError } from '../services/friendlyError'

const route = useRoute()
const mode = ref('mock')
const models = ref({ segmentation: 'mock', render: 'mock', agent: 'mock' })
const statusMessage = ref('')
const presets = ref([])
const result = ref(null)
const loading = ref(false)
const error = ref('')
const modalOpen = ref(false)
const mapOpen = ref(false)
const mapPickerRef = ref(null)
const drawMode = ref(false)
const userBoxes = ref([])
const layers = ref({ roof: true, obstacles: true, panels: true })

const friendly = computed(() => (error.value ? friendlyError(error.value) : null))

const roofCount = computed(() => result.value?.segmentation?.roof_polygons?.length ?? 0)
const obstacleCount = computed(() => result.value?.segmentation?.obstacles?.length ?? 0)
const panelCount = computed(() => result.value?.layout?.total_panels ?? 0)
const assumptionDefaults = ref(null)
const assumptions = ref(null)

// Staged source: chosen but NOT yet analyzed.
const staged = ref({ kind: '', id: '', name: '', url: '', file: null, coords: null })

getAssumptionDefaults().then((d) => {
  assumptionDefaults.value = d
}).catch(() => {})

const selectedPreset = computed(() =>
  presets.value.find((p) => p.id === (staged.value.kind === 'preset' ? staged.value.id : '')) || null,
)

// 1 = source, 2 = staged (ready to run / running), 3 = result ready.
const activeStep = computed(() => (result.value ? 3 : staged.value.kind ? 2 : 1))

const steps = computed(() => [
  { n: 1, title: 'Manbani tanlang', hint: 'Preset, rasm yoki xarita' },
  { n: 2, title: 'AI Audit', hint: loading.value ? 'Tahlil ketmoqda…' : 'Tom va panellar hisoblanadi' },
  { n: 3, title: 'Natija', hint: 'Sozlang, render va PDF oling' },
])

const canRun = computed(() => !!staged.value.kind && !loading.value)
const stageLabel = computed(() => {
  if (staged.value.kind === 'preset') {
    return presets.value.find((p) => p.id === staged.value.id)?.label || staged.value.id
  }
  if (staged.value.kind === 'upload') return staged.value.name || 'Uploaded aerial'
  if (staged.value.kind === 'map' && staged.value.coords) {
    const { lat, lng } = staged.value.coords
    return `Map ${lat.toFixed(5)}, ${lng.toFixed(5)}`
  }
  return ''
})

async function bootstrap() {
  try {
    const [health, presetRes] = await Promise.all([getHealth(), getPresets()])
    mode.value = health.mode
    models.value = health.models
    statusMessage.value = health.message || ''
    presets.value = presetRes.presets
  } catch (e) {
    error.value = e.message || String(e)
  }

  const pid = route.query.project
  if (typeof pid === 'string' && pid) {
    const saved = getProject(pid)
    if (saved?.snapshot) {
      result.value = saved.snapshot
    }
  }
}

function clearOutcome() {
  result.value = null
  error.value = ''
  userBoxes.value = []
  drawMode.value = false
}

function onSelectPreset(id) {
  const p = presets.value.find((x) => x.id === id)
  staged.value = { kind: 'preset', id, name: p?.label || id, url: p?.thumbnail_url || '', file: null, coords: null }
  clearOutcome()
}

function onStageUpload(file) {
  if (staged.value.url?.startsWith('blob:')) URL.revokeObjectURL(staged.value.url)
  staged.value = { kind: 'upload', id: '', name: file.name || 'Uploaded aerial', url: URL.createObjectURL(file), file, coords: null }
  clearOutcome()
}

function clearUpload() {
  if (staged.value.url?.startsWith('blob:')) URL.revokeObjectURL(staged.value.url)
  staged.value = { kind: '', id: '', name: '', url: '', file: null, coords: null }
  clearOutcome()
}

function onStageMap({ lat, lng, zoom }) {
  const coords = { lat, lng, zoom }
  // Preview the exact satellite crop so the user sees the roof before Run.
  staged.value = { kind: 'map', id: '', name: '', url: staticMapUrl(coords), file: null, coords }
  clearOutcome()
  mapOpen.value = false
}

function onAddBox(box) {
  userBoxes.value = [...userBoxes.value, box]
}

function clearBoxes() {
  userBoxes.value = []
  drawMode.value = false
}

function providerFlags() {
  const seg = result.value?.provider?.segmentation || ''
  const tight = seg === 'mock' || seg.endsWith('+mock-fallback')
  const preset = presets.value.find((p) => p.id === staged.value.id)
  return { sam_overbox: !tight, pitched: preset ? preset.pitched !== false : true }
}

async function onApplyAssumptions(a) {
  assumptions.value = a
  await onRefine()
}

async function onRefine() {
  if (!result.value) return
  if (!userBoxes.value.length && !assumptions.value) return
  loading.value = true
  error.value = ''
  try {
    const r = result.value
    const flags = providerFlags()
    const res = await refineLayout({
      roof_polygons: r.segmentation.roof_polygons,
      obstacles: r.segmentation.obstacles,
      user_boxes: userBoxes.value,
      width_px: r.dimensions.width,
      height_px: r.dimensions.height,
      meters_per_pixel: r.meters_per_pixel,
      ...flags,
      assumptions: assumptions.value,
    })
    const summary = r.analytics.agent_summary
    result.value = { ...r, layout: res.layout, analytics: { ...res.analytics, agent_summary: summary } }
    saveProject(result.value, `Refined (${userBoxes.value.length} zones)`)
    userBoxes.value = []
    drawMode.value = false
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function runAudit() {
  if (!staged.value.kind || loading.value) return
  loading.value = true
  error.value = ''
  try {
    if (staged.value.kind === 'preset') {
      result.value = await processPreset(staged.value.id)
      const label = presets.value.find((p) => p.id === staged.value.id)?.label || staged.value.id
      saveProject(result.value, label)
    } else if (staged.value.kind === 'upload') {
      result.value = await processUpload(staged.value.file)
      saveProject(result.value, staged.value.name || 'Upload')
    } else if (staged.value.kind === 'map') {
      mapPickerRef.value?.setCapturing?.(true)
      result.value = await processMap(staged.value.coords)
      const { lat, lng } = staged.value.coords
      saveProject(result.value, `Map ${lat.toFixed(5)}, ${lng.toFixed(5)}`)
    }
  } catch (e) {
    error.value = e.message || String(e)
    mapPickerRef.value?.setCapturing?.(false)
  } finally {
    loading.value = false
  }
}

function reset() {
  if (staged.value.url?.startsWith('blob:')) URL.revokeObjectURL(staged.value.url)
  staged.value = { kind: '', id: '', name: '', url: '', file: null, coords: null }
  clearOutcome()
  modalOpen.value = false
  mapOpen.value = false
}

function downloadPdf() {
  if (!result.value?.project_id) return
  window.open(pdfUrl(result.value.project_id), '_blank')
}

watch(
  () => route.query.project,
  (pid) => {
    if (typeof pid === 'string' && pid) {
      const saved = getProject(pid)
      if (saved?.snapshot) {
        result.value = saved.snapshot
      }
    }
  },
)

onMounted(bootstrap)
</script>

<template>
  <div class="auditor-shell">
    <Header
      :mode="mode"
      :models="models"
      :run-providers="result?.provider || null"
      :status-message="statusMessage"
    />
    <Presets
      :presets="presets"
      :selected-id="staged.kind === 'preset' ? staged.id : ''"
      :loading="loading"
      :maps-enabled="mapsConfigured()"
      :upload-name="staged.kind === 'upload' ? staged.name : ''"
      :upload-url="staged.kind === 'upload' ? staged.url : ''"
      :staged-kind="staged.kind"
      :can-run="canRun"
      @select="onSelectPreset"
      @upload="onStageUpload"
      @clear-upload="clearUpload"
      @open-map="mapOpen = true"
      @run="runAudit"
      @reset="reset"
    />

    <ol class="steps" aria-label="Audit bosqichlari">
      <li
        v-for="s in steps"
        :key="s.n"
        class="step"
        :class="{ active: activeStep === s.n, done: activeStep > s.n }"
      >
        <span class="step-num">{{ activeStep > s.n ? '✓' : s.n }}</span>
        <span class="step-text">
          <b>{{ s.title }}</b>
          <small>{{ s.hint }}</small>
        </span>
      </li>
    </ol>

    <div v-if="!staged.kind && !result" class="guide">
      <b>Qanday ishlaydi?</b>
      Chapdan tayyor tomni tanlang, o'zingizning aerofotongizni yuklang yoki xaritadan binoni belgilang.
      Keyin yashil <b>AI Auditni boshlash</b> tugmasini bosing — qolganini AI bajaradi:
      tomni topadi, panellarni joylaydi, narx va o'zini oqlash muddatini hisoblaydi.
    </div>

    <div v-if="stageLabel && !result && !loading" class="mx-4 mt-3 text-sm text-slate-600 md:mx-6">
      Tanlandi: <b class="text-slate-900">{{ stageLabel }}</b> — ko'rib chiqing, keyin
      <b>AI Auditni boshlash</b> tugmasini bosing.
    </div>

    <div v-if="loading" class="loading-note" role="status">
      <span class="spinner" aria-hidden="true" />
      <span>
        <b>AI ishlamoqda.</b>
        Tom aniqlanmoqda → panellar joylanmoqda → hisobot tayyorlanmoqda.
        Jonli rejimda odatda 30–60 soniya.
      </span>
    </div>

    <div v-if="result && !loading" class="result-banner" role="status">
      <span class="result-main">
        <b>{{ panelCount }} ta panel</b> · {{ result.analytics.system_capacity_kw }} kWp ·
        yiliga ~{{ Math.round(result.analytics.annual_generation_kwh).toLocaleString() }} kWh
      </span>
      <span class="result-actions">
        <button class="btn btn-ghost" type="button" @click="modalOpen = true">Renderni ko'rish</button>
        <button class="btn btn-primary" type="button" @click="downloadPdf">PDF hisobot</button>
      </span>
    </div>

    <div
      v-if="friendly"
      class="mx-4 mb-3 mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800 md:mx-6"
      role="alert"
    >
      <p class="font-bold">{{ friendly.title }}</p>
      <p class="mt-0.5">{{ friendly.hint }}</p>
      <p v-if="friendly.raw && friendly.raw !== friendly.title" class="mt-1 text-xs text-rose-500">{{ friendly.raw }}</p>
      <div class="mt-2 flex flex-wrap gap-2">
        <button class="btn btn-ghost" type="button" @click="error = ''">Yopish</button>
        <button
          v-if="presets.length"
          class="btn btn-ghost"
          type="button"
          @click="error = ''; onSelectPreset(presets[0].id)"
        >
          Preset 1 dan boshlash
        </button>
      </div>
    </div>

    <div
      v-if="result && panelCount === 0"
      class="mx-4 mb-3 mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 md:mx-6"
      role="status"
    >
      <b>0 ta panel joylashdi.</b> Tom maydoni juda kichik yoki to'siqlar bilan yopilgan bo'lishi mumkin.
      Kattaroq kesma yuklang, exclusion zonalarni tozalang yoki presetda sinab ko'ring.
    </div>

    <!-- Step 3 · Aniqlash (natijadan keyin) -->
    <div v-if="result" class="mx-4 mb-3 mt-3 flex flex-wrap items-center gap-2 md:mx-6">
      <span class="text-xs font-bold uppercase tracking-wider text-slate-500">
        3 · Aniqlaş
      </span>
      <button
        class="btn"
        :class="drawMode ? 'btn-primary' : 'btn-ghost'"
        type="button"
        :disabled="loading"
        @click="drawMode = !drawMode"
      >
        {{ drawMode ? 'Chizilmoqda — tom ustida torting' : 'Taqiqlangan zona chizish' }}
      </button>
      <span v-if="drawMode" class="text-xs text-slate-500">
        Panel qo'yilmasin degan joyni sichqoncha bilan tortib belgilang.
      </span>
      <button
        v-if="userBoxes.length"
        class="btn btn-primary"
        type="button"
        :disabled="loading"
        @click="onRefine"
      >
        {{ loading ? 'Joylanmoqda…' : `Panellarni joylash (${userBoxes.length} zona)` }}
      </button>
      <button
        v-if="userBoxes.length"
        class="btn btn-ghost"
        type="button"
        :disabled="loading"
        @click="clearBoxes"
      >
        Zonalarni tozalash
      </button>
    </div>

    <div class="mx-4 mt-3 flex flex-wrap items-center gap-2 md:mx-6">
      <span class="layers-label">Qatlamlar:</span>
      <button type="button" class="chip chip-green" :class="{ off: !layers.roof }" @click="layers.roof = !layers.roof">
        Tom{{ result ? ` (${roofCount})` : '' }}
      </button>
      <button type="button" class="chip chip-red" :class="{ off: !layers.obstacles }" @click="layers.obstacles = !layers.obstacles">
        To'siqlar{{ result ? ` (${obstacleCount})` : '' }}
      </button>
      <button type="button" class="chip chip-blue" :class="{ off: !layers.panels }" @click="layers.panels = !layers.panels">
        Panellar{{ result ? ` (${panelCount})` : '' }}
      </button>
    </div>

    <main class="grid gap-4 px-4 pb-8 md:grid-cols-[1fr_320px] md:px-6 lg:grid-cols-[1fr_360px]">
      <div>
        <ImageCanvas
          :result="result"
          :preview-preset="selectedPreset"
          :preview-url="(staged.kind === 'upload' || staged.kind === 'map') ? staged.url : ''"
          :draw-mode="drawMode"
          :user-boxes="userBoxes"
          :show-roof="layers.roof"
          :show-obstacles="layers.obstacles"
          :show-panels="layers.panels"
          @add-box="onAddBox"
        />
        <div v-if="result" class="telemetry">
          <span>Panellar: <b>{{ panelCount }}</b></span>
          <span>Masshtab: <b>{{ result.meters_per_pixel ? result.meters_per_pixel.toFixed(3) + ' m/px' : '—' }}</b></span>
          <span>AI modeli: <b>{{ result.provider?.segmentation || '—' }}</b></span>
          <span>Holat: <b class="text-emerald-600">Tayyor</b></span>
        </div>
      </div>
      <AnalyticsPanel
        :result="result"
        :loading="loading"
        :defaults="assumptionDefaults"
        @view-render="modalOpen = true"
        @download-pdf="downloadPdf"
        @apply-assumptions="onApplyAssumptions"
      />
    </main>

    <RenderModal
      :open="modalOpen"
      :result="result"
      @close="modalOpen = false"
      @download-pdf="downloadPdf"
    />

    <MapPicker
      ref="mapPickerRef"
      :open="mapOpen"
      @close="mapOpen = false"
      @capture="onStageMap"
    />
  </div>
</template>

<style scoped>
.steps {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  list-style: none;
  margin: 0.75rem 1rem 0;
  padding: 0;
}

@media (min-width: 768px) {
  .steps { margin-left: 1.5rem; margin-right: 1.5rem; }
}

.step {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  flex: 1 1 180px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.55rem 0.8rem;
  opacity: 0.65;
}

.step.active { opacity: 1; border-color: #6ee7b7; background: #f0fdf4; }
.step.done { opacity: 1; }

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 9999px;
  background: #e2e8f0;
  color: #475569;
  font-size: 0.8rem;
  font-weight: 800;
  flex: none;
}

.step.active .step-num { background: #16a34a; color: #fff; }
.step.done .step-num { background: #dcfce7; color: #15803d; }

.step-text { display: flex; flex-direction: column; line-height: 1.25; }
.step-text b { font-size: 0.85rem; color: #0f172a; }
.step-text small { font-size: 0.72rem; color: #64748b; }

.guide {
  margin: 0.75rem 1rem 0;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.8rem 1rem;
  font-size: 0.88rem;
  line-height: 1.55;
  color: #475569;
}

.guide b { color: #0f172a; }

@media (min-width: 768px) {
  .guide { margin-left: 1.5rem; margin-right: 1.5rem; }
}

.loading-note {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin: 0.75rem 1rem 0;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 0.7rem 1rem;
  font-size: 0.85rem;
  color: #166534;
}

@media (min-width: 768px) {
  .loading-note { margin-left: 1.5rem; margin-right: 1.5rem; }
}

.spinner {
  width: 18px;
  height: 18px;
  border-radius: 9999px;
  border: 2.5px solid #bbf7d0;
  border-top-color: #16a34a;
  animation: spin 0.8s linear infinite;
  flex: none;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (prefers-reduced-motion: reduce) {
  .spinner { animation: none; }
}

.result-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  margin: 0.75rem 1rem 0;
  background: #0f172a;
  color: #f8fafc;
  border-radius: 12px;
  padding: 0.7rem 1rem;
  font-size: 0.9rem;
}

@media (min-width: 768px) {
  .result-banner { margin-left: 1.5rem; margin-right: 1.5rem; }
}

.result-main b { color: #86efac; }
.result-actions { display: flex; gap: 0.5rem; }

.layers-label {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #94a3b8;
}

.chip {
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 9999px;
  padding: 0.3rem 0.8rem;
  border: 1px solid;
  background: #fff;
  cursor: pointer;
}

.chip-green { border-color: #6ee7b7; color: #047857; background: #ecfdf5; }
.chip-red { border-color: #fca5a5; color: #b91c1c; background: #fef2f2; }
.chip-blue { border-color: #93c5fd; color: #1d4ed8; background: #eff6ff; }
.chip.off { opacity: 0.4; background: #fff; }

.telemetry {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1.2rem;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #64748b;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.5rem 0.9rem;
}

.telemetry b { color: #0f172a; font-variant-numeric: tabular-nums; }

.auditor-shell {
  min-height: 100vh;
  background:
    radial-gradient(900px 500px at 0% 0%, rgba(6, 182, 212, 0.08), transparent 55%),
    radial-gradient(800px 480px at 100% 0%, rgba(16, 185, 129, 0.08), transparent 50%),
    #f1f5f4;
  color: #0f172a;
  font-family: 'Manrope', sans-serif;
}
</style>
