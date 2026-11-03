<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { importMapsLibrary, loadGoogleMaps, mapsConfigured, mapsKey } from '../services/googleMaps'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'capture'])

/** Below this zoom a whole block/district fits — audit quality collapses. */
const MIN_CAPTURE_ZOOM = 19

const mapEl = ref(null)
const searchMount = ref(null)
const ready = ref(false)
const error = ref('')
const placesMissing = ref(false)
const capturing = ref(false)
const locating = ref(false)
const zoomLabel = ref(20)
const addressHint = ref('')

let map = null
let marker = null
let placeAutocomplete = null
let geocoder = null
let onPlaceSelect = null
let onPlaceError = null

const DEFAULT = { lat: 41.3111, lng: 69.2797 } // Tashkent fallback

const zoomTooFar = computed(() => zoomLabel.value < MIN_CAPTURE_ZOOM)
const canCapture = computed(
  () => ready.value && !capturing.value && !zoomTooFar.value,
)
const geoSupported = computed(
  () => typeof navigator !== 'undefined' && Boolean(navigator.geolocation),
)

async function mountPlaceAutocomplete() {
  if (!searchMount.value || placeAutocomplete) return
  placesMissing.value = false

  let PlaceAutocompleteElement
  try {
    const placesLib = await importMapsLibrary('places')
    PlaceAutocompleteElement = placesLib.PlaceAutocompleteElement
  } catch {
    placesMissing.value = true
    return
  }

  if (!PlaceAutocompleteElement) {
    placesMissing.value = true
    return
  }

  placeAutocomplete = new PlaceAutocompleteElement({
    placeholder: 'Search address…',
    requestedRegion: 'uz',
  })
  placeAutocomplete.className = 'map-place-autocomplete'
  searchMount.value.appendChild(placeAutocomplete)

  onPlaceSelect = async (event) => {
    try {
      const prediction = event.placePrediction
      if (!prediction?.toPlace) return
      const place = prediction.toPlace()
      await place.fetchFields({
        fields: ['displayName', 'formattedAddress', 'location'],
      })
      const loc = place.location
      if (!loc) return
      placesMissing.value = false
      error.value = ''
      goTo(loc.lat(), loc.lng(), 20)
      addressHint.value = place.formattedAddress || place.displayName || ''
      if (addressHint.value) placeAutocomplete.value = addressHint.value
    } catch (err) {
      placesMissing.value = true
      error.value = err?.message || 'Could not load address details.'
    }
  }

  onPlaceError = () => {
    placesMissing.value = true
  }

  placeAutocomplete.addEventListener('gmp-select', onPlaceSelect)
  placeAutocomplete.addEventListener('gmp-error', onPlaceError)
}

async function initMap() {
  if (!props.open || map) return
  error.value = ''
  if (!mapsConfigured()) {
    error.value = 'Map key is not configured — use a preset or image upload instead. (Dev: VITE_GOOGLE_MAPS_API_KEY + restart Vite)'
    return
  }
  try {
    await nextTick()
    const gmaps = await loadGoogleMaps((authErr) => {
      error.value = authErr.message
    })
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
      minZoom: 2,
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

    await mountPlaceAutocomplete()

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
    if (placeAutocomplete && addressHint.value) {
      placeAutocomplete.value = addressHint.value
    }
  })
}

function geoErrorMessage(err) {
  const messages = {
    1: 'Location permission denied. Click Allow in the browser or search for an address.',
    2: 'Could not determine location. Enter an address in search.',
    3: 'Location timed out. Turn on Wi-Fi/GPS or search for an address.',
  }
  return messages[err?.code] || err?.message || 'Location unavailable'
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
    error.value = 'Browser does not support geolocation. Enter an address in search.'
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
    return
  } catch (err) {
    if (err?.code === 1) {
      locating.value = false
      error.value = geoErrorMessage(err)
      return
    }
  }

  try {
    // 3) Last resort: Google Geolocation API (Wi-Fi/cell based, no GPS needed)
    const key = mapsKey()
    if (!key) throw new Error('no-key')
    const res = await fetch(
      `https://www.googleapis.com/geolocation/v1/geolocate?key=${encodeURIComponent(key)}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' },
    )
    if (!res.ok) throw new Error(`geo-http-${res.status}`)
    const data = await res.json()
    if (typeof data?.location?.lat !== 'number') throw new Error('geo-empty')
    goTo(data.location.lat, data.location.lng, 20)
    fillAddress(data.location.lat, data.location.lng)
    locating.value = false
    error.value = ''
  } catch (err) {
    locating.value = false
    error.value =
      'Could not find location (neither GPS nor network). Enter an address in search — e.g. "London, UK".'
  }
}

function destroyPlaceAutocomplete() {
  if (placeAutocomplete) {
    if (onPlaceSelect) placeAutocomplete.removeEventListener('gmp-select', onPlaceSelect)
    if (onPlaceError) placeAutocomplete.removeEventListener('gmp-error', onPlaceError)
    placeAutocomplete.remove()
  }
  placeAutocomplete = null
  onPlaceSelect = null
  onPlaceError = null
}

function destroyMap() {
  destroyPlaceAutocomplete()
  geocoder = null
  marker = null
  map = null
  ready.value = false
  locating.value = false
  placesMissing.value = false
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
    error.value = `Too far out (zoom ${zoom}). Zoom to at least ${MIN_CAPTURE_ZOOM} for a single building.`
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
      <div class="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div>
          <h2 class="font-display text-lg text-slate-900">Pick rooftop on map</h2>
          <p class="text-xs text-slate-500">
            Zoom to one building ({{ MIN_CAPTURE_ZOOM }}–21) · center the roof · then capture
          </p>
        </div>
        <button class="btn btn-ghost" type="button" @click="$emit('close')">Close</button>
      </div>

      <div class="flex flex-wrap items-center gap-2 border-b border-slate-200/60 px-4 py-2">
        <div ref="searchMount" class="map-search-mount min-w-[180px] flex-1" />
        <button
          v-if="geoSupported"
          class="btn btn-ghost shrink-0"
          type="button"
          :disabled="!ready || locating || capturing"
          @click="useMyLocation"
        >
          {{ locating ? 'Locating…' : 'My location' }}
        </button>
        <span
          class="rounded-md px-2 py-1 text-xs font-semibold"
          :class="zoomTooFar
            ? 'bg-amber-100 text-amber-800 ring-1 ring-amber-300'
            : 'bg-emerald-100 text-emerald-800 ring-1 ring-emerald-300'"
        >
          Zoom {{ zoomLabel }}
          <template v-if="zoomTooFar"> · too far</template>
          <template v-else> · OK</template>
        </span>
      </div>

      <div v-if="error" class="mx-4 mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
        {{ error }}
      </div>

      <div v-if="placesMissing && ready" class="mx-4 mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
        Address search is not working — in Cloud Console → API Library, enable <b>Places API (New)</b>,
        add it to the key restrictions, then reload the page. In the meantime, you can drag the map.
      </div>

      <div
        v-if="zoomTooFar && ready"
        class="mx-4 mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        <span>
          You are too far out — a whole neighborhood/block fits in frame. The result will be unreliable.
          Zoom to at least {{ MIN_CAPTURE_ZOOM }}.
        </span>
        <button class="btn btn-ghost shrink-0" type="button" @click="zoomCloser">
          Zoom closer
        </button>
      </div>

      <div ref="mapEl" class="h-[min(62vh,520px)] w-full bg-slate-900" />

      <div class="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 px-4 py-3">
        <p class="text-xs text-slate-500">
          Capture is only available at zoom ≥ {{ MIN_CAPTURE_ZOOM }}.
        </p>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="!canCapture"
          @click="onCapture"
        >
          {{ capturing ? 'Capturing…' : 'Use this area' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-search-mount {
  display: flex;
  align-items: stretch;
}

.map-search-mount :deep(.map-place-autocomplete),
.map-search-mount :deep(gmp-place-autocomplete) {
  flex: 1;
  width: 100%;
  min-width: 0;
  color-scheme: light;
}
</style>
