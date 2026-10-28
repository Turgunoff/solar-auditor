<script setup>
defineProps({
  presets: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  mapsEnabled: { type: Boolean, default: false },
})

defineEmits(['select', 'upload', 'run', 'reset', 'open-map'])
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 px-4 py-3 md:px-6">
    <button
      v-for="p in presets"
      :key="p.id"
      class="btn btn-ghost"
      :class="selectedId === p.id ? 'ring-2 ring-cyan-400/60' : ''"
      :disabled="loading"
      @click="$emit('select', p.id)"
    >
      {{ p.label }}
    </button>

    <label class="btn btn-ghost cursor-pointer">
      Upload aerial
      <input
        type="file"
        accept="image/jpeg,image/png,.jpg,.jpeg,.png"
        class="hidden"
        :disabled="loading"
        @change="(e) => { const f = e.target.files?.[0]; if (f) $emit('upload', f); e.target.value='' }"
      />
    </label>

    <button
      v-if="mapsEnabled"
      class="btn btn-ghost"
      type="button"
      :disabled="loading"
      @click="$emit('open-map')"
    >
      Pick on Google Map
    </button>

    <div class="ml-auto flex flex-wrap gap-2">
      <button class="btn btn-primary" :disabled="loading || !selectedId" @click="$emit('run')">
        {{ loading ? 'Running…' : 'Run AI Audit' }}
      </button>
      <button class="btn btn-danger" :disabled="loading" @click="$emit('reset')">
        Reset Canvas
      </button>
    </div>
  </div>
</template>
