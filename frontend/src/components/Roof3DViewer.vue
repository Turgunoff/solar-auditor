<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { assetUrl } from '../services/api'

const props = defineProps({
  result: { type: Object, required: true },
})

const hostRef = ref(null)
const errorMsg = ref('')

let renderer = null
let scene = null
let camera = null
let controls = null
let raf = 0
let resizeObs = null
const disposables = []

function track(obj) {
  disposables.push(obj)
  return obj
}

function disposeAll() {
  if (raf) cancelAnimationFrame(raf)
  raf = 0
  resizeObs?.disconnect()
  resizeObs = null
  controls?.dispose()
  for (const d of disposables) {
    d.dispose?.()
  }
  disposables.length = 0
  if (scene) {
    scene.traverse((child) => {
      child.geometry?.dispose?.()
      const mats = child.material
        ? Array.isArray(child.material)
          ? child.material
          : [child.material]
        : []
      mats.forEach((m) => {
        m.map?.dispose?.()
        m.dispose?.()
      })
    })
  }
  renderer?.dispose()
  if (hostRef.value) hostRef.value.innerHTML = ''
  renderer = null
  scene = null
  camera = null
  controls = null
}

function makePanelTexture() {
  const c = document.createElement('canvas')
  c.width = 256
  c.height = 128
  const ctx = c.getContext('2d')
  ctx.fillStyle = '#a8b0ba'
  ctx.fillRect(0, 0, 256, 128)
  ctx.fillStyle = '#081222'
  ctx.fillRect(6, 6, 244, 116)
  const cols = 6
  const rows = 3
  const pad = 8
  const cw = (244 - 4) / cols
  const rh = (116 - 4) / rows
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const x = pad + col * cw
      const y = pad + row * rh
      const g = ctx.createLinearGradient(x, y, x + cw, y + rh)
      g.addColorStop(0, '#1c3a5e')
      g.addColorStop(0.5, '#0d213c')
      g.addColorStop(1, '#071018')
      ctx.fillStyle = g
      ctx.fillRect(x + 1, y + 1, cw - 2, rh - 2)
      ctx.strokeStyle = 'rgba(170,200,230,0.28)'
      ctx.beginPath()
      ctx.moveTo(x + cw * 0.33, y + 2)
      ctx.lineTo(x + cw * 0.33, y + rh - 2)
      ctx.moveTo(x + cw * 0.66, y + 2)
      ctx.lineTo(x + cw * 0.66, y + rh - 2)
      ctx.stroke()
    }
  }
  const tex = track(new THREE.CanvasTexture(c))
  tex.colorSpace = THREE.SRGBColorSpace
  tex.anisotropy = 8
  return tex
}

function polyBounds(poly) {
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  for (const [x, y] of poly) {
    minX = Math.min(minX, x)
    minY = Math.min(minY, y)
    maxX = Math.max(maxX, x)
    maxY = Math.max(maxY, y)
  }
  return { minX, minY, maxX, maxY, w: maxX - minX, h: maxY - minY }
}

function unionBounds(polys) {
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  let ok = false
  for (const poly of polys) {
    if (!poly || poly.length < 3) continue
    ok = true
    const b = polyBounds(poly)
    minX = Math.min(minX, b.minX)
    minY = Math.min(minY, b.minY)
    maxX = Math.max(maxX, b.maxX)
    maxY = Math.max(maxY, b.maxY)
  }
  if (!ok) return { minX: 0, minY: 0, maxX: 100, maxY: 100, w: 100, h: 100 }
  return { minX, minY, maxX, maxY, w: maxX - minX, h: maxY - minY }
}

function buildScene() {
  if (!hostRef.value || !props.result) return
  disposeAll()
  errorMsg.value = ''

  try {
    const w = hostRef.value.clientWidth || 720
    const h = Math.max(420, Math.min(560, w * 0.62))

    scene = new THREE.Scene()
    scene.background = new THREE.Color(0xb7d4ef)
    scene.fog = new THREE.Fog(0xc5d6e4, 80, 220)

    camera = new THREE.PerspectiveCamera(42, w / h, 0.1, 500)
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    renderer.setSize(w, h)
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.1
    renderer.outputColorSpace = THREE.SRGBColorSpace
    hostRef.value.appendChild(renderer.domElement)

    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.06
    controls.maxPolarAngle = Math.PI * 0.48
    controls.minDistance = 10
    controls.maxDistance = 140

    scene.add(new THREE.HemisphereLight(0xeff6ff, 0x7a8460, 0.85))
    const sun = new THREE.DirectionalLight(0xfff1d8, 1.45)
    sun.position.set(40, 65, 30)
    sun.castShadow = true
    sun.shadow.mapSize.set(2048, 2048)
    sun.shadow.camera.near = 1
    sun.shadow.camera.far = 200
    sun.shadow.camera.left = -60
    sun.shadow.camera.right = 60
    sun.shadow.camera.top = 60
    sun.shadow.camera.bottom = -60
    sun.shadow.bias = -0.0003
    scene.add(sun)
    const fill = new THREE.DirectionalLight(0xb8d4ff, 0.35)
    fill.position.set(-35, 25, -25)
    scene.add(fill)

    const roofs = props.result.segmentation?.roof_polygons || []
    const obstacles = props.result.segmentation?.obstacles || []
    const panels = props.result.layout?.panels || []
    const dim = props.result.dimensions || { width: 1024, height: 1024 }

    const rb = unionBounds(
      roofs.length
        ? roofs
        : [
            [
              [0, 0],
              [dim.width, 0],
              [dim.width, dim.height],
              [0, dim.height],
            ],
          ],
    )
    const pad = Math.max(rb.w, rb.h) * 0.35 + 48
    const vMinX = Math.max(0, rb.minX - pad)
    const vMinY = Math.max(0, rb.minY - pad)
    const vMaxX = Math.min(dim.width, rb.maxX + pad)
    const vMaxY = Math.min(dim.height, rb.maxY + pad)
    const viewW = Math.max(vMaxX - vMinX, 1)
    const viewH = Math.max(vMaxY - vMinY, 1)
    const cx = (vMinX + vMaxX) / 2
    const cy = (vMinY + vMaxY) / 2
    const s = 52 / Math.max(viewW, viewH)
    // Real massing height (previous ~4.5 looked like a pancake on a 90-unit site)
    const buildingH = 12
    const roofY = buildingH
    const panelY = roofY + 0.28

    const toX = (x) => (x - cx) * s
    const toZ = (y) => (y - cy) * s

    // Terrain
    const skirt = new THREE.Mesh(
      track(new THREE.CircleGeometry(75, 64)),
      new THREE.MeshStandardMaterial({ color: 0x8e9870, roughness: 1 }),
    )
    skirt.rotation.x = -Math.PI / 2
    skirt.position.y = -0.05
    skirt.receiveShadow = true
    scene.add(skirt)

    const groundW = viewW * s
    const groundH = viewH * s
    const groundMat = new THREE.MeshStandardMaterial({ color: 0x7a8462, roughness: 1 })
    const ground = new THREE.Mesh(track(new THREE.PlaneGeometry(groundW, groundH)), groundMat)
    ground.rotation.x = -Math.PI / 2
    ground.position.y = 0.02
    ground.receiveShadow = true
    scene.add(ground)

    const imgUrl = props.result.image_url ? assetUrl(props.result.image_url) : ''
    if (imgUrl) {
      new THREE.TextureLoader().load(
        imgUrl,
        (tex) => {
          tex.colorSpace = THREE.SRGBColorSpace
          tex.wrapS = THREE.ClampToEdgeWrapping
          tex.wrapT = THREE.ClampToEdgeWrapping
          tex.offset.set(vMinX / dim.width, 1 - vMaxY / dim.height)
          tex.repeat.set(viewW / dim.width, viewH / dim.height)
          tex.anisotropy = renderer?.capabilities.getMaxAnisotropy() || 1
          track(tex)
          groundMat.map = tex
          groundMat.color.set(0xffffff)
          groundMat.needsUpdate = true
        },
        undefined,
        () => {},
      )
    }

    function makeShape(poly) {
      const shape = new THREE.Shape()
      poly.forEach(([x, y], i) => {
        const px = toX(x)
        const pz = toZ(y)
        if (i === 0) shape.moveTo(px, pz)
        else shape.lineTo(px, pz)
      })
      shape.closePath()
      return shape
    }

    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xd2cbb8,
      roughness: 0.9,
      metalness: 0.02,
    })
    const roofMat = new THREE.MeshStandardMaterial({
      color: 0x3a4450,
      roughness: 0.8,
      metalness: 0.1,
      side: THREE.DoubleSide,
    })
    const panelTex = makePanelTexture()
    const panelMat = new THREE.MeshStandardMaterial({
      map: panelTex,
      roughness: 0.25,
      metalness: 0.6,
    })
    const frameMat = new THREE.MeshStandardMaterial({
      color: 0xb8c0ca,
      roughness: 0.4,
      metalness: 0.7,
    })
    const hvacMat = new THREE.MeshStandardMaterial({
      color: 0x9099a4,
      roughness: 0.55,
      metalness: 0.35,
    })

    for (const poly of roofs) {
      if (!poly || poly.length < 3) continue
      const shape = makeShape(poly)

      const wallGeo = track(
        new THREE.ExtrudeGeometry(shape, { depth: buildingH, bevelEnabled: false }),
      )
      const walls = new THREE.Mesh(wallGeo, wallMat)
      walls.rotation.x = -Math.PI / 2
      walls.position.y = 0
      walls.castShadow = true
      walls.receiveShadow = true
      scene.add(walls)

      // Dark roof slab above wall top (hides beige extrusion cap)
      const deck = new THREE.Mesh(track(new THREE.ShapeGeometry(makeShape(poly))), roofMat)
      deck.rotation.x = -Math.PI / 2
      deck.position.y = roofY + 0.06
      deck.castShadow = true
      deck.receiveShadow = true
      scene.add(deck)
    }

    for (const poly of obstacles) {
      if (!poly || poly.length < 3) continue
      const b = polyBounds(poly)
      if (b.w < 2 || b.h < 2) continue
      const ow = Math.max(b.w * s, 0.9)
      const od = Math.max(b.h * s, 0.9)
      const oh = Math.min(2.4, Math.max(1.0, Math.min(ow, od) * 0.7))
      const box = new THREE.Mesh(track(new THREE.BoxGeometry(ow, oh, od)), hvacMat)
      box.position.set(toX((b.minX + b.maxX) / 2), roofY + oh / 2 + 0.1, toZ((b.minY + b.maxY) / 2))
      box.castShadow = true
      box.receiveShadow = true
      scene.add(box)
    }

    // Instanced modules
    if (panels.length) {
      const pw = Math.max((panels[0].width || 10) * s * 0.9, 0.3)
      const ph = Math.max((panels[0].height || 6) * s * 0.9, 0.2)
      const modGeo = track(new THREE.BoxGeometry(pw, 0.1, ph))
      const frGeo = track(new THREE.BoxGeometry(pw * 1.05, 0.045, ph * 1.05))
      const mods = new THREE.InstancedMesh(modGeo, panelMat, panels.length)
      const frames = new THREE.InstancedMesh(frGeo, frameMat, panels.length)
      mods.castShadow = true
      mods.receiveShadow = true
      frames.castShadow = true
      const dummy = new THREE.Object3D()
      const tilt = -0.16
      for (let i = 0; i < panels.length; i++) {
        const p = panels[i]
        dummy.position.set(toX(p.x), panelY, toZ(p.y))
        dummy.rotation.set(tilt, -((p.rotation || 0) * Math.PI) / 180, 0)
        dummy.updateMatrix()
        mods.setMatrixAt(i, dummy.matrix)
        dummy.position.y = panelY - 0.05
        dummy.updateMatrix()
        frames.setMatrixAt(i, dummy.matrix)
      }
      mods.instanceMatrix.needsUpdate = true
      frames.instanceMatrix.needsUpdate = true
      scene.add(mods)
      scene.add(frames)
    }

    // Soft contact shadow
    const shadow = new THREE.Mesh(
      track(new THREE.CircleGeometry(Math.max(rb.w, rb.h) * s * 0.55, 48)),
      new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.18 }),
    )
    shadow.rotation.x = -Math.PI / 2
    shadow.position.y = 0.04
    scene.add(shadow)

    camera.position.set(36, 26, 40)
    controls.target.set(0, buildingH * 0.4, 0)
    controls.update()

    const tick = () => {
      raf = requestAnimationFrame(tick)
      controls?.update()
      renderer?.render(scene, camera)
    }
    tick()

    resizeObs = new ResizeObserver(onResize)
    resizeObs.observe(hostRef.value)
  } catch (e) {
    errorMsg.value = e?.message || String(e)
    console.error('Roof3DViewer', e)
  }
}

function onResize() {
  if (!hostRef.value || !renderer || !camera) return
  const w = hostRef.value.clientWidth || 720
  const h = Math.max(420, Math.min(560, w * 0.62))
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

onMounted(() => buildScene())
watch(() => props.result, () => buildScene(), { deep: true })
onUnmounted(() => disposeAll())
</script>

<template>
  <div class="space-y-2">
    <div
      ref="hostRef"
      class="w-full overflow-hidden rounded-xl border border-slate-500/70 bg-slate-300 shadow-inner"
    />
    <p v-if="errorMsg" class="text-xs text-rose-400">{{ errorMsg }}</p>
    <p class="text-[11px] text-slate-400">
      Drag to orbit · scroll to zoom · satellite underlay + building massing · framed PV modules
      (demo heights — not a BIM model).
    </p>
  </div>
</template>
