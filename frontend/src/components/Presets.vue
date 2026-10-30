<script setup>
defineProps({
  presets: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  mapsEnabled: { type: Boolean, default: false },
  uploadName: { type: String, default: '' },
  uploadUrl: { type: String, default: '' },
  stagedKind: { type: String, default: '' },
  canRun: { type: Boolean, default: false },
})

defineEmits(['select', 'upload', 'clear-upload', 'open-map', 'run', 'reset'])

function pickFile(files, emit) {
  const f = files?.[0]
  if (f) emit('upload', f)
}
</script>

<template>
  <div class="preset-bar">
    <div class="tabs" role="tablist" aria-label="Roof preset">
      <span class="tabs-label">Roof preset:</span>
      <button
        v-for="p in presets"
        :key="p.id"
        type="button"
        role="tab"
        class="tab"
        :class="selectedId === p.id && stagedKind === 'preset' ? 'active' : ''"
        :disabled="loading"
        @click="$emit('select', p.id)"
      >
        {{ p.label }}
      </button>

      <label
        class="tab tab-upload"
        :class="stagedKind === 'upload' ? 'active' : ''"
        @dragover.prevent
        @drop.prevent="pickFile($event.dataTransfer.files, $emit)"
      >
        {{ stagedKind === 'upload' ? `✓ ${uploadName}` : 'Upload Aerial (Max 15MB)' }}
        <input
          type="file"
          accept="image/jpeg,image/png,.jpg,.jpeg,.png"
          class="hidden"
          :disabled="loading"
          @change="pickFile($event.target.files, $emit); $event.target.value = ''"
        />
      </label>

      <button
        v-if="mapsEnabled"
        type="button"
        class="tab"
        :class="stagedKind === 'map' ? 'active' : ''"
        :disabled="loading"
        @click="$emit('open-map')"
      >
        Pick on Map
      </button>
    </div>

    <div class="flex items-center gap-2">
      <button class="btn btn-ghost" type="button" :disabled="loading" @click="$emit('reset')">
        Reset
      </button>
      <button class="btn btn-run" type="button" :disabled="!canRun" @click="$emit('run')">
        {{ loading ? 'Analyzing…' : 'Run AI Solar Audit' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.preset-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  padding: 0.6rem 1rem;
}

@media (min-width: 768px) {
  .preset-bar { padding-left: 1.5rem; padding-right: 1.5rem; }
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.3rem 0.4rem;
}

.tabs-label {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #94a3b8;
  padding: 0 0.4rem;
}

.tab {
  font-size: 0.78rem;
  font-weight: 600;
  color: #475569;
  border-radius: 8px;
  padding: 0.4rem 0.75rem;
  cursor: pointer;
  border: 1px solid transparent;
  white-space: nowrap;
}

.tab:hover:not(:disabled) { background: #f1f5f9; }

.tab.active {
  background: #ecfdf5;
  border-color: #6ee7b7;
  color: #065f46;
}

.tab:disabled { opacity: 0.55; cursor: default; }

.tab-upload { cursor: pointer; border-style: dashed; border-color: #cbd5e1; }

.btn-run {
  background: #16a34a;
  color: #fff;
  font-weight: 800;
  border-radius: 10px;
  padding: 0.55rem 1.1rem;
  box-shadow: 0 2px 8px rgba(22, 163, 74, 0.3);
}

.btn-run:hover:not(:disabled) { background: #15803d; }
.btn-run:disabled { background: #86efac; cursor: default; box-shadow: none; }
</style>
