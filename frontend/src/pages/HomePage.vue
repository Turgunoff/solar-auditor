<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const hero = ref(null)
const stats = ref([
  { value: 3, suffix: '', label: 'sample roofs to try' },
  { value: 4, suffix: '', label: 'pipeline stages' },
  { value: 1, suffix: '-pass', label: 'photo to layout sketch' },
  { value: 2, suffix: '', label: 'modes: live + mock' },
])
const counted = ref(stats.value.map(() => 0))

let raf = 0
let observer = null

function onScroll() {
  cancelAnimationFrame(raf)
  raf = requestAnimationFrame(() => {
    if (!hero.value) return
    const y = Math.min(window.scrollY, window.innerHeight)
    hero.value.style.setProperty('--par', `${(y / window.innerHeight).toFixed(3)}`)
  })
}

function animateCount(el, index, target) {
  const dur = 1100
  const t0 = performance.now()
  function tick(t) {
    const p = Math.min((t - t0) / dur, 1)
    const eased = 1 - Math.pow(1 - p, 3)
    counted.value[index] = Math.round(target * eased)
    if (p < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

onMounted(() => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()

  const revealEls = document.querySelectorAll('.home .rv')
  if (reduced || !('IntersectionObserver' in window)) {
    revealEls.forEach((el) => el.classList.add('in'))
    counted.value = stats.value.map((s) => s.value)
    return
  }
  observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue
        e.target.classList.add('in')
        const idx = e.target.dataset.count
        if (idx !== undefined && counted.value[+idx] === 0) {
          animateCount(e.target, +idx, stats.value[+idx].value)
        }
        observer.unobserve(e.target)
      }
    },
    { threshold: 0.25 },
  )
  revealEls.forEach((el) => observer.observe(el))
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  cancelAnimationFrame(raf)
  observer?.disconnect()
})
</script>

<template>
  <div class="home" ref="hero">
    <!-- Full-bleed hero: brand + headline + line + CTAs on real aerial -->
    <section class="hero">
      <img
        class="hero-img"
        src="/hero-roof.jpg?v=4"
        alt="Aerial view of a residential roof with solar panels on the sunlit face"
      />
      <div class="hero-veil" aria-hidden="true" />
      <div class="hero-copy">
        <p class="brand d1">Solar Auditor</p>
        <h1 class="d2">Rooftop photo in. Feasibility sketch out.</h1>
        <p class="sub d3">
          Segment the roof, keep clear of obstacles, pack modules, and export a first-pass plan —
          built for installers who need speed before the site survey.
        </p>
        <div class="cta-row d4">
          <RouterLink to="/app" class="cta-primary">Open auditor</RouterLink>
          <RouterLink to="/how-it-works" class="cta-ghost">How it works</RouterLink>
        </div>
      </div>
      <div class="scroll-cue d5" aria-hidden="true"><span /></div>
    </section>

    <div class="marquee" aria-hidden="true">
      <div class="marquee-track">
        <span>Segment&thinsp;·&thinsp;Layout&thinsp;·&thinsp;ROI&thinsp;·&thinsp;PDF&thinsp;·&thinsp;</span>
        <span>Segment&thinsp;·&thinsp;Layout&thinsp;·&thinsp;ROI&thinsp;·&thinsp;PDF&thinsp;·&thinsp;</span>
      </div>
    </div>

    <section class="band">
      <div class="band-inner rv rv-up">
        <h2>For people who sell and install solar</h2>
        <p>
          Homeowners get a clear story. Installers get a faster first pass. Founders get a real audit
          workflow — not another chatbot wrapper.
        </p>
      </div>
      <div class="stats">
        <div
          v-for="(s, i) in stats"
          :key="s.label"
          class="stat rv rv-up"
          :data-count="i"
        >
          <p class="num">{{ String(counted[i]).padStart(2, '0') }}{{ s.suffix }}</p>
          <p class="cap">{{ s.label }}</p>
        </div>
      </div>
    </section>

    <section class="shot">
      <div class="shot-media rv rv-left">
        <img src="/feature-pitch.jpg?v=3" alt="Pitched campus roofs with panels on sunlit slopes" />
      </div>
      <div class="shot-copy rv rv-right">
        <h2>Respect the roof geometry</h2>
        <p>
          Prefer sunlit planes, keep trees and yards out of the array, and treat Muse as concept art —
          the layout engine owns the module count.
        </p>
      </div>
    </section>

    <section class="shot reverse">
      <div class="shot-media rv rv-right">
        <img src="/feature-commercial.jpg?v=3" alt="Commercial flat roof packed with solar modules" />
      </div>
      <div class="shot-copy rv rv-left">
        <h2>Layout and money math together</h2>
        <p>
          Oriented packing, kWp, annual kWh, installed cost, and simple payback — labeled as
          feasibility estimates, not a bankable report.
        </p>
      </div>
    </section>

    <section class="shot">
      <div class="shot-media rv rv-left">
        <img src="/feature-report.jpg?v=3" alt="Installer reviewing a solar feasibility report" />
      </div>
      <div class="shot-copy rv rv-right">
        <h2>A PDF you can walk into a meeting with</h2>
        <p>
          Aerial, layout overlay, Muse concept, and a clear disclaimer — ready for a client
          conversation, then refine on site.
        </p>
        <RouterLink to="/app" class="cta-primary">Run a free audit</RouterLink>
      </div>
    </section>

    <section class="close">
      <div class="close-inner rv rv-blur">
        <h2>Start with a real roof</h2>
        <p>Pick a building on the map or drop an aerial — get a layout sketch in one pass.</p>
        <div class="cta-row">
          <RouterLink to="/app" class="cta-primary light">Open auditor</RouterLink>
          <RouterLink to="/pricing" class="cta-ghost light">Early plans</RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  --ink: #0c1f18;
  --foam: #f2f7f4;
  --mist: #c5d6cc;
  --leaf: #1a6b4f;
  --sun: #e8a317;
  --par: 0;
  margin-top: -4.25rem; /* pull under sticky nav */
  overflow: clip;
}

.hero {
  position: relative;
  min-height: 100vh;
  min-height: 100dvh;
  display: grid;
  align-items: end;
  overflow: hidden;
  color: var(--foam);
}

.hero-img {
  position: absolute;
  inset: -6% 0;
  width: 100%;
  height: 112%;
  object-fit: cover;
  object-position: center 40%;
  transform: translate3d(0, calc(var(--par) * 12vh), 0) scale(1.06);
  animation: drift 18s ease-in-out alternate infinite;
  will-change: transform;
}

.hero-veil {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(8, 22, 16, 0.42) 0%, rgba(8, 22, 16, 0.12) 42%, rgba(8, 22, 16, 0.72) 100%),
    linear-gradient(90deg, rgba(8, 22, 16, 0.4) 0%, transparent 58%);
  pointer-events: none;
}

.hero-copy {
  position: relative;
  z-index: 1;
  width: min(640px, 100%);
  padding: 7.5rem 1.5rem 3.25rem;
  padding-left: max(1.5rem, calc((100vw - 1120px) / 2 + 1.5rem));
}

.d1, .d2, .d3, .d4, .d5 { animation: rise 0.85s cubic-bezier(0.22, 1, 0.36, 1) both; }
.d2 { animation-delay: 0.1s; }
.d3 { animation-delay: 0.2s; }
.d4 { animation-delay: 0.3s; }
.d5 { animation-delay: 0.55s; }

.brand {
  margin: 0 0 0.85rem;
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: clamp(2.4rem, 6vw, 3.75rem);
  letter-spacing: -0.045em;
  line-height: 0.95;
  color: #fff;
  text-shadow: 0 2px 24px rgba(0, 0, 0, 0.35);
}

h1 {
  margin: 0 0 0.85rem;
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: clamp(1.25rem, 2.4vw, 1.65rem);
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: rgba(242, 247, 244, 0.92);
  max-width: 22ch;
}

.sub {
  margin: 0 0 1.6rem;
  font-size: 1.05rem;
  line-height: 1.55;
  color: rgba(242, 247, 244, 0.78);
  max-width: 40ch;
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.cta-primary,
.cta-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-weight: 700;
  font-size: 0.95rem;
  padding: 0.8rem 1.2rem;
  border-radius: 4px;
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.cta-primary {
  background: var(--sun);
  color: #1a1405;
}

.cta-primary:hover {
  transform: translateY(-2px);
  background: #f0b429;
}

.cta-primary.light {
  background: var(--foam);
  color: var(--ink);
}

.cta-ghost {
  border: 1.5px solid rgba(242, 247, 244, 0.45);
  color: var(--foam);
  background: rgba(8, 22, 16, 0.25);
  backdrop-filter: blur(6px);
}

.cta-ghost:hover {
  border-color: #fff;
}

.cta-ghost.light {
  border-color: rgba(242, 247, 244, 0.4);
  color: var(--foam);
}

.scroll-cue {
  position: absolute;
  z-index: 1;
  left: max(1.5rem, calc((100vw - 1120px) / 2 + 1.5rem));
  bottom: 1.1rem;
  width: 22px;
  height: 36px;
  border: 1.5px solid rgba(242, 247, 244, 0.5);
  border-radius: 12px;
}

.scroll-cue span {
  display: block;
  width: 3px;
  height: 8px;
  margin: 6px auto 0;
  border-radius: 2px;
  background: var(--sun);
  animation: cue 1.8s ease-in-out infinite;
}

.marquee {
  background: var(--sun);
  color: #1a1405;
  overflow: hidden;
  white-space: nowrap;
  padding: 0.65rem 0;
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: 0.95rem;
  letter-spacing: 0.14em;
}

.marquee-track {
  display: inline-flex;
  animation: slide 22s linear infinite;
}

.marquee-track span {
  padding-right: 0.5rem;
}

.band {
  background: #0f2a20;
  color: var(--foam);
  padding: 3.75rem 1.5rem 3rem;
}

.band-inner {
  max-width: 720px;
  margin: 0 auto;
}

.stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem 1rem;
  max-width: 720px;
  margin: 2.5rem auto 0;
}

@media (min-width: 700px) {
  .stats {
    grid-template-columns: repeat(4, 1fr);
  }
}

.stat .num {
  margin: 0;
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: clamp(1.9rem, 3.4vw, 2.5rem);
  letter-spacing: -0.03em;
  color: var(--sun);
  font-variant-numeric: tabular-nums;
}

.stat .cap {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  line-height: 1.45;
  color: rgba(242, 247, 244, 0.66);
}

.band h2,
.shot-copy h2,
.close h2 {
  margin: 0 0 0.75rem;
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: clamp(1.45rem, 2.6vw, 1.95rem);
  letter-spacing: -0.03em;
}

.band p,
.shot-copy p,
.close p {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.6;
  color: rgba(242, 247, 244, 0.78);
}

.shot {
  display: grid;
  background: #0a1a14;
  color: var(--foam);
}

@media (min-width: 900px) {
  .shot {
    grid-template-columns: 1.15fr 0.85fr;
    min-height: 420px;
  }
  .shot.reverse {
    grid-template-columns: 0.85fr 1.15fr;
  }
  .shot.reverse .shot-media {
    order: 2;
  }
}

.shot-media {
  overflow: hidden;
  min-height: 280px;
}

.shot-media img {
  width: 100%;
  height: 100%;
  min-height: 280px;
  object-fit: cover;
  display: block;
  transform: scale(1.12);
  transition: transform 1.4s cubic-bezier(0.22, 1, 0.36, 1);
}

.shot-media.in img {
  transform: scale(1);
}

.shot-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.35rem;
  padding: 2.5rem 1.5rem;
  max-width: 520px;
}

@media (min-width: 900px) {
  .shot-copy {
    padding: 3rem 2.5rem;
  }
}

.shot-copy .cta-primary {
  margin-top: 1.25rem;
  align-self: flex-start;
}

.close {
  background:
    radial-gradient(600px 280px at 20% 0%, rgba(232, 163, 23, 0.18), transparent 60%),
    #07140f;
  padding: 4.5rem 1.5rem;
}

.close-inner {
  max-width: 640px;
  margin: 0 auto;
  text-align: left;
}

.close .cta-row {
  margin-top: 1.5rem;
}

/* Scroll reveals: distinct motion per direction, fired once */
.rv {
  opacity: 0;
}
.rv-up { transform: translateY(26px); }
.rv-left { transform: translateX(-34px); }
.rv-right { transform: translateX(34px); }
.rv-blur { filter: blur(10px); transform: scale(0.985); }
.rv.in {
  opacity: 1;
  transform: none;
  filter: none;
  transition:
    opacity 0.8s ease,
    transform 0.9s cubic-bezier(0.22, 1, 0.36, 1),
    filter 0.9s ease;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes drift {
  from {
    margin-left: 0;
  }
  to {
    margin-left: -1.5%;
  }
}

@keyframes slide {
  to {
    transform: translateX(-50%);
  }
}

@keyframes cue {
  0%, 100% {
    transform: translateY(0);
    opacity: 1;
  }
  50% {
    transform: translateY(10px);
    opacity: 0.35;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-img,
  .d1, .d2, .d3, .d4, .d5,
  .scroll-cue span,
  .marquee-track {
    animation: none;
  }
  .hero-img {
    transform: none;
  }
  .rv {
    opacity: 1;
    transform: none;
    filter: none;
  }
  .shot-media img {
    transform: none;
    transition: none;
  }
}
</style>
