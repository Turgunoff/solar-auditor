<script setup>
import { defineAsyncComponent, ref, watch } from 'vue'
import { assetUrl } from '../services/api'

// three.js is heavy (~500KB) — load only when the 3D tab opens.
const Roof3DViewer = defineAsyncComponent(() => import('./Roof3DViewer.vue'))

const props = defineProps({
  open: { type: Boolean, default: false },
  result: { type: Object, default: null },
  initialTab: { type: String, default: 'layout' },
})

defineEmits(['close', 'download-pdf'])

const tab = ref('layout')

watch(
  () => [props.open, props.initialTab],
  ([open, initial]) => {
    if (!open) return
    if (initial === '2d' || initial === 'muse') tab.value = 'muse'
    else if (initial === '3d') tab.value = '3d'
    else tab.value = 'layout'
  },
)

function layoutSrc(result) {
  return assetUrl(result.layout_url || result.render_url)
}

function museSrc(result) {
  return assetUrl(result.render_url || result.layout_url)
}
</script>

<template>
  <div
    v-if="open && result"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
    @click.self="$emit('close')"
  >
    <div class="card max-h-[92vh] w-full max-w-4xl overflow-auto p-4">
      <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 class="text-lg font-semibold text-slate-900">Visualization</h3>
          <p class="text-xs text-slate-500">
            Provider: {{ result.provider.render }} · Project {{ result.project_id }}
          </p>
        </div>
        <button class="btn btn-ghost" type="button" @click="$emit('close')">Close</button>
      </div>

      <div class="mb-3 flex flex-wrap gap-2">
        <button
          class="btn text-xs"
          type="button"
          :class="tab === 'layout' ? 'btn-primary' : 'btn-ghost'"
          @click="tab = 'layout'"
        >
          Layout (engine)
        </button>
        <button
          class="btn text-xs"
          type="button"
          :class="tab === '3d' ? 'btn-primary' : 'btn-ghost'"
          @click="tab = '3d'"
        >
          3D model
        </button>
        <button
          class="btn text-xs"
          type="button"
          :class="tab === 'muse' ? 'btn-primary' : 'btn-ghost'"
          @click="tab = 'muse'"
        >
          Muse concept
        </button>
      </div>

      <Roof3DViewer v-if="tab === '3d'" :result="result" />
      <template v-else-if="tab === 'layout'">
        <img
          :src="layoutSrc(result)"
          alt="Layout engine overlay"
          class="w-full rounded-lg border border-slate-200"
        />
        <p class="mt-2 text-[11px] text-slate-500">
          Exact packed modules from the layout engine — this matches Analytics panel count.
        </p>
      </template>
      <template v-else>
        <img
          :src="museSrc(result)"
          alt="Muse concept render"
          class="w-full rounded-lg border border-slate-200"
        />
        <p class="mt-2 text-[11px] text-amber-200/90">
          Muse Image is photoreal concept art guided by the layout overlay. It may still
          differ visually — do not use it as the bill of materials.
        </p>
      </template>

      <div class="mt-4 flex justify-end gap-2">
        <button class="btn btn-primary" type="button" @click="$emit('download-pdf')">
          Download PDF Report
        </button>
      </div>
    </div>
  </div>
</template>
