<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { assetUrl } from '../services/api'

const props = defineProps({
  result: { type: Object, default: null },
  previewPreset: { type: Object, default: null },
  drawMode: { type: Boolean, default: false },
  userBoxes: { type: Array, default: () => [] },
})

const emit = defineEmits(['add-box'])

const canvasRef = ref(null)
const wrapRef = ref(null)
const scale = ref(1)
const offset = ref({ x: 0, y: 0 })
const dragging = ref(false)
const last = ref({ x: 0, y: 0 })
const imageObj = ref(null)
const previewOnly = ref(false)
const draftBox = ref(null)

function toImage(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  const x = (e.clientX - rect.left - offset.value.x) / scale.value
  const y = (e.clientY - rect.top - offset.value.y) / scale.value
  const img = imageObj.value
  return {
    x: Math.min(Math.max(x, 0), img ? img.width : x),
    y: Math.min(Math.max(y, 0), img ? img.height : y),
  }
}

async function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = assetUrl(url)
  })
}

function fitImage() {
  const wrap = wrapRef.value
  if (!wrap || !imageObj.value) return
  const pad = 24
  const sx = (wrap.clientWidth - pad) / imageObj.value.width
  const sy = (Math.max(420, wrap.clientWidth * 0.55) - pad) / imageObj.value.height
  scale.value = Math.min(sx, sy, 1.2)
  offset.value = { x: 12, y: 12 }
}

function draw() {
  const canvas = canvasRef.value
  const wrap = wrapRef.value
  if (!canvas || !wrap) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const w = wrap.clientWidth
  const h = Math.max(420, Math.min(640, wrap.clientWidth * 0.55))
  canvas.width = w * dpr
  canvas.height = h * dpr
  canvas.style.width = `${w}px`
  canvas.style.height = `${h}px`
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)
  ctx.fillStyle = '#e9eef2'
  ctx.fillRect(0, 0, w, h)

  if (!imageObj.value) {
    ctx.fillStyle = '#64748b'
    ctx.font = '14px sans-serif'
    ctx.fillText('Select a preset, upload aerial, or pick on Google Map', 24, 40)
    return
  }

  const img = imageObj.value
  ctx.save()
  ctx.translate(offset.value.x, offset.value.y)
  ctx.scale(scale.value, scale.value)
  ctx.drawImage(img, 0, 0)

  if (previewOnly.value || !props.result) {
    ctx.restore()
    ctx.fillStyle = 'rgba(15, 23, 42, 0.72)'
    ctx.fillRect(16, 16, 280, 36)
    ctx.fillStyle = '#67e8f9'
    ctx.font = '13px sans-serif'
    ctx.fillText('Preview — click Run AI Audit', 28, 40)
    return
  }

  const seg = props.result.segmentation
  ctx.lineWidth = 2 / scale.value

  for (const poly of seg.roof_polygons || []) {
    if (!poly?.length) continue
    ctx.beginPath()
    poly.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)))
    ctx.closePath()
    ctx.fillStyle = 'rgba(16, 185, 129, 0.35)'
    ctx.strokeStyle = '#10B981'
    ctx.fill()
    ctx.stroke()
  }

  for (const poly of seg.obstacles || []) {
    if (!poly?.length) continue
    ctx.beginPath()
    poly.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)))
    ctx.closePath()
    ctx.fillStyle = 'rgba(239, 68, 68, 0.4)'
    ctx.strokeStyle = '#EF4444'
    ctx.fill()
    ctx.stroke()
  }

  for (const box of props.userBoxes || []) {
    if (!box?.length) continue
    ctx.beginPath()
    box.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)))
    ctx.closePath()
    ctx.fillStyle = 'rgba(249, 115, 22, 0.22)'
    ctx.strokeStyle = '#F97316'
    ctx.lineWidth = 2 / scale.value
    ctx.setLineDash([8 / scale.value, 5 / scale.value])
    ctx.fill()
    ctx.stroke()
    ctx.setLineDash([])
  }

  if (draftBox.value) {
    const d = draftBox.value
    ctx.fillStyle = 'rgba(249, 115, 22, 0.25)'
    ctx.strokeStyle = '#F97316'
    ctx.lineWidth = 2 / scale.value
    ctx.setLineDash([8 / scale.value, 5 / scale.value])
    ctx.fillRect(d.x0, d.y0, d.x1 - d.x0, d.y1 - d.y0)
    ctx.strokeRect(d.x0, d.y0, d.x1 - d.x0, d.y1 - d.y0)
    ctx.setLineDash([])
  }

  const panels = props.result.layout?.panels || []
  for (const p of panels) {
    const rot = ((p.rotation || 0) * Math.PI) / 180
    ctx.save()
    // Panel.x/y are center coordinates (oriented packing)
    ctx.translate(p.x, p.y)
    ctx.rotate(rot)
    ctx.fillStyle = 'rgba(59, 130, 246, 0.55)'
    ctx.strokeStyle = '#93C5FD'
    ctx.lineWidth = 1.5 / scale.value
    ctx.fillRect(-p.width / 2, -p.height / 2, p.width, p.height)
    ctx.strokeRect(-p.width / 2, -p.height / 2, p.width, p.height)
    // Cell cross for module look
    ctx.strokeStyle = 'rgba(147, 197, 253, 0.55)'
    ctx.beginPath()
    ctx.moveTo(0, -p.height / 2)
    ctx.lineTo(0, p.height / 2)
    ctx.moveTo(-p.width / 2, 0)
    ctx.lineTo(p.width / 2, 0)
    ctx.stroke()
    ctx.restore()
  }

  ctx.restore()
}

async function refreshImage() {
  if (props.result?.image_url) {
    previewOnly.value = false
    try {
      imageObj.value = await loadImage(props.result.image_url)
      fitImage()
    } catch {
      imageObj.value = null
    }
    draw()
    return
  }

  if (props.previewPreset?.thumbnail_url) {
    previewOnly.value = true
    try {
      imageObj.value = await loadImage(props.previewPreset.thumbnail_url)
      fitImage()
    } catch {
      imageObj.value = null
    }
    draw()
    return
  }

  previewOnly.value = false
  imageObj.value = null
  draw()
}

function onWheel(e) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  scale.value = Math.min(4, Math.max(0.2, scale.value * delta))
  draw()
}

function onDown(e) {
  if (props.drawMode && imageObj.value && props.result) {
    const p = toImage(e)
    draftBox.value = { x0: p.x, y0: p.y, x1: p.x, y1: p.y }
    return
  }
  dragging.value = true
  last.value = { x: e.clientX, y: e.clientY }
}

function onMove(e) {
  if (draftBox.value) {
    const p = toImage(e)
    draftBox.value.x1 = p.x
    draftBox.value.y1 = p.y
    draw()
    return
  }
  if (!dragging.value) return
  offset.value = {
    x: offset.value.x + (e.clientX - last.value.x),
    y: offset.value.y + (e.clientY - last.value.y),
  }
  last.value = { x: e.clientX, y: e.clientY }
  draw()
}

function onUp() {
  if (draftBox.value) {
    const d = draftBox.value
    draftBox.value = null
    const w = Math.abs(d.x1 - d.x0)
    const h = Math.abs(d.y1 - d.y0)
    if (w > 8 && h > 8) {
      const x0 = Math.min(d.x0, d.x1)
      const y0 = Math.min(d.y0, d.y1)
      emit('add-box', [
        [x0, y0],
        [x0 + w, y0],
        [x0 + w, y0 + h],
        [x0, y0 + h],
      ])
    } else {
      draw()
    }
    return
  }
  dragging.value = false
}

watch(() => props.result, refreshImage, { deep: true })
watch(() => props.previewPreset, refreshImage, { deep: true })

onMounted(() => {
  refreshImage()
  window.addEventListener('resize', draw)
  window.addEventListener('mouseup', onUp)
})

onUnmounted(() => {
  window.removeEventListener('resize', draw)
  window.removeEventListener('mouseup', onUp)
})
</script>

<template>
  <div ref="wrapRef" class="card relative overflow-hidden">
    <canvas
      ref="canvasRef"
      class="block w-full cursor-grab active:cursor-grabbing"
      @wheel="onWheel"
      @mousedown="onDown"
      @mousemove="onMove"
    />
    <div class="pointer-events-none absolute bottom-3 left-3 flex gap-2 text-[11px] font-semibold">
      <span class="rounded bg-white/85 px-2 py-1 text-emerald-700">Roof</span>
      <span class="rounded bg-white/85 px-2 py-1 text-rose-600">Obstacles</span>
      <span class="rounded bg-white/85 px-2 py-1 text-sky-700">Panels</span>
      <span class="rounded bg-white/85 px-2 py-1 text-slate-500">Scroll zoom · drag pan</span>
    </div>
  </div>
</template>
