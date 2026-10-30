<script setup>
import { ref } from 'vue'

defineProps({
  presets: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  mapsEnabled: { type: Boolean, default: false },
  uploadName: { type: String, default: '' },
  uploadUrl: { type: String, default: '' },
  stagedKind: { type: String, default: '' },
})

defineEmits(['select', 'upload', 'clear-upload', 'open-map'])

const dragOver = ref(false)

function pickFile(files, emit) {
  const f = files?.[0]
  if (f) emit('upload', f)
}
</script>

<template>
  <div class="px-4 pt-4 md:px-6">
    <p class="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">
      1 · Choose a rooftop source
    </p>
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <button
        v-for="p in presets"
        :key="p.id"
        type="button"
        class="source-card"
        :class="selectedId === p.id && stagedKind === 'preset' ? 'active' : ''"
        :disabled="loading"
        @click="$emit('select', p.id)"
      >
        <img :src="p.thumbnail_url" :alt="p.label" loading="lazy" />
        <span class="source-label">{{ p.label }}</span>
      </button>

      <label
        class="source-card upload"
        :class="[stagedKind === 'upload' ? 'active' : '', dragOver ? 'drag' : '']"
        @dragover.prevent="dragOver = true"
        @dragleave="dragOver = false"
        @drop.prevent="dragOver = false; pickFile($event.dataTransfer.files, $emit)"
      >
        <img v-if="uploadUrl" :src="uploadUrl" alt="Uploaded aerial preview" />
        <span v-else class="upload-empty">
          <span class="upload-icon">＋</span>
          <span>Drop aerial here or browse</span>
          <span class="upload-hint">JPG / PNG</span>
        </span>
        <input
          type="file"
          accept="image/jpeg,image/png,.jpg,.jpeg,.png"
          class="hidden"
          :disabled="loading"
          @change="pickFile($event.target.files, $emit); $event.target.value = ''"
        />
        <span v-if="uploadName" class="source-label">{{ uploadName }}</span>
        <span
          v-if="stagedKind === 'upload'"
          class="clear-btn"
          role="button"
          tabindex="0"
          @click.stop.prevent="$emit('clear-upload')"
          @keydown.enter.stop.prevent="$emit('clear-upload')"
        >
          ×
        </span>
      </label>

      <button
        v-if="mapsEnabled"
        type="button"
        class="source-card map"
        :class="stagedKind === 'map' ? 'active' : ''"
        :disabled="loading"
        @click="$emit('open-map')"
      >
        <span class="upload-empty">
          <span class="upload-icon">◎</span>
          <span>Pick on Google Map</span>
          <span class="upload-hint">Satellite capture</span>
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.source-card {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  background: #fff;
  padding: 0;
  cursor: pointer;
  text-align: left;
  min-height: 118px;
  display: flex;
  flex-direction: column;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.source-card:hover:not(:disabled) {
  border-color: #94a3b8;
}

.source-card.active {
  border-color: #e8a317;
  box-shadow: 0 0 0 3px rgba(232, 163, 23, 0.25);
}

.source-card:disabled {
  opacity: 0.6;
  cursor: default;
}

.source-card img {
  width: 100%;
  height: 92px;
  object-fit: cover;
  display: block;
  pointer-events: none;
}

.source-label {
  display: block;
  padding: 0.35rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-card.upload {
  cursor: pointer;
}

.source-card.upload.drag {
  border-color: #e8a317;
  border-style: dashed;
}

.upload-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.15rem;
  flex: 1;
  min-height: 118px;
  color: #475569;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.5rem;
  text-align: center;
}

.upload-icon {
  font-size: 1.4rem;
  line-height: 1;
  color: #1a6b4f;
}

.upload-hint {
  font-size: 0.68rem;
  font-weight: 500;
  color: #94a3b8;
}

.source-card.map .upload-icon {
  color: #0284c7;
}

.clear-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.92);
  color: #b91c1c;
  font-size: 14px;
  font-weight: 800;
  line-height: 22px;
  text-align: center;
  cursor: pointer;
}
</style>
