<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { loadGoogleMaps, mapsConfigured } from '../services/googleMaps'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'capture'])

/** Below this zoom a whole block/district fits — audit quality collapses. */
const MIN_CAPTURE_ZOOM = 19

const mapEl = ref(null)
const searchEl = ref(null)
const ready = ref(false)
const error = ref('')
const capturing = ref(false)
const locating = ref(false)
const zoomLabel = ref(20)
const addressHint = ref('')

let map = null
let marker = null
let autocomplete = null
let geocoder = null

const DEFAULT = { lat: 41.3111, lng: 69.2797 } // Tashkent fallback

const zoomTooFar = computed(() => zoomLabel.value < MIN_CAPTURE_ZOOM)
const canCapture = computed(
  () => ready.value && !capturing.value && !zoomTooFar.value,
)
const geoSupported = computed(
  () => typeof navigator !== 'undefined' && Boolean(navigator.geolocation),
)

async function initMap() {
  if (!props.open || map) return
  error.value = ''
  if (!mapsConfigured()) {
    error.value = 'Xarita kaliti sozlanmagan — preset yoki rasm yuklashdan foydalaning. (Dev: VITE_GOOGLE_MAPS_API_KEY + Vite restart)'
    return
  }
  try {
    await nextTick()
    const gmaps = await loadGoogleMaps()
    if (!mapEl.value) return

    map = new gmaps.Map(mapEl.value, {
      center: DEFAULT,
      zoom: 20,
      mapTypeId: 'satellite',
      tilt: 0,
      streetViewControl: false,
      fullscreenControl: false,
      mapTypeControl: true,
      mapTypeControlOptions: {
        mapTypeIds: ['satellite', 'hybrid', 'roadmap'],
      },
      minZoom: 17,
      maxZoom: 21,
    })

    marker = new gmaps.Marker({
      map,
      position: DEFAULT,
      draggable: true,
      title: 'Roof center',
    })

    map.addListener('center_changed', () => {
      const c = map.getCenter()
      if (c && marker) marker.setPosition(c)
    })
    map.addListener('zoom_changed', () => {
      zoomLabel.value = map.getZoom() || 19
    })
    marker.addListener('dragend', () => {
      const p = marker.getPosition()
      if (p) map.panTo(p)
    })

    if (gmaps.Geocoder) {
      geocoder = new gmaps.Geocoder()
    }

    if (searchEl.value && gmaps.places) {
      autocomplete = new gmaps.places.Autocomplete(searchEl.value, {
        fields: ['geometry', 'formatted_address', 'name'],
      })
      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace()
        const loc = place?.geometry?.location
        if (!loc) return
        goTo(loc.lat(), loc.lng(), 20)
        addressHint.value = place.formatted_address || place.name || ''
        if (searchEl.value && addressHint.value) {
          searchEl.value.value = addressHint.value
        }
      })
    }

    zoomLabel.value = map.getZoom() || 20
    ready.value = true
  } catch (e) {
    error.value = e.message || String(e)
  }
}

function goTo(lat, lng, zoom = 20) {
  if (!map || !marker) return
  const pos = { lat, lng }
  map.setCenter(pos)
  map.setZoom(zoom)
  marker.setPosition(pos)
  zoomLabel.value = zoom
}

function fillAddress(lat, lng) {
  if (!geocoder) return
  geocoder.geocode({ location: { lat, lng } }, (results, status) => {
    if (status !== 'OK' || !results?.[0]) return
    addressHint.value = results[0].formatted_address || ''
    if (searchEl.value && addressHint.value) {
      searchEl.value.value = addressHint.value
    }
  })
}

function geoErrorMessage(err) {
  const messages = {
    1: 'Joylashuv ruxsati berilmadi. Brauzerda Allow bosing yoki manzilni qidiring.',
    2: 'Joylashuvni aniqlab bo‘lmadi. Manzilni qidiruvdan yozing.',
    3: 'Joylashuv vaqti tugadi. Wi‑Fi/GPS yoqing yoki manzilni qidiring.',
  }
  return messages[err?.code] || err?.message || 'Joylashuv olinmadi'
}

function applyPosition(pos) {
  const lat = pos.coords.latitude
  const lng = pos.coords.longitude
  goTo(lat, lng, 20)
  fillAddress(lat, lng)
  locating.value = false
  error.value = ''
}

function getPosition(options) {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, options)
  })
}

async function useMyLocation() {
  if (!map || locating.value) return
  if (!navigator.geolocation) {
    error.value = 'Brauzer geolokatsiyani qo‘llab-quvvatlamaydi. Manzilni qidiruvdan yozing.'
    return
  }
  locating.value = true
  error.value = ''

  try {
    // 1) Fast: cached / network (desktop-friendly)
    const quick = await getPosition({
      enableHighAccuracy: false,
      timeout: 8000,
      maximumAge: 120_000,
    })
    applyPosition(quick)
    return
  } catch (firstErr) {
    if (firstErr?.code === 1) {
      // Permission denied — no point retrying GPS
      locating.value = false
      error.value = geoErrorMessage(firstErr)
      return
    }
  }

  try {
    // 2) Slow fallback: GPS / high accuracy
    const precise = await getPosition({
      enableHighAccuracy: true,
      timeout: 20000,
      maximumAge: 0,
    })
    applyPosition(precise)
  } catch (err) {
    locating.value = false
    error.value = geoErrorMessage(err)
  }
}

function destroyMap() {
  autocomplete = null
  geocoder = null
  marker = null
  map = null
  ready.value = false
  locating.value = false
  addressHint.value = ''
}

function zoomCloser() {
  if (!map) return
  map.setZoom(Math.max(MIN_CAPTURE_ZOOM, map.getZoom() || 17))
  zoomLabel.value = map.getZoom() || MIN_CAPTURE_ZOOM
}

function onCapture() {
  if (!map || capturing.value) return
  const zoom = map.getZoom() || 0
  if (zoom < MIN_CAPTURE_ZOOM) {
    error.value = `Juda uzoq (zoom ${zoom}). Bitta bino uchun kamida zoom ${MIN_CAPTURE_ZOOM} kerak.`
    return
  }
  const c = map.getCenter()
  if (!c) return
  error.value = ''
  capturing.value = true
  emit('capture', {
    lat: c.lat(),
    lng: c.lng(),
    zoom,
  })
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      capturing.value = false
      error.value = ''
      await initMap()
    } else {
      destroyMap()
    }
  },
)

onMounted(() => {
  if (props.open) initMap()
})

onUnmounted(destroyMap)

defineExpose({
  setCapturing(v) {
    capturing.value = v
  },
})
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm"
    @click.self="$emit('close')"
  >
    <div class="card flex w-full max-w-4xl flex-col overflow-hidden">
      <div class="flex items-center justify-between border-b border-slate-700/80 px-4 py-3">
        <div>
          <h2 class="font-display text-lg text-white">Pick rooftop on map</h2>
          <p class="text-xs text-slate-400">
            Zoom to one building ({{ MIN_CAPTURE_ZOOM }}–21) · center the roof · then capture
          </p>
        </div>
        <button class="btn btn-ghost" type="button" @click="$emit('close')">Close</button>
      </div>

      <div class="flex flex-wrap items-center gap-2 border-b border-slate-700/60 px-4 py-2">
        <input
          ref="searchEl"
          type="text"
          placeholder="Manzil qidirish…"
          class="min-w-[180px] flex-1 rounded-lg border border-slate-600 bg-ink-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
        />
        <button
          v-if="geoSupported"
          class="btn btn-ghost shrink-0"
          type="button"
          :disabled="!ready || locating || capturing"
          @click="useMyLocation"
        >
          {{ locating ? 'Aniqlanmoqda…' : 'Mening joylashuvim' }}
        </button>
        <span
          class="rounded-md px-2 py-1 text-xs font-semibold"
          :class="zoomTooFar
            ? 'bg-amber-950/60 text-amber-200 ring-1 ring-amber-600/50'
            : 'bg-emerald-950/50 text-emerald-300 ring-1 ring-emerald-600/40'"
        >
          Zoom {{ zoomLabel }}
          <template v-if="zoomTooFar"> · too far</template>
          <template v-else> · OK</template>
        </span>
      </div>

      <div v-if="error" class="mx-4 mt-3 rounded-lg border border-rose-700/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
        {{ error }}
      </div>

      <div
        v-if="zoomTooFar && ready"
        class="mx-4 mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-700/50 bg-amber-950/40 px-3 py-2 text-sm text-amber-100"
      >
        <span>
          Juda uzoqdasiz — butun mahalla/tuman kadrga tushadi. Natija ishonchsiz bo‘ladi.
          Kamida zoom {{ MIN_CAPTURE_ZOOM }} qiling.
        </span>
        <button class="btn btn-ghost shrink-0 text-amber-50" type="button" @click="zoomCloser">
          Zoom closer
        </button>
      </div>

      <div ref="mapEl" class="h-[min(62vh,520px)] w-full bg-slate-900" />

      <div class="flex flex-wrap items-center justify-between gap-2 border-t border-slate-700/80 px-4 py-3">
        <p class="text-xs text-slate-400">
          Capture faqat zoom ≥ {{ MIN_CAPTURE_ZOOM }} da ochiladi.
        </p>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="!canCapture"
          @click="onCapture"
        >
          {{ capturing ? 'Capturing…' : 'Capture & Run AI Audit' }}
        </button>
      </div>
    </div>
  </div>
</template>
