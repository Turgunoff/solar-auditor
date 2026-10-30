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
} from '../services/api'
import { getProject, saveProject } from '../services/history'
import { mapsConfigured } from '../services/googleMaps'

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
  staged.value = { kind: 'map', id: '', name: '', url: '', file: null, coords: { lat, lng, zoom } }
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

    <div v-if="stageLabel && !result" class="mx-4 mt-1 text-xs text-slate-500 md:mx-6">
      Staged: <b>{{ stageLabel }}</b> — review, then Run AI Solar Audit above.
    </div>

    <div
      v-if="error"
      class="mx-4 mb-3 mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 md:mx-6"
    >
      {{ error }}
    </div>

    <!-- Step 3 · Refine (after analysis) -->
    <div v-if="result" class="mx-4 mb-3 mt-3 flex flex-wrap items-center gap-2 md:mx-6">
      <span class="text-xs font-bold uppercase tracking-wider text-slate-500">
        3 · Refine
      </span>
      <button
        class="btn"
        :class="drawMode ? 'btn-primary' : 'btn-ghost'"
        type="button"
        :disabled="loading"
        @click="drawMode = !drawMode"
      >
        {{ drawMode ? 'Drawing… click-drag on roof' : 'Draw exclusion zone' }}
      </button>
      <button
        v-if="userBoxes.length"
        class="btn btn-primary"
        type="button"
        :disabled="loading"
        @click="onRefine"
      >
        {{ loading ? 'Placing…' : `Place panels (${userBoxes.length} zone${userBoxes.length > 1 ? 's' : ''})` }}
      </button>
      <button
        v-if="userBoxes.length"
        class="btn btn-ghost"
        type="button"
        :disabled="loading"
        @click="clearBoxes"
      >
        Clear zones
      </button>
    </div>

    <div class="mx-4 mt-3 flex flex-wrap items-center gap-2 md:mx-6">
      <span class="layers-label">Layers:</span>
      <button type="button" class="chip chip-green" :class="{ off: !layers.roof }" @click="layers.roof = !layers.roof">
        Roof Polygons{{ result ? ` (${roofCount})` : '' }}
      </button>
      <button type="button" class="chip chip-red" :class="{ off: !layers.obstacles }" @click="layers.obstacles = !layers.obstacles">
        Obstacles{{ result ? ` (${obstacleCount})` : '' }}
      </button>
      <button type="button" class="chip chip-blue" :class="{ off: !layers.panels }" @click="layers.panels = !layers.panels">
        PV Panels{{ result ? ` (${panelCount})` : '' }}
      </button>
    </div>

    <main class="grid gap-4 px-4 pb-8 md:grid-cols-[1fr_320px] md:px-6 lg:grid-cols-[1fr_360px]">
      <div>
        <ImageCanvas
          :result="result"
          :preview-preset="selectedPreset"
          :preview-url="staged.kind === 'upload' ? staged.url : ''"
          :draw-mode="drawMode"
          :user-boxes="userBoxes"
          :show-roof="layers.roof"
          :show-obstacles="layers.obstacles"
          :show-panels="layers.panels"
          @add-box="onAddBox"
        />
        <div v-if="result" class="telemetry">
          <span>Panels: <b>{{ panelCount }}</b></span>
          <span>Scale: <b>{{ result.meters_per_pixel ? result.meters_per_pixel.toFixed(3) + ' m/px' : '—' }}</b></span>
          <span>Segmentation: <b>{{ result.provider?.segmentation || '—' }}</b></span>
          <span>Audit Status: <b class="text-emerald-600">Calibrated</b></span>
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
