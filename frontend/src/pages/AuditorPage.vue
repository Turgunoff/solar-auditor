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
  getHealth,
  getPresets,
  pdfUrl,
  processMap,
  processPreset,
  processUpload,
} from '../services/api'
import { getProject, saveProject } from '../services/history'
import { mapsConfigured } from '../services/googleMaps'

const route = useRoute()
const mode = ref('mock')
const models = ref({ segmentation: 'mock', render: 'mock', agent: 'mock' })
const statusMessage = ref('')
const presets = ref([])
const selectedId = ref('residential_gable')
const result = ref(null)
const loading = ref(false)
const error = ref('')
const modalOpen = ref(false)
const mapOpen = ref(false)
const mapPickerRef = ref(null)

const selectedPreset = computed(() =>
  presets.value.find((p) => p.id === selectedId.value) || null,
)

async function bootstrap() {
  try {
    const [health, presetRes] = await Promise.all([getHealth(), getPresets()])
    mode.value = health.mode
    models.value = health.models
    statusMessage.value = health.message || ''
    presets.value = presetRes.presets
    if (presets.value.length && !selectedId.value) {
      selectedId.value = presets.value[0].id
    }
  } catch (e) {
    error.value = e.message || String(e)
  }

  const pid = route.query.project
  if (typeof pid === 'string' && pid) {
    const saved = getProject(pid)
    if (saved?.snapshot) {
      result.value = saved.snapshot
      selectedId.value = ''
    }
  }
}

function onSelectPreset(id) {
  selectedId.value = id
  result.value = null
  error.value = ''
}

async function runAudit() {
  if (!selectedId.value) return
  loading.value = true
  error.value = ''
  try {
    result.value = await processPreset(selectedId.value)
    const label = presets.value.find((p) => p.id === selectedId.value)?.label || selectedId.value
    saveProject(result.value, label)
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function onUpload(file) {
  loading.value = true
  error.value = ''
  selectedId.value = ''
  try {
    result.value = await processUpload(file)
    saveProject(result.value, file.name || 'Upload')
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function onMapCapture({ lat, lng, zoom }) {
  loading.value = true
  error.value = ''
  selectedId.value = ''
  mapPickerRef.value?.setCapturing?.(true)
  try {
    result.value = await processMap({ lat, lng, zoom })
    saveProject(result.value, `Map ${lat.toFixed(5)}, ${lng.toFixed(5)}`)
    mapOpen.value = false
  } catch (e) {
    error.value = e.message || String(e)
    mapPickerRef.value?.setCapturing?.(false)
  } finally {
    loading.value = false
  }
}

function reset() {
  result.value = null
  error.value = ''
  modalOpen.value = false
  mapOpen.value = false
  selectedId.value = presets.value[0]?.id || 'residential_gable'
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
        selectedId.value = ''
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
      :selected-id="selectedId"
      :loading="loading"
      :maps-enabled="mapsConfigured()"
      @select="onSelectPreset"
      @upload="onUpload"
      @run="runAudit"
      @reset="reset"
      @open-map="mapOpen = true"
    />

    <div
      v-if="error"
      class="mx-4 mb-3 rounded-lg border border-rose-700/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200 md:mx-6"
    >
      {{ error }}
    </div>

    <main class="grid gap-4 px-4 pb-8 md:grid-cols-[1fr_320px] md:px-6 lg:grid-cols-[1fr_360px]">
      <ImageCanvas :result="result" :preview-preset="selectedPreset" />
      <AnalyticsPanel
        :result="result"
        :loading="loading"
        @view-render="modalOpen = true"
        @download-pdf="downloadPdf"
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
      @capture="onMapCapture"
    />
  </div>
</template>

<style scoped>
.auditor-shell {
  min-height: 100vh;
  background:
    radial-gradient(900px 500px at 0% 0%, rgba(6, 182, 212, 0.12), transparent 55%),
    radial-gradient(800px 480px at 100% 0%, rgba(16, 185, 129, 0.1), transparent 50%),
    #0f172a;
  color: #e2e8f0;
  font-family: 'Manrope', sans-serif;
}
</style>
