<script setup>
import { assetUrl } from '../services/api'

const props = defineProps({
  open: { type: Boolean, default: false },
  result: { type: Object, default: null },
})

defineEmits(['close', 'download-pdf'])

function layoutSrc(result) {
  return assetUrl(result.layout_url || result.render_url)
}

function museSrc(result) {
  return assetUrl(result.render_url || result.layout_url)
}

function sameImage(result) {
  return !result.render_url || result.render_url === result.layout_url
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
          <h3 class="text-lg font-semibold text-slate-900">Vizualizatsiya</h3>
          <p class="text-xs text-slate-500">
            {{ result.layout.total_panels }} ta panel · Loyiha {{ result.project_id }}
          </p>
        </div>
        <button class="btn btn-ghost" type="button" @click="$emit('close')">Yopish</button>
      </div>

      <p class="mb-1 text-sm font-bold text-slate-800">1 · Aniq joylashuv (hisob shunga asoslanadi)</p>
      <img
        :src="layoutSrc(result)"
        alt="Layout engine overlay"
        class="w-full rounded-lg border border-slate-200"
      />

      <template v-if="!sameImage(result)">
        <p class="mb-1 mt-4 text-sm font-bold text-slate-800">2 · Konsept ko‘rinish (faqat tasavvur uchun)</p>
        <img
          :src="museSrc(result)"
          alt="Muse concept render"
          class="w-full rounded-lg border border-slate-200"
        />
        <p class="mt-2 text-[11px] text-slate-500">
          Muse surati — fotoreal konsept. U panel soni va o‘rnini biroz o‘zgartirishi mumkin;
          ishonchli variant — yuqoridagi aniq joylashuv.
        </p>
      </template>

      <div class="mt-4 flex justify-end gap-2">
        <button class="btn btn-primary" type="button" @click="$emit('download-pdf')">
          PDF hisobotni yuklash
        </button>
      </div>
    </div>
  </div>
</template>
