<script setup>
import { assetUrl } from '../services/api'

const props = defineProps({
  open: { type: Boolean, default: false },
  result: { type: Object, default: null },
})

defineEmits(['close', 'download-pdf'])

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

      <img
        :src="museSrc(result)"
        alt="Muse concept render"
        class="w-full rounded-lg border border-slate-200"
      />
      <p class="mt-2 text-[11px] text-slate-500">
        Muse Image is photoreal concept art guided by the layout overlay. It may still
        differ visually — do not use it as the bill of materials.
      </p>

      <div class="mt-4 flex justify-end gap-2">
        <button class="btn btn-primary" type="button" @click="$emit('download-pdf')">
          Download PDF Report
        </button>
      </div>
    </div>
  </div>
</template>
